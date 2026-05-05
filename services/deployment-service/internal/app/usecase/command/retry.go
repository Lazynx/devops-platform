package command

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"deployment-service/internal/app/port"
	"deployment-service/internal/domain"
	"deployment-service/internal/metrics"

	"github.com/google/uuid"
)

type RetryCommand struct {
	deployments  port.DeploymentRepository
	configs      port.ConfigRepository
	nomad        port.NomadClient
	publisher    port.Publisher
	auth         port.AuthService
	secrets      port.SecretsFetcher
	buildRender  BuildJobRenderer
	deployRender DeployJobRenderer
	registry     RegistryConfig
	appCtx       context.Context
}

func NewRetryCommand(
	deployments port.DeploymentRepository,
	configs port.ConfigRepository,
	nomad port.NomadClient,
	publisher port.Publisher,
	auth port.AuthService,
	secrets port.SecretsFetcher,
	buildRender BuildJobRenderer,
	deployRender DeployJobRenderer,
	registry RegistryConfig,
	appCtx context.Context,
) *RetryCommand {
	return &RetryCommand{
		deployments:  deployments,
		configs:      configs,
		nomad:        nomad,
		publisher:    publisher,
		auth:         auth,
		secrets:      secrets,
		buildRender:  buildRender,
		deployRender: deployRender,
		registry:     registry,
		appCtx:       appCtx,
	}
}

type RetryInput struct {
	ProjectID       uuid.UUID
	ProjectName     string
	UserAccessToken string
	StartCommand    string
	CorrelationID   string
}

func (c *RetryCommand) Execute(ctx context.Context, in RetryInput) (*domain.Deployment, error) {
	githubToken, err := c.auth.GetGitHubToken(ctx, in.UserAccessToken)
	if err != nil {
		return nil, fmt.Errorf("get github token: %w", err)
	}

	cfgs, err := c.configs.GetByProjectID(ctx, in.ProjectID)
	if err != nil || len(cfgs) == 0 {
		return nil, domain.ErrConfigNotFound
	}
	cfg := cfgs[0]

	existing, _ := c.deployments.GetByProjectID(ctx, in.ProjectID)
	version := fmt.Sprintf("v%d", len(existing)+1)

	d := domain.NewDeployment(cfg.ID, in.ProjectID, version, "")
	if err := d.MarkBuilding(); err != nil {
		return nil, err
	}
	if err := c.deployments.Save(ctx, d); err != nil {
		return nil, fmt.Errorf("save deployment: %w", err)
	}
	_ = c.publisher.PublishBuilding(ctx, d.ID, d.ProjectID)

	go c.runBuildAndDeploy(c.appCtx, d, cfg, githubToken, in)
	return d, nil
}

func (c *RetryCommand) runBuildAndDeploy(ctx context.Context, d *domain.Deployment, cfg *domain.DeploymentConfig, githubToken string, in RetryInput) {
	log := slog.Default().With(
		"deployment_id", d.ID,
		"project_id", d.ProjectID,
		"correlation_id", in.CorrelationID,
	)

	buildStart := time.Now()
	imageURL := fmt.Sprintf("%s/%s/project-%s:%s", c.registry.URL, c.registry.Repo, d.ProjectID, d.Version)

	buildHCL, err := c.buildRender.RenderBuildJob(BuildJobParams{
		ProjectID:        d.ProjectID.String(),
		Version:          d.Version,
		GitHubRepoURL:    cfg.GitHubRepoURL,
		GitHubToken:      githubToken,
		DockerfilePath:   cfg.DockerfilePath,
		BuildContext:     cfg.DockerBuildContext,
		ImageTag:         imageURL,
		RegistryURL:      c.registry.URL,
		RegistryUser:     c.registry.User,
		RegistryPassword: c.registry.Password,
		RegistryRepo:     c.registry.Repo,
	})
	if err != nil {
		c.fail(ctx, d, "render build job: "+err.Error())
		return
	}
	if _, err := c.nomad.SubmitJob(ctx, buildHCL); err != nil {
		c.fail(ctx, d, "submit build job: "+err.Error())
		return
	}

	buildCtx, cancel := context.WithTimeout(ctx, 15*time.Minute)
	defer cancel()
	if err := c.nomad.WaitForCompletion(buildCtx, d.NomadBuildJobID()); err != nil {
		c.fail(ctx, d, "build failed: "+err.Error())
		metrics.DeploymentTotal.WithLabelValues("failed", string(cfg.Environment)).Inc()
		return
	}

	metrics.DeploymentDurationSeconds.WithLabelValues("build").Observe(time.Since(buildStart).Seconds())

	if err := d.MarkDeploying(); err != nil {
		c.fail(ctx, d, err.Error())
		return
	}
	_ = c.deployments.Save(ctx, d)
	_ = c.publisher.PublishDeploying(ctx, d.ID, d.ProjectID)

	secretRefs, err := c.secrets.FetchForProject(ctx, d.ProjectID)
	if err != nil {
		log.Warn("could not fetch secrets for retry, deploying without env vars", "err", err)
		secretRefs = nil
	}

	deploymentURL := fmt.Sprintf("http://%s-%s.localhost:8090", in.ProjectName, d.ID.String()[:8])

	deployHCL, err := c.deployRender.RenderDeployJob(DeployJobParams{
		DeploymentID:     d.ID.String(),
		ProjectID:        d.ProjectID.String(),
		ProjectName:      in.ProjectName,
		ImageURL:         imageURL,
		Port:             cfg.Port,
		StartCommand:     in.StartCommand,
		Secrets:          secretRefs,
		RegistryURL:      c.registry.URL,
		RegistryUser:     c.registry.User,
		RegistryPassword: c.registry.Password,
		Hostname:         deploymentURL,
	})
	if err != nil {
		c.fail(ctx, d, "render deploy job: "+err.Error())
		return
	}
	if _, err := c.nomad.SubmitJob(ctx, deployHCL); err != nil {
		c.fail(ctx, d, "submit deploy job: "+err.Error())
		return
	}

	if err := d.MarkRunning(imageURL, deploymentURL); err != nil {
		c.fail(ctx, d, err.Error())
		return
	}
	_ = c.deployments.Save(ctx, d)
	_ = c.publisher.PublishRunning(ctx, d.ID, d.ProjectID, imageURL, deploymentURL)

	metrics.DeploymentTotal.WithLabelValues("running", string(cfg.Environment)).Inc()
	metrics.ActiveDeployments.WithLabelValues(string(cfg.Environment)).Inc()
	log.Info("retry deployment running", "url", deploymentURL)
}

func (c *RetryCommand) fail(ctx context.Context, d *domain.Deployment, reason string) {
	d.MarkFailed(reason)
	_ = c.deployments.Save(ctx, d)
	_ = c.publisher.PublishFailed(ctx, d.ID, d.ProjectID, reason)
}
