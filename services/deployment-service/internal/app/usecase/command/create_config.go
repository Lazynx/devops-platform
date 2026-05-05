package command

import (
	"context"
	"errors"
	"fmt"

	"deployment-service/internal/app/port"
	"deployment-service/internal/domain"

	"github.com/google/uuid"
)

type CreateConfigCommand struct {
	configs port.ConfigRepository
	auth    port.AuthService
}

func NewCreateConfigCommand(configs port.ConfigRepository, auth port.AuthService) *CreateConfigCommand {
	return &CreateConfigCommand{configs: configs, auth: auth}
}

type CreateConfigInput struct {
	UserAccessToken    string
	ProjectID          uuid.UUID
	GitHubRepoURL      string
	Environment        string
	InstanceCount      int
	CPULimit           float64
	MemoryLimit        int
	AutoScalingEnabled bool
	MinInstances       int
	MaxInstances       int
	Port               int
	HealthCheckPath    string
	DockerfilePath     string
	DockerBuildContext string
}

func (c *CreateConfigCommand) Execute(ctx context.Context, in CreateConfigInput) (*domain.DeploymentConfig, error) {
	if err := c.auth.VerifyProjectAccess(ctx, in.UserAccessToken, in.ProjectID); err != nil {
		return nil, fmt.Errorf("access denied: %w", err)
	}

	existing, err := c.configs.GetByProjectAndEnv(ctx, in.ProjectID, domain.Environment(in.Environment))
	if err != nil && !errors.Is(err, domain.ErrConfigNotFound) {
		return nil, fmt.Errorf("check existing config: %w", err)
	}
	if existing != nil {
		return nil, domain.ErrConfigAlreadyExists
	}

	cfg := &domain.DeploymentConfig{
		ID:                 uuid.New(),
		ProjectID:          in.ProjectID,
		GitHubRepoURL:      in.GitHubRepoURL,
		Environment:        domain.Environment(in.Environment),
		InstanceCount:      in.InstanceCount,
		CPULimit:           in.CPULimit,
		MemoryLimit:        in.MemoryLimit,
		AutoScalingEnabled: in.AutoScalingEnabled,
		MinInstances:       in.MinInstances,
		MaxInstances:       in.MaxInstances,
		Port:               in.Port,
		HealthCheckPath:    in.HealthCheckPath,
		DockerfilePath:     in.DockerfilePath,
		DockerBuildContext: in.DockerBuildContext,
	}
	if err := cfg.Validate(); err != nil {
		return nil, err
	}
	if err := c.configs.Save(ctx, cfg); err != nil {
		return nil, fmt.Errorf("save config: %w", err)
	}
	return cfg, nil
}
