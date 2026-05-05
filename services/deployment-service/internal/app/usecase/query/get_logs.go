package query

import (
	"context"
	"fmt"

	"deployment-service/internal/app/port"
	"deployment-service/internal/domain"

	"github.com/google/uuid"
)

type GetLogs struct {
	repo  port.DeploymentRepository
	nomad port.NomadClient
}

func NewGetLogs(repo port.DeploymentRepository, nomad port.NomadClient) *GetLogs {
	return &GetLogs{repo: repo, nomad: nomad}
}

func (q *GetLogs) Execute(ctx context.Context, deploymentID uuid.UUID, tail int) (string, error) {
	d, err := q.repo.GetByID(ctx, deploymentID)
	if err != nil {
		return "", fmt.Errorf("get deployment: %w", err)
	}

	switch d.Status {
	case domain.StatusBuilding:
		return q.nomad.GetLogs(ctx, d.NomadBuildJobID(), "build-and-push", tail)

	case domain.StatusDeploying:
		logs, err := q.nomad.GetLogs(ctx, d.NomadBuildJobID(), "build-and-push", tail)
		if err != nil {
			return fmt.Sprintf("[Build completed]\n[logs unavailable: %v]\n\n[Deploying...]", err), nil
		}
		return fmt.Sprintf("[Build completed]\n%s\n\n[Deploying...]", logs), nil

	default:
		logs, err := q.nomad.GetLogs(ctx, d.NomadAppJobID(), "server", tail)
		if err != nil {
			return q.nomad.GetLogs(ctx, d.NomadBuildJobID(), "build-and-push", tail)
		}
		return logs, nil
	}
}
