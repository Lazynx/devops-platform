package postgres

import (
	"context"
	"errors"
	"fmt"

	"deployment-service/internal/domain"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type ConfigRepo struct {
	pool *pgxpool.Pool
}

func NewConfigRepo(pool *pgxpool.Pool) *ConfigRepo {
	return &ConfigRepo{pool: pool}
}

func (r *ConfigRepo) Save(ctx context.Context, c *domain.DeploymentConfig) error {
	_, err := r.pool.Exec(ctx, `
		INSERT INTO deployment_configs
		    (id, project_id, github_repo_url, environment, instance_count, cpu_limit, memory_limit,
		     auto_scaling_enabled, min_instances, max_instances, port, health_check_path,
		     dockerfile_path, docker_build_context, created_at, updated_at)
		VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16)
		ON CONFLICT (id) DO UPDATE SET
		    instance_count       = EXCLUDED.instance_count,
		    cpu_limit            = EXCLUDED.cpu_limit,
		    memory_limit         = EXCLUDED.memory_limit,
		    auto_scaling_enabled = EXCLUDED.auto_scaling_enabled,
		    min_instances        = EXCLUDED.min_instances,
		    max_instances        = EXCLUDED.max_instances,
		    updated_at           = EXCLUDED.updated_at`,
		c.ID, c.ProjectID, c.GitHubRepoURL, string(c.Environment),
		c.InstanceCount, c.CPULimit, c.MemoryLimit,
		c.AutoScalingEnabled, c.MinInstances, c.MaxInstances,
		c.Port, c.HealthCheckPath, c.DockerfilePath, c.DockerBuildContext,
		c.CreatedAt, c.UpdatedAt,
	)
	if err != nil {
		return fmt.Errorf("repo.config.Save: %w", err)
	}
	return nil
}

func (r *ConfigRepo) GetByID(ctx context.Context, id uuid.UUID) (*domain.DeploymentConfig, error) {
	row := r.pool.QueryRow(ctx, `
		SELECT id, project_id, github_repo_url, environment, instance_count, cpu_limit, memory_limit,
		       auto_scaling_enabled, min_instances, max_instances, port, health_check_path,
		       dockerfile_path, docker_build_context, created_at, updated_at
		FROM deployment_configs WHERE id = $1`, id)

	c, err := scanConfig(row)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, domain.ErrConfigNotFound
		}
		return nil, fmt.Errorf("repo.config.GetByID: %w", err)
	}
	return c, nil
}

func (r *ConfigRepo) GetByProjectID(ctx context.Context, projectID uuid.UUID) ([]*domain.DeploymentConfig, error) {
	rows, err := r.pool.Query(ctx, `
		SELECT id, project_id, github_repo_url, environment, instance_count, cpu_limit, memory_limit,
		       auto_scaling_enabled, min_instances, max_instances, port, health_check_path,
		       dockerfile_path, docker_build_context, created_at, updated_at
		FROM deployment_configs WHERE project_id = $1`, projectID)
	if err != nil {
		return nil, fmt.Errorf("repo.config.GetByProjectID: %w", err)
	}
	defer rows.Close()

	var result []*domain.DeploymentConfig
	for rows.Next() {
		c, err := scanConfig(rows)
		if err != nil {
			return nil, err
		}
		result = append(result, c)
	}
	return result, rows.Err()
}

func (r *ConfigRepo) GetByProjectAndEnv(ctx context.Context, projectID uuid.UUID, env domain.Environment) (*domain.DeploymentConfig, error) {
	row := r.pool.QueryRow(ctx, `
		SELECT id, project_id, github_repo_url, environment, instance_count, cpu_limit, memory_limit,
		       auto_scaling_enabled, min_instances, max_instances, port, health_check_path,
		       dockerfile_path, docker_build_context, created_at, updated_at
		FROM deployment_configs WHERE project_id = $1 AND environment = $2`, projectID, string(env))

	c, err := scanConfig(row)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, domain.ErrConfigNotFound
		}
		return nil, fmt.Errorf("repo.config.GetByProjectAndEnv: %w", err)
	}
	return c, nil
}

func (r *ConfigRepo) DeleteByProjectID(ctx context.Context, projectID uuid.UUID) error {
	_, err := r.pool.Exec(ctx, `DELETE FROM deployment_configs WHERE project_id = $1`, projectID)
	if err != nil {
		return fmt.Errorf("repo.config.DeleteByProjectID: %w", err)
	}
	return nil
}

func scanConfig(row pgx.Row) (*domain.DeploymentConfig, error) {
	var c domain.DeploymentConfig
	var env string
	if err := row.Scan(
		&c.ID, &c.ProjectID, &c.GitHubRepoURL, &env,
		&c.InstanceCount, &c.CPULimit, &c.MemoryLimit,
		&c.AutoScalingEnabled, &c.MinInstances, &c.MaxInstances,
		&c.Port, &c.HealthCheckPath, &c.DockerfilePath, &c.DockerBuildContext,
		&c.CreatedAt, &c.UpdatedAt,
	); err != nil {
		return nil, err
	}
	c.Environment = domain.Environment(env)
	return &c, nil
}
