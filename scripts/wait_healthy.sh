#!/bin/bash
# Ждёт пока критические сервисы Docker Compose станут healthy

set -euo pipefail

TIMEOUT=120
INTERVAL=5

wait_for() {
  local name=$1
  local check_cmd=$2
  local elapsed=0

  printf "  Waiting for %-20s " "$name..."
  until eval "$check_cmd" &>/dev/null; do
    if [ "$elapsed" -ge "$TIMEOUT" ]; then
      echo "TIMEOUT"
      exit 1
    fi
    sleep "$INTERVAL"
    elapsed=$((elapsed + INTERVAL))
    printf "."
  done
  echo " OK"
}

wait_for "PostgreSQL" "docker exec devops-postgres pg_isready -U postgres"
wait_for "Redis"      "docker exec devops-redis redis-cli ping"
wait_for "OpenSearch" "curl -sf http://localhost:9200/_cluster/health"

# Kafka — просто проверяем что порт открыт (SASL усложняет health check)
wait_for "Kafka" "bash -c 'echo > /dev/tcp/localhost/9094' 2>/dev/null"

echo ""
echo "All services are ready."
