package domain

import (
	"testing"

	"github.com/google/uuid"
)

func TestNewDeploymentConfig_Defaults(t *testing.T) {
	projectID := uuid.New()
	c := NewDeploymentConfig(projectID, "https://github.com/o/r", EnvDevelopment)

	if c.ID == uuid.Nil {
		t.Error("expected non-nil ID")
	}
	if c.ProjectID != projectID {
		t.Errorf("wrong projectID: %s", c.ProjectID)
	}
	if c.Environment != EnvDevelopment {
		t.Errorf("wrong environment: %s", c.Environment)
	}
	if c.InstanceCount != 1 {
		t.Errorf("default InstanceCount should be 1, got %d", c.InstanceCount)
	}
	if c.CPULimit != 1.0 {
		t.Errorf("default CPULimit should be 1.0, got %f", c.CPULimit)
	}
	if c.MemoryLimit != 512 {
		t.Errorf("default MemoryLimit should be 512, got %d", c.MemoryLimit)
	}
	if c.Port != 8000 {
		t.Errorf("default Port should be 8000, got %d", c.Port)
	}
	if c.HealthCheckPath != "/health" {
		t.Errorf("default HealthCheckPath should be /health, got %s", c.HealthCheckPath)
	}
	if c.AutoScalingEnabled {
		t.Error("AutoScalingEnabled should be false by default")
	}
}

func TestDeploymentConfig_Validate_Valid(t *testing.T) {
	c := NewDeploymentConfig(uuid.New(), "https://github.com/o/r", EnvProduction)
	if err := c.Validate(); err != nil {
		t.Errorf("expected valid config, got error: %v", err)
	}
}

func TestDeploymentConfig_Validate_InvalidPort(t *testing.T) {
	cases := []int{0, -1, 65536, 99999}
	for _, port := range cases {
		c := NewDeploymentConfig(uuid.New(), "https://github.com/o/r", EnvDevelopment)
		c.Port = port
		if err := c.Validate(); err == nil {
			t.Errorf("expected error for port %d", port)
		}
	}
}

func TestDeploymentConfig_Validate_ValidPort(t *testing.T) {
	cases := []int{1, 80, 8080, 65535}
	for _, port := range cases {
		c := NewDeploymentConfig(uuid.New(), "https://github.com/o/r", EnvDevelopment)
		c.Port = port
		if err := c.Validate(); err != nil {
			t.Errorf("expected valid for port %d, got: %v", port, err)
		}
	}
}

func TestDeploymentConfig_Validate_InvalidInstanceCount(t *testing.T) {
	cases := []int{0, 21, 100}
	for _, count := range cases {
		c := NewDeploymentConfig(uuid.New(), "https://github.com/o/r", EnvDevelopment)
		c.InstanceCount = count
		if err := c.Validate(); err == nil {
			t.Errorf("expected error for instance_count %d", count)
		}
	}
}

func TestDeploymentConfig_Validate_InvalidCPU(t *testing.T) {
	cases := []float64{0.0, 0.09, 16.1, 100.0}
	for _, cpu := range cases {
		c := NewDeploymentConfig(uuid.New(), "https://github.com/o/r", EnvDevelopment)
		c.CPULimit = cpu
		if err := c.Validate(); err == nil {
			t.Errorf("expected error for cpu_limit %f", cpu)
		}
	}
}

func TestDeploymentConfig_Validate_InvalidMemory(t *testing.T) {
	cases := []int{0, 127, 32769, 65536}
	for _, mem := range cases {
		c := NewDeploymentConfig(uuid.New(), "https://github.com/o/r", EnvDevelopment)
		c.MemoryLimit = mem
		if err := c.Validate(); err == nil {
			t.Errorf("expected error for memory_limit %d", mem)
		}
	}
}

func TestDeploymentConfig_Validate_AutoScaling_MinGtMax(t *testing.T) {
	c := NewDeploymentConfig(uuid.New(), "https://github.com/o/r", EnvProduction)
	c.AutoScalingEnabled = true
	c.MinInstances = 5
	c.MaxInstances = 3

	if err := c.Validate(); err == nil {
		t.Error("expected error when min_instances >= max_instances")
	}
}

func TestDeploymentConfig_Validate_AutoScaling_EqualMinMax(t *testing.T) {
	c := NewDeploymentConfig(uuid.New(), "https://github.com/o/r", EnvProduction)
	c.AutoScalingEnabled = true
	c.MinInstances = 3
	c.MaxInstances = 3

	if err := c.Validate(); err == nil {
		t.Error("expected error when min_instances == max_instances")
	}
}

func TestDeploymentConfig_Validate_AutoScaling_MaxExceedsLimit(t *testing.T) {
	c := NewDeploymentConfig(uuid.New(), "https://github.com/o/r", EnvProduction)
	c.AutoScalingEnabled = true
	c.MinInstances = 1
	c.MaxInstances = 51

	if err := c.Validate(); err == nil {
		t.Error("expected error when max_instances > 50")
	}
}

func TestDeploymentConfig_Validate_AutoScaling_Valid(t *testing.T) {
	c := NewDeploymentConfig(uuid.New(), "https://github.com/o/r", EnvProduction)
	c.AutoScalingEnabled = true
	c.MinInstances = 2
	c.MaxInstances = 10

	if err := c.Validate(); err != nil {
		t.Errorf("expected valid autoscaling config, got: %v", err)
	}
}
