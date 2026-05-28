package command

import (
	"context"
	"fmt"

	"deployment-service/internal/app/port"
	"deployment-service/internal/domain"
	"deployment-service/internal/metrics"

	"github.com/google/uuid"
)

type StopCommand struct {
	deployments port.DeploymentRepository
	nomad       port.NomadClient
}

func NewStopCommand(deployments port.DeploymentRepository, nomad port.NomadClient) *StopCommand {
	return &StopCommand{deployments: deployments, nomad: nomad}
}

func (c *StopCommand) Execute(ctx context.Context, deploymentID uuid.UUID) error {
	d, err := c.deployments.GetByID(ctx, deploymentID)
	if err != nil {
		return fmt.Errorf("get deployment: %w", err)
	}

	if d.Status != domain.StatusRunning {
		return domain.ErrNotRunning
	}

	if err := c.nomad.StopJob(ctx, d.NomadAppJobID(), true); err != nil {
		return fmt.Errorf("stop nomad job: %w", err)
	}

	if err := d.MarkStopped(); err != nil {
		return err
	}

	if err := c.deployments.Save(ctx, d); err != nil {
		return fmt.Errorf("save stopped deployment: %w", err)
	}

	metrics.ActiveDeployments.WithLabelValues("").Dec()
	return nil
}
