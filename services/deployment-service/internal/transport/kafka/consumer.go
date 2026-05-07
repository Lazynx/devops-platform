package kafka

import (
	"context"
	"encoding/json"
	"log/slog"
	"time"

	"deployment-service/internal/app/port"
	"deployment-service/internal/app/usecase/command"

	"github.com/google/uuid"
	"github.com/twmb/franz-go/pkg/kgo"
)

const dlqTopic = "deployment-service.dlq"

type Consumer struct {
	client        *kgo.Client
	producer      *kgo.Client
	deploy        *command.DeployCommand
	deleteProject *command.DeleteProjectCommand
}

func NewConsumer(
	client *kgo.Client,
	producer *kgo.Client,
	deploy *command.DeployCommand,
	deleteProject *command.DeleteProjectCommand,
) *Consumer {
	return &Consumer{
		client:        client,
		producer:      producer,
		deploy:        deploy,
		deleteProject: deleteProject,
	}
}

func (c *Consumer) Run(ctx context.Context) error {
	slog.Info("kafka consumer starting")
	for {
		fetches := c.client.PollFetches(ctx)
		if fetches.IsClientClosed() || ctx.Err() != nil {
			return ctx.Err()
		}

		fetches.EachError(func(topic string, partition int32, err error) {
			slog.Error("kafka fetch error", "topic", topic, "partition", partition, "err", err)
		})

		var toCommit []*kgo.Record

		fetches.EachRecord(func(rec *kgo.Record) {
			if err := c.dispatch(ctx, rec); err != nil {
				slog.Error("failed to handle kafka event",
					"topic", rec.Topic,
					"offset", rec.Offset,
					"err", err,
				)
				c.publishDLQ(ctx, rec, err)
				return
			}
			toCommit = append(toCommit, rec)
		})

		if len(toCommit) > 0 {
			if err := c.client.CommitRecords(ctx, toCommit...); err != nil {
				slog.Error("failed to commit kafka offsets", "err", err)
			}
		}
	}
}

func (c *Consumer) dispatch(ctx context.Context, rec *kgo.Record) error {
	switch rec.Topic {
	case "secrets.bulk_created":
		return c.handleSecretsBulkCreated(ctx, rec.Value)
	case "project.deleted":
		return c.handleProjectDeleted(ctx, rec.Value)
	default:
		slog.Warn("unhandled kafka topic", "topic", rec.Topic)
		return nil
	}
}

func (c *Consumer) publishDLQ(ctx context.Context, rec *kgo.Record, err error) {
	payload, _ := json.Marshal(map[string]any{
		"topic":    rec.Topic,
		"offset":   rec.Offset,
		"payload":  string(rec.Value),
		"error":    err.Error(),
		"failed_at": time.Now().UTC().Format(time.RFC3339),
	})
	if err := c.producer.ProduceSync(ctx, &kgo.Record{
		Topic: dlqTopic,
		Value: payload,
	}).FirstErr(); err != nil {
		slog.Error("failed to publish to DLQ", "topic", rec.Topic, "offset", rec.Offset, "err", err)
	}
}

type secretsBulkCreatedEvent struct {
	ProjectID     string `json:"project_id"`
	Name          string `json:"name"`
	GitHubRepoURL string `json:"github_repo_url"`
	GitHubToken   string `json:"github_token"`
	StartCommand  string `json:"start_command"`
	Secrets       []struct {
		Key       string `json:"key"`
		VaultPath string `json:"vault_path"`
	} `json:"secrets"`
	DeploymentConfig *struct {
		Environment        string  `json:"environment"`
		InstanceCount      int     `json:"instance_count"`
		CPULimit           float64 `json:"cpu_limit"`
		MemoryLimit        int     `json:"memory_limit"`
		Port               int     `json:"port"`
		HealthCheckPath    string  `json:"health_check_path"`
		DockerfilePath     string  `json:"dockerfile_path"`
		DockerBuildContext string  `json:"docker_build_context"`
	} `json:"deployment_config"`
	AutoDeploy    bool   `json:"auto_deploy"`
	CorrelationID string `json:"correlation_id"`
}

func (c *Consumer) handleSecretsBulkCreated(ctx context.Context, data []byte) error {
	var ev secretsBulkCreatedEvent
	if err := json.Unmarshal(data, &ev); err != nil {
		return err
	}
	projectID, err := uuid.Parse(ev.ProjectID)
	if err != nil {
		return err
	}

	secrets := make([]port.SecretRef, len(ev.Secrets))
	for i, s := range ev.Secrets {
		secrets[i] = port.SecretRef{Key: s.Key, VaultPath: s.VaultPath}
	}

	in := command.SecretsBulkCreatedInput{
		ProjectID:     projectID,
		ProjectName:   ev.Name,
		GitHubRepoURL: ev.GitHubRepoURL,
		GitHubToken:   ev.GitHubToken,
		StartCommand:  ev.StartCommand,
		Secrets:       secrets,
		CorrelationID: ev.CorrelationID,
	}
	if ev.DeploymentConfig != nil {
		in.DeploymentConfig = &command.DeploymentConfigInput{
			Environment:        ev.DeploymentConfig.Environment,
			InstanceCount:      ev.DeploymentConfig.InstanceCount,
			CPULimit:           ev.DeploymentConfig.CPULimit,
			MemoryLimit:        ev.DeploymentConfig.MemoryLimit,
			Port:               ev.DeploymentConfig.Port,
			HealthCheckPath:    ev.DeploymentConfig.HealthCheckPath,
			DockerfilePath:     ev.DeploymentConfig.DockerfilePath,
			DockerBuildContext: ev.DeploymentConfig.DockerBuildContext,
		}
	}
	return c.deploy.Execute(ctx, in)
}

type projectDeletedEvent struct {
	ProjectID     string `json:"project_id"`
	CorrelationID string `json:"correlation_id"`
}

func (c *Consumer) handleProjectDeleted(ctx context.Context, data []byte) error {
	var ev projectDeletedEvent
	if err := json.Unmarshal(data, &ev); err != nil {
		return err
	}
	projectID, err := uuid.Parse(ev.ProjectID)
	if err != nil {
		return err
	}
	return c.deleteProject.Execute(ctx, command.DeleteProjectInput{
		ProjectID:     projectID,
		CorrelationID: ev.CorrelationID,
	})
}
