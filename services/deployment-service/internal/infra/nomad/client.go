package nomad

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"sort"
	"time"
)

type Client struct {
	baseURL    string
	httpClient *http.Client
}

func NewClient(nomadURL string) *Client {
	return &Client{
		baseURL: nomadURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

func (c *Client) SubmitJob(ctx context.Context, jobHCL string) (string, error) {
	parseBody, _ := json.Marshal(map[string]any{
		"JobHCL":       jobHCL,
		"Canonicalize": true,
	})
	parseResp, err := c.do(ctx, http.MethodPost, "/v1/jobs/parse", parseBody)
	if err != nil {
		return "", fmt.Errorf("parse job HCL: %w", err)
	}

	var jobJSON map[string]any
	if err := json.Unmarshal(parseResp, &jobJSON); err != nil {
		return "", fmt.Errorf("decode parsed job: %w", err)
	}

	jobID, _ := jobJSON["ID"].(string)

	submitBody, _ := json.Marshal(map[string]any{"Job": jobJSON})
	if _, err := c.do(ctx, http.MethodPost, "/v1/jobs", submitBody); err != nil {
		return "", fmt.Errorf("register job %q: %w", jobID, err)
	}

	return jobID, nil
}

func (c *Client) WaitForCompletion(ctx context.Context, jobID string) error {
	const pollInterval = 10 * time.Second

	for {
		select {
		case <-ctx.Done():
			return fmt.Errorf("timeout waiting for job %q: %w", jobID, ctx.Err())
		case <-time.After(pollInterval):
		}

		allocs, err := c.getAllocations(ctx, jobID)
		if err != nil {
			continue
		}
		if len(allocs) == 0 {
			continue
		}

		latest := allocs[0]
		clientStatus, _ := latest["ClientStatus"].(string)

		switch clientStatus {
		case "complete":
			taskStates, _ := latest["TaskStates"].(map[string]any)
			for _, ts := range taskStates {
				state, _ := ts.(map[string]any)
				events, _ := state["Events"].([]any)
				if len(events) > 0 {
					last, _ := events[len(events)-1].(map[string]any)
					exitCode, _ := last["ExitCode"].(float64)
					if exitCode != 0 {
						return fmt.Errorf("job %q failed with exit code %d", jobID, int(exitCode))
					}
				}
			}
			return nil
		case "failed":
			return fmt.Errorf("job %q allocation failed", jobID)
		}
	}
}

func (c *Client) StopJob(ctx context.Context, jobID string, purge bool) error {
	path := fmt.Sprintf("/v1/job/%s?purge=%v", jobID, purge)
	resp, err := c.doRaw(ctx, http.MethodDelete, path, nil)
	if err != nil {
		return fmt.Errorf("stop job %q: %w", jobID, err)
	}
	if resp.StatusCode == http.StatusNotFound {
		return nil
	}
	if resp.StatusCode >= 400 {
		return fmt.Errorf("stop job %q: status %d", jobID, resp.StatusCode)
	}
	return nil
}

func (c *Client) GetLogs(ctx context.Context, jobID, taskName string, tail int) (string, error) {
	allocs, err := c.getAllocations(ctx, jobID)
	if err != nil || len(allocs) == 0 {
		return "", fmt.Errorf("no allocations for job %q", jobID)
	}

	allocID, _ := allocs[0]["ID"].(string)
	path := fmt.Sprintf("/v1/client/fs/logs/%s?task=%s&type=stdout&plain=true&origin=end&offset=%d",
		allocID, taskName, tail*1000)

	data, err := c.do(ctx, http.MethodGet, path, nil)
	if err != nil {
		return "", err
	}
	return string(data), nil
}

func (c *Client) getAllocations(ctx context.Context, jobID string) ([]map[string]any, error) {
	data, err := c.do(ctx, http.MethodGet, fmt.Sprintf("/v1/job/%s/allocations", jobID), nil)
	if err != nil {
		return nil, err
	}
	var allocs []map[string]any
	if err := json.Unmarshal(data, &allocs); err != nil {
		return nil, err
	}
	sort.Slice(allocs, func(i, j int) bool {
		ti, _ := allocs[i]["CreateTime"].(float64)
		tj, _ := allocs[j]["CreateTime"].(float64)
		return ti > tj
	})
	return allocs, nil
}

func (c *Client) do(ctx context.Context, method, path string, body []byte) ([]byte, error) {
	resp, err := c.doRaw(ctx, method, path, body)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var buf bytes.Buffer
	buf.ReadFrom(resp.Body)

	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("nomad %s %s: status %d: %s", method, path, resp.StatusCode, buf.String())
	}
	return buf.Bytes(), nil
}

func (c *Client) doRaw(ctx context.Context, method, path string, body []byte) (*http.Response, error) {
	req, err := http.NewRequestWithContext(ctx, method, c.baseURL+path, bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	return c.httpClient.Do(req)
}
