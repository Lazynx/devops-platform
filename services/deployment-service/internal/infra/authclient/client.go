package authclient

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

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

func (c *Client) GetGitHubToken(ctx context.Context, userAccessToken string) (string, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.baseURL+"/api/v1/auth/github-token", nil)
	if err != nil {
		return "", err
	}
	req.Header.Set("Authorization", "Bearer "+userAccessToken)

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return "", fmt.Errorf("get github token: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("auth-service returned %d", resp.StatusCode)
	}

	var body struct {
		GithubToken string `json:"github_token"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
		return "", fmt.Errorf("decode github token response: %w", err)
	}
	return body.GithubToken, nil
}

func (c *Client) VerifyProjectAccess(ctx context.Context, userAccessToken string, projectID uuid.UUID) error {
	req, err := http.NewRequestWithContext(ctx,
		http.MethodGet,
		fmt.Sprintf("%s/api/v1/auth/verify-project/%s", c.baseURL, projectID),
		nil,
	)
	if err != nil {
		return err
	}
	req.Header.Set("Authorization", "Bearer "+userAccessToken)

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("verify project access: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusForbidden || resp.StatusCode == http.StatusUnauthorized {
		return fmt.Errorf("access denied to project %s", projectID)
	}
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("auth-service returned %d", resp.StatusCode)
	}
	return nil
}
