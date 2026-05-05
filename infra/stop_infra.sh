#!/bin/bash

echo "Stopping infrastructure..."
echo ""

echo "Stopping Nomad..."
pkill -TERM nomad
sleep 2

echo "Stopping Vault..."
pkill -TERM vault
sleep 2

echo "Stopping Consul..."
pkill -TERM consul
sleep 2

echo "Stopping Prometheus..."
pkill -x prometheus
sleep 1

echo "Stopping Alertmanager..."
pkill -x alertmanager
sleep 1

echo "Infrastructure stopped."
echo ""
echo "Note: Stateful services (Postgres, Redis, Kafka, OpenSearch, Nexus) are managed"
echo "      by Docker Compose. Stop them with: docker compose -f docker-compose.dev.yml down"
echo "      or via Makefile: make down-compose"