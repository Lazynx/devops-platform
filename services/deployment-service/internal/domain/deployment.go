package domain

import (
	"fmt"
	"time"

	"github.com/google/uuid"
)

type DeploymentStatus string

const (
	StatusPending   DeploymentStatus = "pending"
	StatusBuilding  DeploymentStatus = "building"
	StatusDeploying DeploymentStatus = "deploying"
	StatusRunning   DeploymentStatus = "running"
	StatusFailed    DeploymentStatus = "failed"
	StatusStopped   DeploymentStatus = "stopped"
)

var validTransitions = map[DeploymentStatus][]DeploymentStatus{
	StatusPending:   {StatusBuilding, StatusFailed},
	StatusBuilding:  {StatusDeploying, StatusFailed},
	StatusDeploying: {StatusRunning, StatusFailed},
	StatusRunning:   {StatusStopped, StatusFailed},
	StatusFailed:    {},
	StatusStopped:   {},
}

type Deployment struct {
	ID            uuid.UUID
	ConfigID      uuid.UUID
	ProjectID     uuid.UUID
	Version       string
	CommitSHA     string
	ImageURL      string
	DeploymentURL string
	Status        DeploymentStatus
	ErrorMessage  string
	DeployedAt    *time.Time
	StoppedAt     *time.Time
	CreatedAt     time.Time
	UpdatedAt     time.Time
}

func NewDeployment(configID, projectID uuid.UUID, version, commitSHA string) *Deployment {
	now := time.Now().UTC()
	return &Deployment{
		ID:        uuid.New(),
		ConfigID:  configID,
		ProjectID: projectID,
		Version:   version,
		CommitSHA: commitSHA,
		Status:    StatusPending,
		CreatedAt: now,
		UpdatedAt: now,
	}
}

func (d *Deployment) canTransitionTo(next DeploymentStatus) bool {
	for _, s := range validTransitions[d.Status] {
		if s == next {
			return true
		}
	}
	return false
}

func (d *Deployment) MarkBuilding() error {
	if !d.canTransitionTo(StatusBuilding) {
		return ErrInvalidTransition{From: d.Status, To: StatusBuilding}
	}
	d.Status = StatusBuilding
	d.UpdatedAt = time.Now().UTC()
	return nil
}

func (d *Deployment) MarkDeploying() error {
	if !d.canTransitionTo(StatusDeploying) {
		return ErrInvalidTransition{From: d.Status, To: StatusDeploying}
	}
	d.Status = StatusDeploying
	d.UpdatedAt = time.Now().UTC()
	return nil
}

func (d *Deployment) MarkRunning(imageURL, deploymentURL string) error {
	if !d.canTransitionTo(StatusRunning) {
		return ErrInvalidTransition{From: d.Status, To: StatusRunning}
	}
	now := time.Now().UTC()
	d.Status = StatusRunning
	d.ImageURL = imageURL
	d.DeploymentURL = deploymentURL
	d.DeployedAt = &now
	d.UpdatedAt = now
	return nil
}

func (d *Deployment) MarkFailed(reason string) {
	d.Status = StatusFailed
	d.ErrorMessage = reason
	d.UpdatedAt = time.Now().UTC()
}

func (d *Deployment) MarkStopped() error {
	if !d.canTransitionTo(StatusStopped) {
		return ErrInvalidTransition{From: d.Status, To: StatusStopped}
	}
	now := time.Now().UTC()
	d.Status = StatusStopped
	d.StoppedAt = &now
	d.UpdatedAt = now
	return nil
}

func (d *Deployment) NomadBuildJobID() string {
	return fmt.Sprintf("build-%s-%s", d.ProjectID, d.Version)
}

func (d *Deployment) NomadAppJobID() string {
	return fmt.Sprintf("app-%s", d.ID)
}
