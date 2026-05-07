#!/bin/bash

if [ -d "infra" ]; then
    echo "Running from project root."
    NOMAD_CONFIG="infra/nomad-stack/nomad-config.hcl"
    CONSUL_CONFIG="infra/nomad-stack/consul-config.hcl"
    VAULT_CONFIG="infra/nomad-stack/vault-config.hcl"
    LOG_DIR="infra/logs"
    CONSUL_SERVICES_DIR="infra/nomad-stack/consul"
elif [ -d "nomad-stack" ]; then
    echo "Running from infra directory."
    NOMAD_CONFIG="nomad-stack/nomad-config.hcl"
    CONSUL_CONFIG="nomad-stack/consul-config.hcl"
    VAULT_CONFIG="nomad-stack/vault-config.hcl"
    LOG_DIR="logs"
    CONSUL_SERVICES_DIR="nomad-stack/consul"
else
    echo "Error: Cannot find configuration files."
    exit 1
fi

UNSEAL_KEY="${VAULT_UNSEAL_KEY:?Error: VAULT_UNSEAL_KEY env var is required. Export it before running.}"

mkdir -p "$LOG_DIR"

echo "Starting Consul..."
if ! pgrep -x "consul" >/dev/null; then
    nohup consul agent -config-file="$CONSUL_CONFIG" > "$LOG_DIR/consul.log" 2>&1 &
    echo "Consul started. Logs at $LOG_DIR/consul.log"
    sleep 3
else
    echo "Consul is already running."
fi

echo "Starting Vault..."
if ! pgrep -x "vault" >/dev/null; then
    nohup vault server -config="$VAULT_CONFIG" > "$LOG_DIR/vault.log" 2>&1 &
    echo "Vault started. Logs at $LOG_DIR/vault.log"
    
    export VAULT_ADDR='http://127.0.0.1:8200'
    
    echo "Waiting for Vault to be ready..."
    for i in {1..30}; do
        if vault status >/dev/null 2>&1; then
            echo "Vault is ready"
            break
        fi
        sleep 1
    done
    
    echo "Unsealing Vault..."
    vault operator unseal "$UNSEAL_KEY"
    
    if [ $? -eq 0 ]; then
        echo "Vault unsealed successfully"
    else
        echo "Vault unseal failed"
        exit 1
    fi
else
    echo "Vault is already running."
fi

sleep 2

echo "Registering services with Consul..."
consul services register "$CONSUL_SERVICES_DIR/postgres-service.json"
consul services register "$CONSUL_SERVICES_DIR/redis-service.json"
consul services register "$CONSUL_SERVICES_DIR/kafka-service.json"
consul services register "$CONSUL_SERVICES_DIR/nexus-service.json"
consul services register "$CONSUL_SERVICES_DIR/opensearch-service.json"

echo "Starting Nomad..."
if ! pgrep -x "nomad" >/dev/null; then
    nohup nomad agent -config="$NOMAD_CONFIG" > "$LOG_DIR/nomad.log" 2>&1 &
    echo "Nomad started. Logs at $LOG_DIR/nomad.log"
    sleep 3
else
    echo "Nomad is already running."
fi

echo "Infrastructure started."
echo "Consul:  http://localhost:8500"
echo "Vault:   http://localhost:8200"
echo "Nomad:   http://localhost:4646"