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

echo "Stopping Nexus..."
if [ -d "infra" ]; then
    infra/nexus/bin/nexus stop
elif [ -d "nexus" ]; then
    nexus/bin/nexus stop
fi
sleep 2

echo "Stopping OpenSearch..."
brew services stop opensearch

echo "Stopping Kafka..."
brew services stop kafka

echo "Stopping Redis..."
brew services stop redis

echo "Stopping PostgreSQL..."
brew services stop postgresql@14

echo "Infrastructure stopped."