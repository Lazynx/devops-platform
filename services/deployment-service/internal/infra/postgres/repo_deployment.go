package postgres

import (
	"context"
	"errors"
	"fmt"
	"time"

	"deployment-service/internal/domain"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type DeploymentRepo struct {
	pool *pgxpool.Pool
}

func NewDeploymentRepo(pool *pgxpool.Pool) *DeploymentRepo {
	return &DeploymentRepo{pool: pool}
}

func (r *DeploymentRepo) Save(ctx context.Context, d *domain.Deployment) error {
	_, err := r.pool.Exec(ctx, `
		INSERT INTO deployments
		    (id, config_id, project_id, version, commit_sha, image_url, deployment_url,
		     status, error_message, deployed_at, stopped_at, created_at, updated_at)
		VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
		ON CONFLICT (id) DO UPDATE SET
		    status          = EXCLUDED.status,
		    image_url       = EXCLUDED.image_url,
		    deployment_url  = EXCLUDED.deployment_url,
		    error_message   = EXCLUDED.error_message,
		    deployed_at     = EXCLUDED.deployed_at,
		    stopped_at      = EXCLUDED.stopped_at,
		    updated_at      = EXCLUDED.updated_at`,
		d.ID, d.ConfigID, d.ProjectID, d.Version, d.CommitSHA,
		nullStr(d.ImageURL), nullStr(d.DeploymentURL),
		string(d.Status), nullStr(d.ErrorMessage),
		d.DeployedAt, d.StoppedAt, d.CreatedAt, d.UpdatedAt,
	)
	if err != nil {
		return fmt.Errorf("repo.deployment.Save: %w", err)
	}
	return nil
}

func (r *DeploymentRepo) GetByID(ctx context.Context, id uuid.UUID) (*domain.Deployment, error) {
	row := r.pool.QueryRow(ctx, `
		SELECT id, config_id, project_id, version, commit_sha, image_url, deployment_url,
		       status, error_message, deployed_at, stopped_at, created_at, updated_at
		FROM deployments WHERE id = $1`, id)

	d, err := scanDeployment(row)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, domain.ErrDeploymentNotFound
		}
		return nil, fmt.Errorf("repo.deployment.GetByID: %w", err)
	}
	return d, nil
}

func (r *DeploymentRepo) GetByProjectID(ctx context.Context, projectID uuid.UUID) ([]*domain.Deployment, error) {
	rows, err := r.pool.Query(ctx, `
		SELECT id, config_id, project_id, version, commit_sha, image_url, deployment_url,
		       status, error_message, deployed_at, stopped_at, created_at, updated_at
		FROM deployments WHERE project_id = $1 ORDER BY created_at DESC`, projectID)
	if err != nil {
		return nil, fmt.Errorf("repo.deployment.GetByProjectID: %w", err)
	}
	defer rows.Close()
	return collectDeployments(rows)
}

func (r *DeploymentRepo) GetByConfigID(ctx context.Context, configID uuid.UUID) ([]*domain.Deployment, error) {
	rows, err := r.pool.Query(ctx, `
		SELECT id, config_id, project_id, version, commit_sha, image_url, deployment_url,
		       status, error_message, deployed_at, stopped_at, created_at, updated_at
		FROM deployments WHERE config_id = $1 ORDER BY created_at DESC`, configID)
	if err != nil {
		return nil, fmt.Errorf("repo.deployment.GetByConfigID: %w", err)
	}
	defer rows.Close()
	return collectDeployments(rows)
}

func (r *DeploymentRepo) DeleteByConfigID(ctx context.Context, configID uuid.UUID) error {
	_, err := r.pool.Exec(ctx, `DELETE FROM deployments WHERE config_id = $1`, configID)
	if err != nil {
		return fmt.Errorf("repo.deployment.DeleteByConfigID: %w", err)
	}
	return nil
}

func scanDeployment(row pgx.Row) (*domain.Deployment, error) {
	var d domain.Deployment
	var status string
	var commitSHA, imageURL, deploymentURL, errMsg *string
	var deployedAt, stoppedAt *time.Time

	if err := row.Scan(
		&d.ID, &d.ConfigID, &d.ProjectID, &d.Version, &commitSHA,
		&imageURL, &deploymentURL, &status, &errMsg,
		&deployedAt, &stoppedAt, &d.CreatedAt, &d.UpdatedAt,
	); err != nil {
		return nil, err
	}

	d.Status = domain.DeploymentStatus(status)
	if commitSHA != nil {
		d.CommitSHA = *commitSHA
	}
	if imageURL != nil {
		d.ImageURL = *imageURL
	}
	if deploymentURL != nil {
		d.DeploymentURL = *deploymentURL
	}
	if errMsg != nil {
		d.ErrorMessage = *errMsg
	}
	d.DeployedAt = deployedAt
	d.StoppedAt = stoppedAt
	return &d, nil
}

func collectDeployments(rows pgx.Rows) ([]*domain.Deployment, error) {
	var result []*domain.Deployment
	for rows.Next() {
		d, err := scanDeployment(rows)
		if err != nil {
			return nil, err
		}
		result = append(result, d)
	}
	return result, rows.Err()
}

func nullStr(s string) *string {
	if s == "" {
		return nil
	}
	return &s
}
