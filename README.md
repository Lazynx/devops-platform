# DevOps Platform

A unified self-service platform for automated CI/CD pipelines, environment provisioning, and deployment management. This platform enables developers to deploy containerized applications with automated builds, secret management, and service discovery.

## Project Overview

This platform provides a complete DevOps solution for managing the entire application lifecycle from code to deployment. It combines multiple HashiCorp tools (Nomad, Consul, Vault) with modern observability and artifact management systems to create a production-ready deployment platform.

### Key Features

- **Self-Service Deployments**: Automated build and deployment pipeline triggered via REST API
- **GitHub Integration**: Direct integration with GitHub repositories for source code management
- **Secret Management**: Secure storage and injection of application secrets via HashiCorp Vault
- **Service Discovery**: Automatic service registration and DNS-based discovery with Consul
- **Dynamic Routing**: HTTP routing and load balancing with Traefik
- **Artifact Registry**: Docker image storage and management with Sonatype Nexus
- **Observability**: Centralized logging with OpenSearch, Logstash, and OpenSearch Dashboards
- **Event-Driven Architecture**: Asynchronous service communication via Apache Kafka

## Architecture

### Technology Stack

#### Orchestration and Scheduling
- **Nomad**: Lightweight workload orchestrator for running Docker containers and batch jobs
- **Consul**: Service mesh providing service discovery, health checking, and KV store
- **Vault**: Secrets management with dynamic secret generation and secure storage

#### Networking and Routing
- **Traefik**: Cloud-native API gateway and reverse proxy with automatic service discovery
- **Consul DNS**: DNS-based service discovery (*.service.consul)

#### Data Storage
- **PostgreSQL**: Relational database for platform services (auth, projects, deployments, secrets)
- **Apache Kafka**: Distributed event streaming platform for inter-service communication

#### Artifact Management
- **Sonatype Nexus**: Universal artifact repository serving as Docker registry

#### Observability
- **OpenSearch**: Distributed search and analytics engine for log storage
- **Logstash**: Data processing pipeline for log ingestion and transformation
- **OpenSearch Dashboards**: Visualization and exploration interface for logs and metrics

#### Application Runtime
- **Docker**: Container runtime for application isolation
- **Python 3.12**: Primary programming language for microservices
- **FastAPI**: Modern async web framework for REST APIs
- **FastStream**: Framework for building event-driven microservices

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Client Applications                         │
│                    (Frontend / API Clients)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │    Traefik     │
                    │  API Gateway   │
                    │   Port: 8090   │
                    └────────┬───────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│Auth Service  │    │Project Service│   │Secrets Service│
│  Port: 8000  │    │  Port: 8001  │   │  Port: 8003  │
└──────┬───────┘    └───────┬───────┘   └───────┬───────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │Apache Kafka  │
                    │ Event Bus    │
                    │  Port: 9092  │
                    └──────┬───────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │Deployment Service│
                  │   Port: 8005    │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Nomad Cluster  │
                  │   Port: 4646    │
                  └────────┬─────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   ┌─────────┐      ┌──────────┐      ┌──────────┐
   │  Build  │      │  Deploy  │      │User Apps │
   │   Job   │      │   Job    │      │(Dynamic) │
   └────┬────┘      └────┬─────┘      └────┬─────┘
        │                │                 │
        ▼                ▼                 │
   ┌─────────┐      ┌──────────┐           │
   │  Nexus  │─────▶│  Vault   │           │
   │Registry │      │ Secrets  │           │
   └─────────┘      └──────────┘           │
                                           │
   ┌───────────────────────────────────────┘
   │
   ▼
┌──────────┐         ┌──────────┐
│  Consul  │◄────────│PostgreSQL│
│ Service  │         │Databases │
│Discovery │         │          │
└──────────┘         └──────────┘
```

## Platform Services

### Authentication Service (Port 8000)
Handles user authentication and authorization with GitHub OAuth integration.

**Technologies**: FastAPI, SQLAlchemy, Redis, JWT

**Responsibilities**:
- GitHub OAuth authentication flow
- JWT token generation and validation
- Session management
- User profile management

### Project Service (Port 8001)
Manages project lifecycle and repository analysis.

**Technologies**: FastAPI, SQLAlchemy, GitHub API

**Responsibilities**:
- Project CRUD operations
- GitHub repository analysis and framework detection
- Project configuration management
- Deployment status tracking

### Secrets Service (Port 8003)
Manages application secrets and environment variables.

**Technologies**: FastAPI, HashiCorp Vault, Kafka

**Responsibilities**:
- Secret storage in Vault KV v2
- Per-project Vault policy management
- Bulk secret creation and updates
- Secret encryption and access control

### Deployment Service (Port 8005)
Orchestrates application builds and deployments.

**Technologies**: FastAPI, Nomad API, Docker, Nexus

**Responsibilities**:
- Docker image build job generation
- Application deployment job generation
- Nomad job lifecycle management
- Build artifact management
- Deployment configuration

## Deployment Workflow

1. **Project Creation**
   - User creates project via REST API with GitHub repository URL
   - Project Service analyzes repository structure and detects framework
   - Event published to Kafka: `project.created_with_secrets`

2. **Secret Management**
   - Secrets Service receives event
   - Stores secrets in Vault with project-specific path
   - Creates Vault policy for secure access
   - Event published: `secrets.bulk_created`

3. **Build Phase**
   - Deployment Service receives event
   - Generates Nomad build job with Docker build task
   - Job clones repository, builds Docker image
   - Pushes image to Nexus registry
   - Event published: `deployment.building`

4. **Deploy Phase**
   - Deployment Service generates deployment job
   - Nomad schedules container on available node
   - Vault secrets injected via template mechanism
   - Dynamic port allocation by Nomad
   - Service registered in Consul
   - Event published: `deployment.running`

5. **Service Discovery**
   - Consul registers service with health checks
   - Traefik discovers service via Consul catalog
   - HTTP route created: `{project}-{deployment-id}.localhost:8090`

## Infrastructure Components

### Nomad Configuration
- **Mode**: Single-node development cluster
- **Driver**: Docker with privileged mode enabled
- **Networking**: Dynamic port allocation with bridge networking
- **Integration**: Vault workload identity for secret injection

### Consul Configuration
- **Mode**: Single-node development cluster
- **DNS**: Enabled on `.consul` domain
- **Services**: HTTP API on port 8500, DNS on port 8600
- **Storage**: Raft consensus with persistent data

### Vault Configuration
- **Storage Backend**: Raft integrated storage
- **KV Engine**: Version 2 secrets engine at path `secret/`
- **Policies**: Dynamic per-project policies
- **Integration**: Nomad workload identity authentication

### Traefik Configuration
- **Entry Points**: HTTP on port 8090
- **Providers**: Consul Catalog for automatic service discovery
- **Routing**: Host-based routing rules from Consul tags

### Nexus Configuration
- **HTTP Port**: 8083 (UI)
- **Docker Registry**: 8082
- **Repository**: docker-hosted for image storage

### Kafka Configuration
- **Broker**: Single-node cluster on port 9092
- **Topics**: Auto-created on first publish
- **Consumer Groups**: Configured per service

### PostgreSQL Databases
- **auth_db**: User authentication data
- **project_db**: Project metadata and configurations
- **deployment_db**: Deployment history and configs
- **secrets_db**: Secret metadata (values in Vault)

## Project Structure

```
devops-platform/
├── infra/                          # Infrastructure configuration
│   ├── nomad-stack/
│   │   ├── consul/                 # Consul configuration
│   │   ├── jobs/                   # Nomad job definitions
│   │   │   ├── auth-service.nomad
│   │   │   ├── project-service.nomad
│   │   │   ├── secrets-service.nomad
│   │   │   ├── deployment-service.nomad
│   │   │   ├── traefik.nomad
│   │   │   └── migrations/         # Database migration jobs
│   │   ├── nomad-config.hcl        # Nomad agent configuration
│   │   └── vault-config.hcl        # Vault configuration
│   ├── start_infra.sh              # Start infrastructure services
│   ├── start_jobs.sh               # Deploy platform services
│   ├── stop_infra.sh               # Stop infrastructure
│   └── stop_jobs.sh                # Stop platform services
│
├── services/                       # Microservices
│   ├── auth-service/
│   │   ├── src/auth_service/
│   │   │   ├── application/        # Business logic layer
│   │   │   ├── domain/             # Domain entities
│   │   │   ├── infrastructure/     # External integrations
│   │   │   └── presentation/       # API endpoints
│   │   ├── migrations/             # Alembic migrations
│   │   └── pyproject.toml
│   │
│   ├── project-service/
│   │   └── src/project_service/
│   │       ├── application/
│   │       │   └── interactors/    # Use cases
│   │       ├── domain/
│   │       ├── infrastructure/
│   │       │   ├── messaging/      # Kafka consumers
│   │       │   └── sqlalchemy/     # Database repositories
│   │       └── presentation/
│   │
│   ├── secrets-service/
│   │   └── src/secrets_service/
│   │       ├── infrastructure/
│   │       │   └── vault/          # Vault client
│   │       └── ...
│   │
│   └── deployment-service/
│       └── src/deployment_service/
│           ├── infrastructure/
│           │   └── nomad/          # Job generators
│           └── ...
│
└── README.md
```

## API Endpoints

### Authentication Service
- `POST /api/v1/auth/github` - Initiate GitHub OAuth flow
- `GET /api/v1/auth/github/callback` - OAuth callback handler
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/system/health` - Health check

### Project Service
- `POST /api/v1/projects` - Create new project
- `GET /api/v1/projects` - List user projects
- `GET /api/v1/projects/{id}` - Get project details
- `DELETE /api/v1/projects/{id}` - Delete project
- `POST /api/v1/repositories/analyze` - Analyze GitHub repository

### Secrets Service
- `POST /api/v1/secrets` - Create secret
- `GET /api/v1/secrets/project/{project_id}` - List project secrets
- `PUT /api/v1/secrets/{id}` - Update secret
- `DELETE /api/v1/secrets/{id}` - Delete secret

### Deployment Service
- `POST /api/v1/deployments` - Create deployment
- `GET /api/v1/deployments/project/{project_id}` - List deployments
- `GET /api/v1/deployments/{id}` - Get deployment details
- `GET /api/v1/deployments/{id}/logs` - Stream deployment logs
- `POST /api/v1/deployments/{id}/retry` - Retry failed deployment

## Development Setup

### Prerequisites
- Python 3.12+
- Docker
- Nomad 1.6+
- Consul 1.16+
- Vault 1.14+
- PostgreSQL 15+
- Apache Kafka 3.5+
- Sonatype Nexus OSS

### Starting the Platform

1. **Start infrastructure services**:
```bash
cd infra
./start_infra.sh
```

2. **Run database migrations**:
```bash
nomad job run infra/nomad-stack/jobs/migrations/migrate-auth-service.nomad
nomad job run infra/nomad-stack/jobs/migrations/migrate-project-service.nomad
nomad job run infra/nomad-stack/jobs/migrations/migrate-secrets-service.nomad
nomad job run infra/nomad-stack/jobs/migrations/migrate-deployment-service.nomad
```

3. **Deploy platform services**:
```bash
./start_jobs.sh
```

4. **Verify services**:
```bash
nomad status
consul catalog services
```

### Accessing Services

- **Nomad UI**: http://localhost:4646
- **Consul UI**: http://localhost:8500
- **Vault UI**: http://localhost:8200
- **Nexus UI**: http://localhost:8083
- **OpenSearch Dashboards**: http://localhost:5601
- **Traefik Dashboard**: http://localhost:8090/dashboard/

## Architecture Principles

### Clean Architecture
Services follow Clean Architecture principles with clear separation of concerns:
- **Domain Layer**: Pure business logic and entities
- **Application Layer**: Use cases and application services
- **Infrastructure Layer**: External integrations (databases, APIs, message brokers)
- **Presentation Layer**: HTTP API endpoints and request/response models

### SOLID Principles
- **Single Responsibility**: Each service has a focused domain
- **Open/Closed**: Extensible through interfaces and dependency injection
- **Liskov Substitution**: Interface-based design with Dishka DI
- **Interface Segregation**: Minimal, focused interfaces
- **Dependency Inversion**: Dependencies injected via IoC container

### Event-Driven Architecture
Services communicate asynchronously via Kafka events to ensure:
- Loose coupling between services
- Resilience to service failures
- Scalability through horizontal scaling
- Event sourcing for audit trails

## Technology Decisions

### Why Nomad over Kubernetes?
- **Simplicity**: Lower operational complexity for smaller teams
- **Resource Efficiency**: Minimal overhead compared to Kubernetes
- **Flexibility**: Supports Docker, raw executables, and custom drivers
- **Integration**: First-class integration with Consul and Vault

### Why Consul for Service Discovery?
- **DNS Integration**: Native DNS interface for service discovery
- **Health Checking**: Built-in health check system
- **KV Store**: Distributed configuration storage
- **Service Mesh**: Optional mTLS and traffic management

### Why Vault for Secrets?
- **Dynamic Secrets**: Generate database credentials on-demand
- **Encryption**: Secure storage with automatic encryption
- **Access Control**: Fine-grained policies per project
- **Audit Logging**: Complete audit trail of secret access

### Why FastAPI?
- **Performance**: Async/await support for high concurrency
- **Type Safety**: Pydantic models with automatic validation
- **Documentation**: Auto-generated OpenAPI specs
- **Modern**: Built on Starlette and Python 3.7+ features

## Monitoring and Observability

### Logging
- **Collection**: Logstash ingests logs from all services
- **Storage**: OpenSearch stores structured log data
- **Visualization**: OpenSearch Dashboards for log analysis
- **Format**: Structured JSON logging with correlation IDs

### Health Checks
- **Nomad**: Task-level health checks via HTTP/TCP
- **Consul**: Service-level health checks with configurable intervals
- **Application**: `/api/v1/system/health` endpoint per service

## Security Considerations

### Secret Management
- Secrets stored in Vault, never in code or environment variables
- Per-project Vault policies restrict access scope
- Workload identity for Nomad-Vault integration

### Network Security
- Services communicate over internal network
- Traefik as single entry point for external traffic
- Consul DNS for internal service discovery

### Authentication
- GitHub OAuth for user authentication
- JWT tokens for API authentication
- Session management with Redis

## Future Enhancements

### Planned Features
- **Metrics Collection**: Prometheus integration for metrics
- **Distributed Tracing**: Jaeger for request tracing
- **Automated Testing**: CI pipeline integration
- **Blue-Green Deployments**: Zero-downtime deployment strategy
- **Auto-Scaling**: Dynamic scaling based on metrics
- **Multi-Tenancy**: Resource quotas and isolation per user

### Observability Improvements
- Grafana dashboards for metrics visualization
- Alerting with Prometheus AlertManager
- Distributed tracing with OpenTelemetry
- Custom application metrics

### Infrastructure as Code
- Terraform for infrastructure provisioning
- Ansible for configuration management
- GitOps workflow for deployment automation

## Contributing

This is an academic project developed as part of DevOps coursework.

## License

This project is developed for educational purposes.

## Contact

For questions or feedback, please refer to the project repository.
