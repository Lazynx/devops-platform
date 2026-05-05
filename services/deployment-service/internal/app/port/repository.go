package port

import (
	"context"

	"deployment-service/internal/domain"

	"github.com/google/uuid"
)

type DeploymentRepository interface {
	Save(ctx context.Context, d *domain.Deployment) error
	GetByID(ctx context.Context, id uuid.UUID) (*domain.Deployment, error)
	GetByProjectID(ctx context.Context, projectID uuid.UUID) ([]*domain.Deployment, error)
	GetByConfigID(ctx context.Context, configID uuid.UUID) ([]*domain.Deployment, error)
	DeleteByConfigID(ctx context.Context, configID uuid.UUID) error
}

type ConfigRepository interface {
	Save(ctx context.Context, c *domain.DeploymentConfig) error
	GetByID(ctx context.Context, id uuid.UUID) (*domain.DeploymentConfig, error)
	GetByProjectID(ctx context.Context, projectID uuid.UUID) ([]*domain.DeploymentConfig, error)
	GetByProjectAndEnv(ctx context.Context, projectID uuid.UUID, env domain.Environment) (*domain.DeploymentConfig, error)
	DeleteByProjectID(ctx context.Context, projectID uuid.UUID) error
}
