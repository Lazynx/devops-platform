# Secrets Service

Secure secrets management service using HashiCorp Vault.

## Features

- Store and retrieve secrets securely via Vault
- Project and deployment-scoped secrets
- REST API for CRUD operations
- Kafka event publishing for secret lifecycle events
- SQLAlchemy metadata storage

## Setup

1. Install dependencies:
```bash
uv sync
```

2. Run migrations:
```bash
alembic upgrade head
```

3. Start service:
```bash
uv run python -m secrets_service.app
```
