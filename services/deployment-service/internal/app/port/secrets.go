package port

import (
	"context"

	"github.com/google/uuid"
)

type SecretRef struct {
	Key       string
	VaultPath string
}

type SecretsFetcher interface {
	FetchForProject(ctx context.Context, projectID uuid.UUID) ([]SecretRef, error)
}
