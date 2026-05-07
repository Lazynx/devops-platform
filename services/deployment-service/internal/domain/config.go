package domain

import (
	"fmt"
	"time"

	"github.com/google/uuid"
)

type Environment string

const (
	EnvDevelopment Environment = "development"
	EnvStaging     Environment = "staging"
	EnvProduction  Environment = "production"
)

type DeploymentConfig struct {
	ID                 uuid.UUID
	ProjectID          uuid.UUID
	GitHubRepoURL      string
	Environment        Environment
	InstanceCount      int
	CPULimit           float64
	MemoryLimit        int
	AutoScalingEnabled bool
	MinInstances       int
	MaxInstances       int
	Port               int
	HealthCheckPath    string
	DockerfilePath     string
	DockerBuildContext string
	CreatedAt          time.Time
	UpdatedAt          time.Time
}

func NewDeploymentConfig(projectID uuid.UUID, repoURL string, env Environment) *DeploymentConfig {
	now := time.Now().UTC()
	return &DeploymentConfig{
		ID:                 uuid.New(),
		ProjectID:          projectID,
		GitHubRepoURL:      repoURL,
		Environment:        env,
		InstanceCount:      1,
		CPULimit:           1.0,
		MemoryLimit:        512,
		AutoScalingEnabled: false,
		MinInstances:       1,
		MaxInstances:       10,
		Port:               8000,
		HealthCheckPath:    "/health",
		DockerfilePath:     "./Dockerfile",
		DockerBuildContext: ".",
		CreatedAt:          now,
		UpdatedAt:          now,
	}
}

func (c *DeploymentConfig) Validate() error {
	if c.Port < 1 || c.Port > 65535 {
		return fmt.Errorf("port must be between 1 and 65535, got %d", c.Port)
	}
	if c.InstanceCount < 1 || c.InstanceCount > 20 {
		return fmt.Errorf("instance_count must be between 1 and 20, got %d", c.InstanceCount)
	}
	if c.CPULimit < 0.1 || c.CPULimit > 16.0 {
		return fmt.Errorf("cpu_limit must be between 0.1 and 16.0, got %.2f", c.CPULimit)
	}
	if c.MemoryLimit < 128 || c.MemoryLimit > 32768 {
		return fmt.Errorf("memory_limit must be between 128 and 32768 MB, got %d", c.MemoryLimit)
	}
	if c.AutoScalingEnabled {
		if c.MinInstances >= c.MaxInstances {
			return fmt.Errorf("min_instances (%d) must be less than max_instances (%d)", c.MinInstances, c.MaxInstances)
		}
		if c.MaxInstances > 50 {
			return fmt.Errorf("max_instances cannot exceed 50, got %d", c.MaxInstances)
		}
	}
	return nil
}
