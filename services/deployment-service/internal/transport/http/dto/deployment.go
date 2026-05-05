package dto

import (
	"time"

	"deployment-service/internal/domain"
)

type DeploymentResponse struct {
	ID            string     `json:"id"`
	ConfigID      string     `json:"config_id"`
	ProjectID     string     `json:"project_id"`
	Version       string     `json:"version"`
	CommitSHA     string     `json:"commit_sha,omitempty"`
	Status        string     `json:"status"`
	ImageURL      string     `json:"image_url,omitempty"`
	DeploymentURL string     `json:"deployment_url,omitempty"`
	ErrorMessage  string     `json:"error_message,omitempty"`
	DeployedAt    *time.Time `json:"deployed_at,omitempty"`
	StoppedAt     *time.Time `json:"stopped_at,omitempty"`
	CreatedAt     time.Time  `json:"created_at"`
	UpdatedAt     time.Time  `json:"updated_at"`
}

type ConfigResponse struct {
	ID                 string    `json:"id"`
	ProjectID          string    `json:"project_id"`
	GitHubRepoURL      string    `json:"github_repo_url"`
	Environment        string    `json:"environment"`
	InstanceCount      int       `json:"instance_count"`
	CPULimit           float64   `json:"cpu_limit"`
	MemoryLimit        int       `json:"memory_limit"`
	AutoScalingEnabled bool      `json:"auto_scaling_enabled"`
	MinInstances       int       `json:"min_instances"`
	MaxInstances       int       `json:"max_instances"`
	Port               int       `json:"port"`
	HealthCheckPath    string    `json:"health_check_path"`
	DockerfilePath     string    `json:"dockerfile_path"`
	DockerBuildContext string    `json:"docker_build_context"`
	CreatedAt          time.Time `json:"created_at"`
	UpdatedAt          time.Time `json:"updated_at"`
}

type LogsResponse struct {
	Logs string `json:"logs"`
}

func FromDeployment(d *domain.Deployment) DeploymentResponse {
	return DeploymentResponse{
		ID:            d.ID.String(),
		ConfigID:      d.ConfigID.String(),
		ProjectID:     d.ProjectID.String(),
		Version:       d.Version,
		CommitSHA:     d.CommitSHA,
		Status:        string(d.Status),
		ImageURL:      d.ImageURL,
		DeploymentURL: d.DeploymentURL,
		ErrorMessage:  d.ErrorMessage,
		DeployedAt:    d.DeployedAt,
		StoppedAt:     d.StoppedAt,
		CreatedAt:     d.CreatedAt,
		UpdatedAt:     d.UpdatedAt,
	}
}

func FromDeployments(deployments []*domain.Deployment) []DeploymentResponse {
	result := make([]DeploymentResponse, len(deployments))
	for i, d := range deployments {
		result[i] = FromDeployment(d)
	}
	return result
}

func FromConfig(c *domain.DeploymentConfig) ConfigResponse {
	return ConfigResponse{
		ID:                 c.ID.String(),
		ProjectID:          c.ProjectID.String(),
		GitHubRepoURL:      c.GitHubRepoURL,
		Environment:        string(c.Environment),
		InstanceCount:      c.InstanceCount,
		CPULimit:           c.CPULimit,
		MemoryLimit:        c.MemoryLimit,
		AutoScalingEnabled: c.AutoScalingEnabled,
		MinInstances:       c.MinInstances,
		MaxInstances:       c.MaxInstances,
		Port:               c.Port,
		HealthCheckPath:    c.HealthCheckPath,
		DockerfilePath:     c.DockerfilePath,
		DockerBuildContext: c.DockerBuildContext,
		CreatedAt:          c.CreatedAt,
		UpdatedAt:          c.UpdatedAt,
	}
}
