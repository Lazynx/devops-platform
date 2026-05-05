package port

import "context"

type NomadClient interface {
	SubmitJob(ctx context.Context, jobHCL string) (jobID string, err error)
	WaitForCompletion(ctx context.Context, jobID string) error
	StopJob(ctx context.Context, jobID string, purge bool) error
	GetLogs(ctx context.Context, jobID, taskName string, tail int) (string, error)
}
