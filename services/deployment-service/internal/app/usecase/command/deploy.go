package command

import (
	"context"
	"fmt"
	"log/slog"
	"regexp"
	"strings"
	"sync"
	"time"

	"deployment-service/internal/app/port"
	"deployment-service/internal/domain"
	"deployment-service/internal/metrics"

	"github.com/google/uuid"
)

var nonAlphanumDash = regexp.MustCompile(`[^a-z0-9-]`)

func slugify(name string) string {
	s := strings.ToLower(name)
	s = nonAlphanumDash.ReplaceAllString(s, "-")
	s = regexp.MustCompile(`-+`).ReplaceAllString(s, "-")
	return strings.Trim(s, "-")
}

type BuildJobRenderer interface {
	RenderBuildJob(p BuildJobParams) (string, error)
}

type DeployJobRenderer interface {
	RenderDeployJob(p DeployJobParams) (string, error)
}

type DeployCommand struct {
	deployments  port.DeploymentRepository
	configs      port.ConfigRepository
	nomad        port.NomadClient
	publisher    port.Publisher
	buildRender  BuildJobRenderer
	deployRender DeployJobRenderer
	registry     RegistryConfig
	appCtx       context.Context
	wg           sync.WaitGroup
}

type RegistryConfig struct {
	URL      string
	Repo     string
	User     string
	Password string
}

func NewDeployCommand(
	deployments port.DeploymentRepository,
	configs port.ConfigRepository,
	nomad port.NomadClient,
	publisher port.Publisher,
	buildRender BuildJobRenderer,
	deployRender DeployJobRenderer,
	registry RegistryConfig,
	appCtx context.Context,
) *DeployCommand {
	return &DeployCommand{
		deployments:  deployments,
		configs:      configs,
		nomad:        nomad,
		publisher:    publisher,
		buildRender:  buildRender,
		deployRender: deployRender,
		registry:     registry,
		appCtx:       appCtx,
	}
}

type SecretsBulkCreatedInput struct {
	ProjectID        uuid.UUID
	ProjectName      string
	GitHubRepoURL    string
	GitHubToken      string
	StartCommand     string
	Secrets          []port.SecretRef
	DeploymentConfig *DeploymentConfigInput
	CorrelationID    string
}

type DeploymentConfigInput struct {
	Environment        string
	InstanceCount      int
	CPULimit           float64
	MemoryLimit        int
	Port               int
	HealthCheckPath    string
	DockerfilePath     string
	DockerBuildContext string
}

func (c *DeployCommand) Execute(ctx context.Context, in SecretsBulkCreatedInput) error {
	cfg, err := c.createConfig(ctx, in)
	if err != nil {
		return err
	}

	deployment := domain.NewDeployment(cfg.ID, in.ProjectID, "v1", "")
	if err := deployment.MarkBuilding(); err != nil {
		return err
	}
	if err := c.deployments.Save(ctx, deployment); err != nil {
		return fmt.Errorf("save deployment: %w", err)
	}
	if err := c.publisher.PublishBuilding(ctx, deployment.ID, deployment.ProjectID, in.CorrelationID); err != nil {
		slog.Warn("failed to publish building event", "err", err)
	}

	c.wg.Add(1)
	go func() {
		defer c.wg.Done()
		c.runBuildAndDeploy(c.appCtx, deployment, cfg, in)
	}()

	return nil
}

func (c *DeployCommand) Wait() { c.wg.Wait() }

func (c *DeployCommand) createConfig(ctx context.Context, in SecretsBulkCreatedInput) (*domain.DeploymentConfig, error) {
	di := in.DeploymentConfig
	env := domain.EnvDevelopment
	if di != nil && di.Environment != "" {
		env = domain.Environment(di.Environment)
	}

	cfg := domain.NewDeploymentConfig(in.ProjectID, in.GitHubRepoURL, env)
	if di != nil {
		if di.InstanceCount > 0 {
			cfg.InstanceCount = di.InstanceCount
		}
		if di.CPULimit > 0 {
			cfg.CPULimit = di.CPULimit
		}
		if di.MemoryLimit > 0 {
			cfg.MemoryLimit = di.MemoryLimit
		}
		if di.Port > 0 {
			cfg.Port = di.Port
		}
		if di.HealthCheckPath != "" {
			cfg.HealthCheckPath = di.HealthCheckPath
		}
		if di.DockerfilePath != "" {
			cfg.DockerfilePath = di.DockerfilePath
		}
		if di.DockerBuildContext != "" {
			cfg.DockerBuildContext = di.DockerBuildContext
		}
	}
	if err := cfg.Validate(); err != nil {
		return nil, fmt.Errorf("invalid config: %w", err)
	}
	if err := c.configs.Save(ctx, cfg); err != nil {
		return nil, fmt.Errorf("save config: %w", err)
	}
	return cfg, nil
}

func (c *DeployCommand) runBuildAndDeploy(ctx context.Context, d *domain.Deployment, cfg *domain.DeploymentConfig, in SecretsBulkCreatedInput) {
	log := slog.Default().With(
		"deployment_id", d.ID,
		"project_id", d.ProjectID,
		"correlation_id", in.CorrelationID,
	)

	buildStart := time.Now()

	buildHCL, err := c.buildRender.RenderBuildJob(BuildJobParams{
		ProjectID:        d.ProjectID.String(),
		Version:          d.Version,
		GitHubRepoURL:    in.GitHubRepoURL,
		GitHubToken:      in.GitHubToken,
		DockerfilePath:   cfg.DockerfilePath,
		BuildContext:     cfg.DockerBuildContext,
		ImageTag:         c.imageTag(d.ProjectID.String(), d.Version),
		RegistryURL:      c.registry.URL,
		RegistryUser:     c.registry.User,
		RegistryPassword: c.registry.Password,
		RegistryRepo:     c.registry.Repo,
	})
	if err != nil {
		log.Error("failed to render build job", "err", err)
		c.failDeployment(ctx, d, "render build job: "+err.Error(), in.CorrelationID)
		return
	}

	if _, err := c.nomad.SubmitJob(ctx, buildHCL); err != nil {
		c.failDeployment(ctx, d, "submit build job: "+err.Error(), in.CorrelationID)
		return
	}
	log.Info("build job submitted", "job_id", d.NomadBuildJobID())

	buildCtx, cancel := context.WithTimeout(ctx, 15*time.Minute)
	defer cancel()

	if err := c.nomad.WaitForCompletion(buildCtx, d.NomadBuildJobID()); err != nil {
		c.failDeployment(ctx, d, "build failed: "+err.Error(), in.CorrelationID)
		metrics.DeploymentTotal.WithLabelValues("failed", string(cfg.Environment)).Inc()
		return
	}

	metrics.DeploymentDurationSeconds.WithLabelValues("build").Observe(time.Since(buildStart).Seconds())
	log.Info("build completed")

	if err := d.MarkDeploying(); err != nil {
		c.failDeployment(ctx, d, err.Error(), in.CorrelationID)
		return
	}
	if err := c.deployments.Save(ctx, d); err != nil {
		log.Error("failed to save deploying status", "err", err)
		return
	}
	_ = c.publisher.PublishDeploying(ctx, d.ID, d.ProjectID, in.CorrelationID)

	imageURL := c.imageTag(d.ProjectID.String(), d.Version)
	deploymentURL := fmt.Sprintf("http://%s-%s.localhost:8090", slugify(in.ProjectName), d.ID.String()[:8])

	deployHCL, err := c.deployRender.RenderDeployJob(DeployJobParams{
		DeploymentID:     d.ID.String(),
		ProjectID:        d.ProjectID.String(),
		ProjectName:      in.ProjectName,
		ImageURL:         imageURL,
		Port:             cfg.Port,
		StartCommand:     in.StartCommand,
		Secrets:          in.Secrets,
		RegistryURL:      c.registry.URL,
		RegistryUser:     c.registry.User,
		RegistryPassword: c.registry.Password,
		Hostname:         deploymentURL,
	})
	if err != nil {
		c.failDeployment(ctx, d, "render deploy job: "+err.Error(), in.CorrelationID)
		return
	}

	if _, err := c.nomad.SubmitJob(ctx, deployHCL); err != nil {
		c.failDeployment(ctx, d, "submit deploy job: "+err.Error(), in.CorrelationID)
		return
	}

	if err := d.MarkRunning(imageURL, deploymentURL); err != nil {
		c.failDeployment(ctx, d, err.Error(), in.CorrelationID)
		return
	}
	if err := c.deployments.Save(ctx, d); err != nil {
		log.Error("failed to save running status", "err", err)
		return
	}
	_ = c.publisher.PublishRunning(ctx, d.ID, d.ProjectID, imageURL, deploymentURL, in.CorrelationID)

	metrics.DeploymentTotal.WithLabelValues("running", string(cfg.Environment)).Inc()
	metrics.ActiveDeployments.WithLabelValues(string(cfg.Environment)).Inc()
	log.Info("deployment running", "url", deploymentURL)
}

func (c *DeployCommand) failDeployment(ctx context.Context, d *domain.Deployment, reason, correlationID string) {
	d.MarkFailed(reason)
	if err := c.deployments.Save(ctx, d); err != nil {
		slog.Error("failed to persist failed deployment", "err", err, "deployment_id", d.ID)
	}
	_ = c.publisher.PublishFailed(ctx, d.ID, d.ProjectID, reason, correlationID)
}

func (c *DeployCommand) imageTag(projectID, version string) string {
	return fmt.Sprintf("%s/%s/project-%s:%s", c.registry.URL, c.registry.Repo, projectID, version)
}
