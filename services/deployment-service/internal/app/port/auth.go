package port

import (
	"context"

	"github.com/google/uuid"
)

type AuthService interface {
	GetGitHubToken(ctx context.Context, userAccessToken string) (string, error)
	VerifyProjectAccess(ctx context.Context, userAccessToken string, projectID uuid.UUID) error
}
