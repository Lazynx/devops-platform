#!/bin/bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"

echo "Configuring for PROJECT_ROOT=$PROJECT_ROOT"

INFRA="$PROJECT_ROOT/infra/nomad-stack"

sed "s|PROJECT_ROOT|$PROJECT_ROOT|g" "$INFRA/nomad-config.hcl.example" > "$INFRA/nomad-config.hcl"
sed "s|PROJECT_ROOT|$PROJECT_ROOT|g" "$INFRA/consul-config.hcl.example" > "$INFRA/consul-config.hcl"

echo "Generated:"
echo "  $INFRA/nomad-config.hcl"
echo "  $INFRA/consul-config.hcl"
