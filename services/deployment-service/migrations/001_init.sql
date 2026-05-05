CREATE TABLE IF NOT EXISTS deployment_configs (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id          UUID        NOT NULL,
    github_repo_url     VARCHAR(512) NOT NULL,
    environment         VARCHAR(20) NOT NULL DEFAULT 'development',
    instance_count      INTEGER     NOT NULL DEFAULT 1,
    cpu_limit           DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    memory_limit        INTEGER     NOT NULL DEFAULT 512,
    auto_scaling_enabled BOOLEAN    NOT NULL DEFAULT false,
    min_instances       INTEGER     NOT NULL DEFAULT 1,
    max_instances       INTEGER     NOT NULL DEFAULT 10,
    port                INTEGER     NOT NULL DEFAULT 8000,
    health_check_path   VARCHAR(255) NOT NULL DEFAULT '/health',
    dockerfile_path     VARCHAR(255) NOT NULL DEFAULT './Dockerfile',
    docker_build_context VARCHAR(255) NOT NULL DEFAULT '.',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_deployment_configs_project_env UNIQUE (project_id, environment)
);

CREATE TABLE IF NOT EXISTS deployments (
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id      UUID        NOT NULL REFERENCES deployment_configs(id) ON DELETE CASCADE,
    project_id     UUID        NOT NULL,
    version        VARCHAR(255) NOT NULL,
    commit_sha     VARCHAR(255),
    image_url      VARCHAR(512),
    deployment_url VARCHAR(512),
    status         VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message  TEXT,
    deployed_at    TIMESTAMPTZ,
    stopped_at     TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_deployments_project_id  ON deployments(project_id);
CREATE INDEX IF NOT EXISTS idx_deployments_config_id   ON deployments(config_id);
CREATE INDEX IF NOT EXISTS idx_configs_project_id      ON deployment_configs(project_id);
CREATE INDEX IF NOT EXISTS idx_configs_project_env     ON deployment_configs(project_id, environment);
