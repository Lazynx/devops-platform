# Observability Service

Centralized logging and metrics collection service with Kafka integration.

## Features

- Real-time log collection from Kafka topics
- Metrics collection and aggregation
- Time-series data storage with PostgreSQL
- RESTful API for querying logs and metrics
- Trace ID correlation for distributed tracing
- Prepared for future Grafana/ELK integration

## Architecture

- Kafka consumers for log/metric ingestion
- PostgreSQL with optimized indexes for fast queries
- Clean Architecture with repository pattern
- Ready to scale with TimescaleDB extension

## API Endpoints

### Logs
- `POST /api/v1/observability/logs/query` - Query logs with filters
- `GET /api/v1/observability/logs/service/{service_name}` - Get service logs

### Metrics
- `POST /api/v1/observability/metrics/query` - Query aggregated metrics
- `GET /api/v1/observability/metrics/service/{service_name}/{metric_name}` - Get specific metric

## Future Enhancements

- TimescaleDB for efficient time-series data
- Grafana dashboards
- ELK Stack integration
- Alert rules and notifications
- Log retention policies
