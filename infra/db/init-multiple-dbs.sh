#!/bin/bash
# Создаёт все базы данных из переменной POSTGRES_MULTIPLE_DATABASES
# Формат: POSTGRES_MULTIPLE_DATABASES=db1,db2,db3

set -e

if [ -z "$POSTGRES_MULTIPLE_DATABASES" ]; then
  echo "POSTGRES_MULTIPLE_DATABASES not set, skipping"
  exit 0
fi

echo "Creating databases: $POSTGRES_MULTIPLE_DATABASES"

for db in $(echo "$POSTGRES_MULTIPLE_DATABASES" | tr ',' ' '); do
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    SELECT 'CREATE DATABASE $db' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db')\gexec
EOSQL
  echo "  ✓ $db"
done
