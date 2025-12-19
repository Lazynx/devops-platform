#!/bin/bash

# Determine the correct path based on where script is run from
if [ -d "infra" ]; then
    JOBS_DIR="infra/nomad-stack/jobs/migrations"
elif [ -d "nomad-stack" ]; then
    JOBS_DIR="nomad-stack/jobs/migrations"
else
    echo "Error: Run from project root or infra directory"
    exit 1
fi

SERVICES=("auth-service" "project-service" "deployment-service" "secrets-service")

echo "Running migrations for all services..."

for service in "${SERVICES[@]}"; do
    echo ""
    echo "====================================="
    echo "Migrating: $service"
    echo "====================================="
    
    nomad job run "$JOBS_DIR/migrate-$service.nomad"
    
    if [ $? -eq 0 ]; then
        echo "✓ $service migration submitted"
        
        JOB_ID="migrate-$service"
        
        echo "Waiting for migration to complete..."
        while true; do
            STATUS=$(nomad job status $JOB_ID 2>/dev/null | grep "Status" | head -1 | awk '{print $3}')
            
            if [ "$STATUS" == "dead" ]; then
                echo "✓ $service migration completed"
                break
            elif [ "$STATUS" == "running" ]; then
                echo "  Migration in progress..."
                sleep 2
            else
                sleep 1
            fi
        done
        
        nomad job stop -purge $JOB_ID 2>/dev/null
    else
        echo "✗ Failed to submit $service migration"
        exit 1
    fi
done

echo ""
echo "====================================="
echo "All migrations completed!"
echo "====================================="
