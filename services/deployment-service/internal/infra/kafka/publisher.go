package kafka

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/twmb/franz-go/pkg/kgo"
)

type Publisher struct {
	client *kgo.Client
}

func NewPublisher(client *kgo.Client) *Publisher {
	return &Publisher{client: client}
}

func (p *Publisher) PublishBuilding(ctx context.Context, deploymentID, projectID uuid.UUID) error {
	return p.publish(ctx, "deployment.building", map[string]any{
		"deployment_id": deploymentID.String(),
		"project_id":    projectID.String(),
	})
}

func (p *Publisher) PublishDeploying(ctx context.Context, deploymentID, projectID uuid.UUID) error {
	return p.publish(ctx, "deployment.deploying", map[string]any{
		"deployment_id": deploymentID.String(),
		"project_id":    projectID.String(),
	})
}

func (p *Publisher) PublishRunning(ctx context.Context, deploymentID, projectID uuid.UUID, imageURL, deploymentURL string) error {
	return p.publish(ctx, "deployment.running", map[string]any{
		"deployment_id":  deploymentID.String(),
		"project_id":     projectID.String(),
		"image_url":      imageURL,
		"deployment_url": deploymentURL,
	})
}

func (p *Publisher) PublishFailed(ctx context.Context, deploymentID, projectID uuid.UUID, reason string) error {
	return p.publish(ctx, "deployment.failed", map[string]any{
		"deployment_id": deploymentID.String(),
		"project_id":    projectID.String(),
		"error_message": reason,
	})
}

func (p *Publisher) publish(ctx context.Context, topic string, payload map[string]any) error {
	payload["timestamp"] = time.Now().UTC().Format(time.RFC3339)

	data, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("marshal event %q: %w", topic, err)
	}

	results := p.client.ProduceSync(ctx, &kgo.Record{
		Topic: topic,
		Value: data,
	})
	if err := results.FirstErr(); err != nil {
		return fmt.Errorf("publish %q: %w", topic, err)
	}
	return nil
}
