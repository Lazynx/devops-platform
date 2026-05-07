# DevOps Platform

A self-hosted application deployment platform — point it at any GitHub repository and it builds, containerises, and deploys the app to your own infrastructure. Built to demonstrate production-grade microservices, event-driven architecture, and infrastructure-as-code.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       Traefik (API Gateway)                      │
│            Host-based routing via Consul service catalog         │
└──────┬───────────────┬─────────────┬──────────────┬──────────────┘
       │               │             │              │
 ┌─────▼──────┐ ┌──────▼─────┐ ┌─────▼──────┐ ┌─────▼──────────┐
 │auth-service│ │project-svc │ │secrets-svc │ │deployment-svc  │
 │  Python    │ │  Python    │ │  Python    │ │      Go        │
 │  :8000     │ │  :8001     │ │  :8003     │ │  :8005         │
 └─────┬──────┘ └──────┬─────┘ └─────┬──────┘ └───────┬────────┘
       │               │             │                │
       └───────────────┴─────────────┴────────────────┘
                               │
               ┌───────────────▼───────────────┐
               │  Apache Kafka (KRaft + SASL)  │
               └───────────────┬───────────────┘
                               │
          ┌────────────────────┼─────────────────┐
          │                    │                 │
   ┌──────▼──────┐    ┌────────▼───────┐  ┌──────▼──────┐
   │  PostgreSQL │    │ Nomad+Consul   │  │   Vault     │
   │  (per svc)  │    │ (orchestrator) │  │  (secrets)  │
   └─────────────┘    └────────────────┘  └─────────────┘
```

### End-to-end deployment flow

```
User  ──POST /projects──▶  project-service
                                │
                        project.created (Kafka)
                                │
                         secrets-service  ◀── stores in Vault
                                │
                        secrets.bulk_created (Kafka)
                                │
                         deployment-service (Go)
                           ├── Submit build job ──▶ Nomad
                           │     └── Docker build + push to Nexus
                           └── Submit deploy job ──▶ Nomad
                                 └── Container running, Consul registered
                                       │
                                 Traefik picks up route
                                       │
                              App live at {project}.localhost:8090
```

---

## Services

| Service | Language | Port | Responsibility |
|---|---|---|---|
| `auth-service` | Python / FastAPI | 8000 | GitHub OAuth, JWT issue/refresh, session management (Redis) |
| `project-service` | Python / FastAPI | 8001 | Project CRUD, repository framework detection, status aggregation |
| `secrets-service` | Python / FastAPI | 8003 | Secret CRUD, Vault KV storage, bulk provisioning |
| `deployment-service` | **Go** / net/http | 8005 | Build pipeline, Nomad job orchestration, log streaming |

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| API gateway | Traefik | Consul catalog integration, zero-config routing |
| Message broker | Kafka (KRaft, SASL/PLAIN) | At-least-once delivery, replay via DLQ topics |
| Orchestrator | HashiCorp Nomad | Simpler than k8s, first-class Vault/Consul integration |
| Service mesh | HashiCorp Consul | DNS-based discovery, health checks |
| Secrets | HashiCorp Vault | KV v2, per-project policies, Nomad workload identity |
| Container registry | Sonatype Nexus | Self-hosted Docker registry |
| Database | PostgreSQL 16 | One database per service (schema isolation) |
| Cache / sessions | Redis 7 | JWT blocklist, session store |
| Observability | Prometheus + Alertmanager + OpenSearch + Logstash | Metrics + structured logs |
| Go Kafka client | franz-go | Manual offset commit, DLQ on failure |
| Python DI | Dishka | Async IoC container for FastAPI |
| Python messaging | FastStream | Kafka consumer/producer DSL |

---

## Project Layout

```
devops-platform/
├── services/
│   ├── auth-service/           # Python, FastAPI, SQLAlchemy ORM, Alembic
│   ├── project-service/        # Python, FastAPI, CQRS via interactors
│   ├── secrets-service/        # Python, FastAPI, hvac (Vault), asyncio.to_thread
│   └── deployment-service/     # Go, Clean Architecture (see below)
├── infra/
│   ├── nomad-stack/
│   │   └── jobs/               # HCL job files; variable "project_root" in every file
│   ├── monitoring/             # Prometheus rules, Alertmanager config
│   ├── start_infra.sh          # Vault unseal + daemon bootstrap
│   └── stop_infra.sh
├── docker-compose.dev.yml      # Postgres, Redis, Kafka, OpenSearch, Nexus
├── docker-compose.prod.yml     # Production-hardened compose
├── .lima/devops-platform.yaml  # ARM64 Ubuntu VM for Mac M4
├── Makefile
└── .github/workflows/ci.yml   # Lint → test → nomad validate → docker build
```

### Go deployment-service — Clean Architecture

```
deployment-service/
├── cmd/api/main.go
└── internal/
    ├── domain/              # Deployment, DeploymentConfig, Status, domain errors
    ├── app/
    │   ├── port/            # Interfaces: Repository, NomadClient, Publisher, AuthService, SecretsFetcher
    │   └── usecase/
    │       ├── command/     # DeployCommand, RetryCommand, StopCommand, CreateConfigCommand
    │       └── query/       # GetDeployment, ListDeployments, GetLogs
    ├── infra/
    │   ├── nomad/           # NomadClient (HTTP), JobBuilder (text/template HCL)
    │   ├── postgres/        # pgx/v5 repositories, raw SQL
    │   ├── kafka/           # franz-go publisher
    │   ├── authclient/      # HTTP → auth-service (token validation)
    │   └── secretsclient/   # HTTP → secrets-service (fetch env vars for retry)
    ├── metrics/             # Prometheus: deployments_total, deployment_duration_seconds, active_deployments
    └── transport/
        ├── http/            # chi router, typed DTOs, correlation-id middleware
        └── kafka/           # Consumer: manual commit, DLQ on error, graceful shutdown
```

**Key design decisions:**

- **No ORM in Go** — raw SQL via `pgx/v5` for full query control
- **App-lifecycle context** — background goroutines use the app `context.Context` passed from `main`, not `context.Background()`; they stop on SIGTERM
- **DLQ** — failed Kafka events published to `deployment-service.dlq` via a dedicated producer client (separate from the consumer)
- **Retry with fresh secrets** — `RetryCommand` calls `secrets-service` before re-deploying so env vars are always current
- **DB-level uniqueness** — `UNIQUE (project_id, environment)` on `deployment_configs` prevents race conditions
- **Typed HTTP responses** — all handlers return `dto.DeploymentResponse` / `dto.ConfigResponse`; domain internals never leak to the API

---

## Quick Start

### Prerequisites

- Docker + Docker Compose
- Go 1.23+, Python 3.12+, [uv](https://docs.astral.sh/uv/)
- Nomad, Consul, Vault (or use the Lima VM)

### 1. Stateful services

```bash
docker compose -f docker-compose.dev.yml up -d
```

### 2. Infrastructure (Nomad / Consul / Vault)

```bash
cp infra/kafka_server_jaas.conf.example infra/kafka_server_jaas.conf
# fill in KAFKA_USERNAME / KAFKA_PASSWORD

export VAULT_UNSEAL_KEY=<your-key>
./infra/start_infra.sh
```

### 3. Services

```bash
# All at once
make dev

# Individually
cd services/auth-service       && uv run uvicorn auth_service.app:app --port 8000 --reload
cd services/project-service    && uv run uvicorn project_service.app:app --port 8001 --reload
cd services/secrets-service    && uv run uvicorn secrets_service.app:app --port 8003 --reload
cd services/deployment-service && go run ./cmd/api/
```

### Mac ARM chip — Lima VM

```bash
limactl start .lima/devops-platform.yaml
limactl shell devops-platform
```

Provisions Docker, Nomad, Consul, Vault, and `uv` on first boot.

---

## API Reference

### Auth — `http://localhost:8000`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/auth/github` | Get GitHub OAuth redirect URL |
| `GET` | `/api/v1/auth/github/callback` | OAuth callback; sets `refresh_token` HttpOnly cookie |
| `POST` | `/api/v1/auth/refresh` | Refresh access token from cookie |
| `POST` | `/api/v1/auth/logout` | Invalidate session |
| `GET` | `/api/v1/auth/me` | Current user |
| `GET` | `/api/v1/auth/oauth/github/token` | Retrieve stored GitHub token |
| `GET` | `/metrics` | Prometheus metrics |

### Projects — `http://localhost:8001`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/projects/` | List user projects |
| `POST` | `/api/v1/projects/` | Create project → triggers full deploy flow |
| `GET` | `/api/v1/projects/{id}/status` | Aggregated status (secrets + deployment) |
| `GET` | `/api/v1/projects/{id}/status/poll` | Long-poll for status change |
| `DELETE` | `/api/v1/projects/{id}` | Delete project; emits `project.deleted` |

### Secrets — `http://localhost:8003`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/secrets` | Create single secret |
| `POST` | `/api/v1/secrets/bulk` | Bulk create → triggers deployment |
| `GET` | `/api/v1/secrets/project/{id}` | List project secrets |
| `PUT` | `/api/v1/secrets/{id}` | Update secret value |
| `DELETE` | `/api/v1/secrets/{id}` | Delete secret |

### Deployments — `http://localhost:8005`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/deployments/configs` | Create deployment config |
| `GET` | `/api/v1/deployments/project/{id}` | List project deployments |
| `POST` | `/api/v1/deployments/project/{id}/retry` | Retry last deployment |
| `GET` | `/api/v1/deployments/{id}` | Get deployment |
| `POST` | `/api/v1/deployments/{id}/stop` | Stop running deployment |
| `GET` | `/api/v1/deployments/{id}/logs` | Stream logs (`?tail=N`) |
| `GET` | `/metrics` | Prometheus metrics |

---

## Kafka Topics

| Topic | Producer | Consumer | Purpose |
|---|---|---|---|
| `project.created` | project-service | — | Informational: project created without secrets |
| `project.created_with_secrets` | project-service | secrets-service | Trigger secret provisioning + deployment config |
| `project.deleted` | project-service | deployment-service, secrets-service | Cascade delete |
| `secrets.bulk_created` | secrets-service | deployment-service | Trigger build + deploy |
| `secrets.failed` | secrets-service | project-service | Propagate secret provisioning failure |
| `deployment.config_created` | deployment-service | project-service | Config stored, optionally trigger deploy |
| `deployment.config_failed` | deployment-service | project-service | Propagate config creation failure |
| `deployment.building` | deployment-service | project-service | Update project deployment status |
| `deployment.deploying` | deployment-service | project-service | Update project deployment status |
| `deployment.running` | deployment-service | project-service | Update project status + deployment URL |
| `deployment.failed` | deployment-service | project-service | Update project status + error message |
| `service-logs` | all services | logstash | Centralised structured logging |
| `*.dlq` | each service | — | Dead-letter queue for failed events |

---

## Observability

| Tool | URL | Purpose |
|---|---|---|
| Prometheus | `http://localhost:9090` | Metrics scraping & querying |
| Alertmanager | `http://localhost:9097` | Alert routing |
| OpenSearch Dashboards | `http://localhost:5601` | Log search and visualisation |
| Traefik dashboard | `http://localhost:8080` | Live routing overview |
| Nomad UI | `http://localhost:4646` | Job and allocation status |
| Consul UI | `http://localhost:8500` | Service registry and health |
| Vault UI | `http://localhost:8200` | Secrets management |
| Nexus | `http://localhost:8081` | Docker registry UI |

Custom business metrics (deployment-service):

```
deployments_total{status, environment}
deployment_duration_seconds{phase}   # build / deploy
active_deployments{environment}
```

---

## CI Pipeline

Every push and pull request runs:

```
lint-auth-service   ──┐
lint-project-service──┼──▶ test-auth-service (Postgres + Redis containers)
lint-secrets-service──┘
                         validate-nomad-jobs (nomad job validate -var project_root=...)
                         build-deployment-service-go (go build + go vet + go test -race)
                         build-docker-images (PR only, matrix: auth / project / secrets)
```

> Note: the Go deployment-service Docker image is only built during CD (not in CI lint/test jobs).


---

 ## CD Pipeline
                                                                                                                                                                                                                                   
On every successful CI run on `main`, images are built and pushed to GitHub Container Registry (GHCR):                                                                                                                           
                                                                                                                                                                                                                                   
CI (success on main)                                                                                                                                                                                                             
   │                                                 
   ▼                                                                                                                                                                                                                        
publish-images (matrix: auth / project / secrets / deployment)
   │                                                                                                                                                                                                                        
   ├── docker buildx build
   └── ghcr.io/lazynx/devops-platform-{service}:latest                                                                                                                                                                      
       ghcr.io/lazynx/devops-platform-{service}:{git-sha}                                                                                                                                                                   
                                                                                                                                                                                                                            
| Image | Registry path |                                                                                                                                                                                                        
|---|---|                                                                                                                                                                                                                        
| `auth-service` | `ghcr.io/lazynx/devops-platform-auth-service` |
| `project-service` | `ghcr.io/lazynx/devops-platform-project-service` |                                                                                                                                                         
| `secrets-service` | `ghcr.io/lazynx/devops-platform-secrets-service` |
| `deployment-service` | `ghcr.io/lazynx/devops-platform-deployment-service` |                                                                                                                                                   
                                                     
Tags pushed per release: `:latest` and `:<commit-sha>` for pinned rollbacks.         

---

## Environment Variables

| Variable | Service | Description |
|---|---|---|
| `JWT_SECRET_KEY` | auth | JWT signing secret |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | auth | GitHub OAuth app |
| `VAULT_ADDR` / `VAULT_TOKEN` | secrets | Vault connection |
| `KAFKA_USERNAME` / `KAFKA_PASSWORD` | all | SASL credentials |
| `KAFKA_BOOTSTRAP_SERVERS` | all | Kafka broker addresses |
| `NOMAD_URL` | deployment | Nomad API endpoint |
| `NEXUS_REGISTRY_URL` | deployment | Docker registry |
| `AUTH_SERVICE_URL` | deployment | auth-service base URL |
| `SECRETS_SERVICE_URL` | deployment | secrets-service base URL |
