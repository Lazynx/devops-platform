#!/bin/bash

echo "Starting Traefik..."
nomad job run nomad-stack/jobs/traefik.nomad
sleep 5

echo "Starting Auth Service..."
nomad job run nomad-stack/jobs/auth-service.nomad

echo "Starting Secrets Service..."
nomad job run nomad-stack/jobs/secrets-service.nomad
sleep 5

echo "Starting Project Service..."
nomad job run nomad-stack/jobs/project-service.nomad

echo "Starting Deployment Service..."
nomad job run nomad-stack/jobs/deployment-service.nomad

echo "Starting Logstash..."
nomad job run nomad-stack/jobs/logstash.nomad

echo "Starting OpenSearch Dashboards..."
nomad job run nomad-stack/jobs/opensearch-dashboards.nomad

echo "All jobs submitted."