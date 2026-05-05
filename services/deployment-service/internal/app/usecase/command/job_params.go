package command

import "deployment-service/internal/app/port"

type BuildJobParams struct {
	ProjectID        string
	Version          string
	GitHubRepoURL    string
	GitHubToken      string
	DockerfilePath   string
	BuildContext     string
	ImageTag         string
	RegistryURL      string
	RegistryRepo     string
	RegistryUser     string
	RegistryPassword string
}

type DeployJobParams struct {
	DeploymentID     string
	ProjectID        string
	ProjectName      string
	ImageURL         string
	Port             int
	StartCommand     string
	Secrets          []port.SecretRef
	RegistryURL      string
	RegistryUser     string
	RegistryPassword string
	Hostname         string
}
