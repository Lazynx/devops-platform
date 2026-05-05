package command

import (
	"context"
	"fmt"
	"log/slog"

	"deployment-service/internal/app/port"

	"github.com/google/uuid"
)

type DeleteProjectCommand struct {
	deployments port.DeploymentRepository
	configs     port.ConfigRepository
	nomad       port.NomadClient
}

func NewDeleteProjectCommand(
	deployments port.DeploymentRepository,
	configs port.ConfigRepository,
	nomad port.NomadClient,
) *DeleteProjectCommand {
	return &DeleteProjectCommand{deployments: deployments, configs: configs, nomad: nomad}
}

type DeleteProjectInput struct {
	ProjectID     uuid.UUID
	CorrelationID string
}

func (c *DeleteProjectCommand) Execute(ctx context.Context, in DeleteProjectInput) error {
	log := slog.Default().With("project_id", in.ProjectID, "correlation_id", in.CorrelationID)

	cfgs, err := c.configs.GetByProjectID(ctx, in.ProjectID)
	if err != nil {
		return fmt.Errorf("get configs: %w", err)
	}

	for _, cfg := range cfgs {
		deps, err := c.deployments.GetByConfigID(ctx, cfg.ID)
		if err != nil {
			log.Warn("failed to get deployments for config", "config_id", cfg.ID, "err", err)
			continue
		}
		for _, d := range deps {
			if err := c.nomad.StopJob(ctx, d.NomadAppJobID(), true); err != nil {
				log.Warn("failed to stop app job", "job_id", d.NomadAppJobID(), "err", err)
			}
			if err := c.nomad.StopJob(ctx, d.NomadBuildJobID(), true); err != nil {
				log.Warn("failed to stop build job", "job_id", d.NomadBuildJobID(), "err", err)
			}
		}
		if err := c.deployments.DeleteByConfigID(ctx, cfg.ID); err != nil {
			log.Warn("failed to delete deployments", "config_id", cfg.ID, "err", err)
		}
	}

	if err := c.configs.DeleteByProjectID(ctx, in.ProjectID); err != nil {
		return fmt.Errorf("delete configs: %w", err)
	}

	log.Info("project resources deleted")
	return nil
}
