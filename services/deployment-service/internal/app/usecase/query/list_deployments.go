package query

import (
	"context"

	"deployment-service/internal/app/port"
	"deployment-service/internal/domain"

	"github.com/google/uuid"
)

type ListDeployments struct {
	repo port.DeploymentRepository
}

func NewListDeployments(repo port.DeploymentRepository) *ListDeployments {
	return &ListDeployments{repo: repo}
}

func (q *ListDeployments) Execute(ctx context.Context, projectID uuid.UUID) ([]*domain.Deployment, error) {
	return q.repo.GetByProjectID(ctx, projectID)
}
