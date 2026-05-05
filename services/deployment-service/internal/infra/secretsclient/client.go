package secretsclient

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"deployment-service/internal/app/port"

	"github.com/google/uuid"
)

type Client struct {
	baseURL    string
	httpClient *http.Client
}

func NewClient(baseURL string) *Client {
	return &Client{
		baseURL:    baseURL,
		httpClient: &http.Client{Timeout: 10 * time.Second},
	}
}

func (c *Client) FetchForProject(ctx context.Context, projectID uuid.UUID) ([]port.SecretRef, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet,
		fmt.Sprintf("%s/api/v1/secrets/project/%s", c.baseURL, projectID), nil)
	if err != nil {
		return nil, fmt.Errorf("build request: %w", err)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("fetch secrets: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, nil
	}
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("secrets-service returned %d", resp.StatusCode)
	}

	var items []struct {
		Key       string `json:"key"`
		VaultPath string `json:"vault_path"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&items); err != nil {
		return nil, fmt.Errorf("decode response: %w", err)
	}

	refs := make([]port.SecretRef, len(items))
	for i, item := range items {
		refs[i] = port.SecretRef{Key: item.Key, VaultPath: item.VaultPath}
	}
	return refs, nil
}
