#!/bin/bash
set -euo pipefail

if [ -d "infra" ]; then
  JOBS_DIR="infra/nomad-stack/jobs"
  PROJECT_ROOT="$(pwd)"
elif [ -d "nomad-stack" ]; then
  JOBS_DIR="nomad-stack/jobs"
  PROJECT_ROOT="$(cd .. && pwd)"
else
  echo "Error: run from project root or infra directory."
  exit 1
fi

run_job() {
  local job_file="$1"
  echo "Submitting $(basename $job_file)..."
  nomad job run -var="project_root=$PROJECT_ROOT" "$job_file"
}

run_job_no_var() {
  local job_file="$1"
  echo "Submitting $(basename $job_file)..."
  nomad job run "$job_file"
}

run_job_no_var "$JOBS_DIR/traefik.nomad"
sleep 5

run_job "$JOBS_DIR/auth-service.nomad"
run_job "$JOBS_DIR/secrets-service.nomad"
sleep 5

run_job "$JOBS_DIR/project-service.nomad"
run_job "$JOBS_DIR/deployment-service.nomad"

run_job_no_var "$JOBS_DIR/logstash.nomad"
run_job_no_var "$JOBS_DIR/opensearch-dashboards.nomad"

echo "All jobs submitted."
