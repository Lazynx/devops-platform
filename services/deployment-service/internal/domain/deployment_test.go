package domain

import (
	"strings"
	"testing"

	"github.com/google/uuid"
)

func TestNewDeployment_Defaults(t *testing.T) {
	configID := uuid.New()
	projectID := uuid.New()

	d := NewDeployment(configID, projectID, "v1", "abc123")

	if d.ID == uuid.Nil {
		t.Error("expected non-nil ID")
	}
	if d.ConfigID != configID {
		t.Errorf("expected configID %s, got %s", configID, d.ConfigID)
	}
	if d.ProjectID != projectID {
		t.Errorf("expected projectID %s, got %s", projectID, d.ProjectID)
	}
	if d.Version != "v1" {
		t.Errorf("expected version v1, got %s", d.Version)
	}
	if d.CommitSHA != "abc123" {
		t.Errorf("expected commitSHA abc123, got %s", d.CommitSHA)
	}
	if d.Status != StatusPending {
		t.Errorf("expected status pending, got %s", d.Status)
	}
	if d.DeployedAt != nil {
		t.Error("expected DeployedAt to be nil")
	}
	if d.StoppedAt != nil {
		t.Error("expected StoppedAt to be nil")
	}
}

func TestDeployment_HappyPath(t *testing.T) {
	d := NewDeployment(uuid.New(), uuid.New(), "v1", "sha")

	if err := d.MarkBuilding(); err != nil {
		t.Fatalf("MarkBuilding: %v", err)
	}
	if d.Status != StatusBuilding {
		t.Errorf("expected building, got %s", d.Status)
	}

	if err := d.MarkDeploying(); err != nil {
		t.Fatalf("MarkDeploying: %v", err)
	}
	if d.Status != StatusDeploying {
		t.Errorf("expected deploying, got %s", d.Status)
	}

	if err := d.MarkRunning("registry/img:latest", "http://app.localhost"); err != nil {
		t.Fatalf("MarkRunning: %v", err)
	}
	if d.Status != StatusRunning {
		t.Errorf("expected running, got %s", d.Status)
	}
	if d.ImageURL != "registry/img:latest" {
		t.Errorf("unexpected ImageURL: %s", d.ImageURL)
	}
	if d.DeployedAt == nil {
		t.Error("expected DeployedAt to be set")
	}

	if err := d.MarkStopped(); err != nil {
		t.Fatalf("MarkStopped: %v", err)
	}
	if d.Status != StatusStopped {
		t.Errorf("expected stopped, got %s", d.Status)
	}
	if d.StoppedAt == nil {
		t.Error("expected StoppedAt to be set")
	}
}

func TestDeployment_MarkFailed_FromAnyState(t *testing.T) {
	states := []struct {
		name  string
		setup func(*Deployment)
	}{
		{"from pending", func(d *Deployment) {}},
		{"from building", func(d *Deployment) { _ = d.MarkBuilding() }},
		{"from deploying", func(d *Deployment) {
			_ = d.MarkBuilding()
			_ = d.MarkDeploying()
		}},
		{"from running", func(d *Deployment) {
			_ = d.MarkBuilding()
			_ = d.MarkDeploying()
			_ = d.MarkRunning("img", "url")
		}},
	}

	for _, tc := range states {
		t.Run(tc.name, func(t *testing.T) {
			d := NewDeployment(uuid.New(), uuid.New(), "v1", "sha")
			tc.setup(d)
			d.MarkFailed("something went wrong")
			if d.Status != StatusFailed {
				t.Errorf("expected failed, got %s", d.Status)
			}
			if d.ErrorMessage != "something went wrong" {
				t.Errorf("expected error message, got %s", d.ErrorMessage)
			}
		})
	}
}

func TestDeployment_InvalidTransitions(t *testing.T) {
	cases := []struct {
		name  string
		setup func(*Deployment)
		op    func(*Deployment) error
	}{
		{
			name:  "pending to deploying",
			setup: func(d *Deployment) {},
			op:    func(d *Deployment) error { return d.MarkDeploying() },
		},
		{
			name:  "pending to running",
			setup: func(d *Deployment) {},
			op:    func(d *Deployment) error { return d.MarkRunning("img", "url") },
		},
		{
			name:  "building to running",
			setup: func(d *Deployment) { _ = d.MarkBuilding() },
			op:    func(d *Deployment) error { return d.MarkRunning("img", "url") },
		},
		{
			name:  "stopped to building",
			setup: func(d *Deployment) {
				_ = d.MarkBuilding()
				_ = d.MarkDeploying()
				_ = d.MarkRunning("img", "url")
				_ = d.MarkStopped()
			},
			op: func(d *Deployment) error { return d.MarkBuilding() },
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			d := NewDeployment(uuid.New(), uuid.New(), "v1", "sha")
			tc.setup(d)
			err := tc.op(d)
			if err == nil {
				t.Error("expected error for invalid transition, got nil")
			}
			var transErr ErrInvalidTransition
			if _, ok := err.(ErrInvalidTransition); !ok {
				_ = transErr
				t.Errorf("expected ErrInvalidTransition, got %T: %v", err, err)
			}
		})
	}
}

func TestDeployment_NomadJobIDs(t *testing.T) {
	projectID := uuid.New()
	d := NewDeployment(uuid.New(), projectID, "v2", "sha")

	buildID := d.NomadBuildJobID()
	if !strings.Contains(buildID, projectID.String()) {
		t.Errorf("build job ID should contain projectID, got: %s", buildID)
	}
	if !strings.HasPrefix(buildID, "build-") {
		t.Errorf("build job ID should start with 'build-', got: %s", buildID)
	}

	appID := d.NomadAppJobID()
	if !strings.Contains(appID, d.ID.String()) {
		t.Errorf("app job ID should contain deploymentID, got: %s", appID)
	}
	if !strings.HasPrefix(appID, "app-") {
		t.Errorf("app job ID should start with 'app-', got: %s", appID)
	}
}

func TestErrInvalidTransition_Error(t *testing.T) {
	err := ErrInvalidTransition{From: StatusPending, To: StatusRunning}
	msg := err.Error()
	if !strings.Contains(msg, "pending") || !strings.Contains(msg, "running") {
		t.Errorf("error message should mention both states: %s", msg)
	}
}
