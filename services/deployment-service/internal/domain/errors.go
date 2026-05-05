package domain

import "fmt"

type ErrInvalidTransition struct {
	From DeploymentStatus
	To   DeploymentStatus
}

func (e ErrInvalidTransition) Error() string {
	return fmt.Sprintf("invalid transition: %s -> %s", e.From, e.To)
}

var (
	ErrDeploymentNotFound  = fmt.Errorf("deployment not found")
	ErrConfigNotFound      = fmt.Errorf("deployment config not found")
	ErrConfigAlreadyExists = fmt.Errorf("deployment config already exists for this project and environment")
	ErrNotRunning          = fmt.Errorf("deployment is not in running state")
)
