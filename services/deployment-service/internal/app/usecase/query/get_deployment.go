package query

import (
	"context"

	"deployment-service/internal/app/port"
	"deployment-service/internal/domain"

	"github.com/google/uuid"
)

type GetDeployment struct {
	repo port.DeploymentRepository
}

func NewGetDeployment(repo port.DeploymentRepository) *GetDeployment {
	return &GetDeployment{repo: repo}
}

func (q *GetDeployment) Execute(ctx context.Context, id uuid.UUID) (*domain.Deployment, error) {
	return q.repo.GetByID(ctx, id)
}
