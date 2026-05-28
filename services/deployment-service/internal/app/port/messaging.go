package port

import (
	"context"

	"github.com/google/uuid"
)

type Publisher interface {
	PublishBuilding(ctx context.Context, deploymentID, projectID uuid.UUID, correlationID string) error
	PublishDeploying(ctx context.Context, deploymentID, projectID uuid.UUID, correlationID string) error
	PublishRunning(ctx context.Context, deploymentID, projectID uuid.UUID, imageURL, deploymentURL, correlationID string) error
	PublishFailed(ctx context.Context, deploymentID, projectID uuid.UUID, reason, correlationID string) error
}
