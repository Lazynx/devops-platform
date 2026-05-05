package port

import (
	"context"

	"github.com/google/uuid"
)

type Publisher interface {
	PublishBuilding(ctx context.Context, deploymentID, projectID uuid.UUID) error
	PublishDeploying(ctx context.Context, deploymentID, projectID uuid.UUID) error
	PublishRunning(ctx context.Context, deploymentID, projectID uuid.UUID, imageURL, deploymentURL string) error
	PublishFailed(ctx context.Context, deploymentID, projectID uuid.UUID, reason string) error
}
