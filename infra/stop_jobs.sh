#!/bin/bash

echo "Stopping Deployment Service..."
nomad job stop -purge deployment-service

echo "Stopping Project Service..."
nomad job stop -purge project-service

echo "Stopping Auth Service..."
nomad job stop -purge auth-service

echo "Stopping Secrets Service..."
nomad job stop -purge secrets-service

echo "Stopping Logstash..."
nomad job stop -purge logstash

echo "Stopping OpenSearch Dashboards..."
nomad job stop -purge opensearch-dashboards

echo "Stopping Traefik..."
nomad job stop -purge traefik

echo "All jobs stopped."