package handler

import (
	"encoding/json"
	"errors"
	"net/http"
	"strconv"

	"deployment-service/internal/app/usecase/command"
	"deployment-service/internal/app/usecase/query"
	"deployment-service/internal/domain"
	"deployment-service/internal/transport/http/dto"
	"deployment-service/internal/transport/http/middleware"

	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"
)

type Deployment struct {
	deploy          *command.DeployCommand
	createConfig    *command.CreateConfigCommand
	stop            *command.StopCommand
	retry           *command.RetryCommand
	getDeployment   *query.GetDeployment
	listDeployments *query.ListDeployments
	getLogs         *query.GetLogs
}

func NewDeployment(
	deploy *command.DeployCommand,
	createConfig *command.CreateConfigCommand,
	stop *command.StopCommand,
	retry *command.RetryCommand,
	getDeployment *query.GetDeployment,
	listDeployments *query.ListDeployments,
	getLogs *query.GetLogs,
) *Deployment {
	return &Deployment{
		deploy:          deploy,
		createConfig:    createConfig,
		stop:            stop,
		retry:           retry,
		getDeployment:   getDeployment,
		listDeployments: listDeployments,
		getLogs:         getLogs,
	}
}

func (h *Deployment) Routes(r chi.Router) {
	r.Route("/api/v1/deployments", func(r chi.Router) {
		r.Post("/configs", h.createDeploymentConfig)
		r.Get("/project/{projectID}", h.listProjectDeployments)
		r.Post("/project/{projectID}/retry", h.retryDeployment)
		r.Get("/{deploymentID}", h.getDeploymentByID)
		r.Post("/{deploymentID}/stop", h.stopDeployment)
		r.Get("/{deploymentID}/logs", h.getDeploymentLogs)
	})
}

func (h *Deployment) createDeploymentConfig(w http.ResponseWriter, r *http.Request) {
	token, ok := requireBearer(w, r)
	if !ok {
		return
	}
	var req struct {
		ProjectID          uuid.UUID `json:"project_id"`
		GitHubRepoURL      string    `json:"github_repo_url"`
		Environment        string    `json:"environment"`
		InstanceCount      int       `json:"instance_count"`
		CPULimit           float64   `json:"cpu_limit"`
		MemoryLimit        int       `json:"memory_limit"`
		AutoScalingEnabled bool      `json:"auto_scaling_enabled"`
		MinInstances       int       `json:"min_instances"`
		MaxInstances       int       `json:"max_instances"`
		Port               int       `json:"port"`
		HealthCheckPath    string    `json:"health_check_path"`
		DockerfilePath     string    `json:"dockerfile_path"`
		DockerBuildContext string    `json:"docker_build_context"`
	}
	if !decode(w, r, &req) {
		return
	}
	if req.ProjectID == uuid.Nil {
		http.Error(w, "project_id is required", http.StatusBadRequest)
		return
	}
	if req.GitHubRepoURL == "" {
		http.Error(w, "github_repo_url is required", http.StatusBadRequest)
		return
	}

	cfg, err := h.createConfig.Execute(r.Context(), command.CreateConfigInput{
		UserAccessToken:    token,
		ProjectID:          req.ProjectID,
		GitHubRepoURL:      req.GitHubRepoURL,
		Environment:        req.Environment,
		InstanceCount:      req.InstanceCount,
		CPULimit:           req.CPULimit,
		MemoryLimit:        req.MemoryLimit,
		AutoScalingEnabled: req.AutoScalingEnabled,
		MinInstances:       req.MinInstances,
		MaxInstances:       req.MaxInstances,
		Port:               req.Port,
		HealthCheckPath:    req.HealthCheckPath,
		DockerfilePath:     req.DockerfilePath,
		DockerBuildContext: req.DockerBuildContext,
	})
	if err != nil {
		writeErr(w, err)
		return
	}
	writeJSON(w, http.StatusCreated, dto.FromConfig(cfg))
}

func (h *Deployment) listProjectDeployments(w http.ResponseWriter, r *http.Request) {
	if _, ok := requireBearer(w, r); !ok {
		return
	}
	projectID := parseUUID(w, r, "projectID")
	if projectID == uuid.Nil {
		return
	}
	deps, err := h.listDeployments.Execute(r.Context(), projectID)
	if err != nil {
		writeErr(w, err)
		return
	}
	writeJSON(w, http.StatusOK, dto.FromDeployments(deps))
}

func (h *Deployment) getDeploymentByID(w http.ResponseWriter, r *http.Request) {
	if _, ok := requireBearer(w, r); !ok {
		return
	}
	id := parseUUID(w, r, "deploymentID")
	if id == uuid.Nil {
		return
	}
	d, err := h.getDeployment.Execute(r.Context(), id)
	if err != nil {
		writeErr(w, err)
		return
	}
	writeJSON(w, http.StatusOK, dto.FromDeployment(d))
}

func (h *Deployment) stopDeployment(w http.ResponseWriter, r *http.Request) {
	if _, ok := requireBearer(w, r); !ok {
		return
	}
	id := parseUUID(w, r, "deploymentID")
	if id == uuid.Nil {
		return
	}
	if err := h.stop.Execute(r.Context(), id); err != nil {
		writeErr(w, err)
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func (h *Deployment) retryDeployment(w http.ResponseWriter, r *http.Request) {
	token, ok := requireBearer(w, r)
	if !ok {
		return
	}
	projectID := parseUUID(w, r, "projectID")
	if projectID == uuid.Nil {
		return
	}
	var req struct {
		ProjectName  string `json:"project_name"`
		StartCommand string `json:"start_command"`
	}
	if !decode(w, r, &req) {
		return
	}
	if req.ProjectName == "" {
		http.Error(w, "project_name is required", http.StatusBadRequest)
		return
	}
	d, err := h.retry.Execute(r.Context(), command.RetryInput{
		ProjectID:       projectID,
		ProjectName:     req.ProjectName,
		UserAccessToken: token,
		StartCommand:    req.StartCommand,
		CorrelationID:   middleware.FromContext(r.Context()),
	})
	if err != nil {
		writeErr(w, err)
		return
	}
	writeJSON(w, http.StatusCreated, dto.FromDeployment(d))
}

func (h *Deployment) getDeploymentLogs(w http.ResponseWriter, r *http.Request) {
	if _, ok := requireBearer(w, r); !ok {
		return
	}
	id := parseUUID(w, r, "deploymentID")
	if id == uuid.Nil {
		return
	}
	tail := 100
	if t := r.URL.Query().Get("tail"); t != "" {
		if n, err := strconv.Atoi(t); err == nil && n > 0 {
			tail = n
		}
	}
	logs, err := h.getLogs.Execute(r.Context(), id, tail)
	if err != nil {
		writeErr(w, err)
		return
	}
	writeJSON(w, http.StatusOK, dto.LogsResponse{Logs: logs})
}

func requireBearer(w http.ResponseWriter, r *http.Request) (string, bool) {
	auth := r.Header.Get("Authorization")
	if len(auth) > 7 && auth[:7] == "Bearer " {
		return auth[7:], true
	}
	http.Error(w, "missing or invalid Authorization header", http.StatusUnauthorized)
	return "", false
}

func decode(w http.ResponseWriter, r *http.Request, v any) bool {
	if err := json.NewDecoder(r.Body).Decode(v); err != nil {
		http.Error(w, "invalid request body: "+err.Error(), http.StatusBadRequest)
		return false
	}
	return true
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(v) //nolint:errcheck
}

func writeErr(w http.ResponseWriter, err error) {
	switch {
	case errors.Is(err, domain.ErrDeploymentNotFound),
		errors.Is(err, domain.ErrConfigNotFound):
		http.Error(w, err.Error(), http.StatusNotFound)
	case errors.Is(err, domain.ErrConfigAlreadyExists),
		errors.Is(err, domain.ErrNotRunning):
		http.Error(w, err.Error(), http.StatusConflict)
	default:
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

func parseUUID(w http.ResponseWriter, r *http.Request, param string) uuid.UUID {
	raw := chi.URLParam(r, param)
	id, err := uuid.Parse(raw)
	if err != nil {
		http.Error(w, "invalid "+param+": "+raw, http.StatusBadRequest)
		return uuid.Nil
	}
	return id
}
