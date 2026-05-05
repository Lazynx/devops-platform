job "migrate-secrets-service" {
  datacenters = ["dc1"]
  type = "batch"

  group "migrate" {
    count = 1

    task "migrate" {
      driver = "raw_exec"

      vault {}

      template {
        data = <<EOH
{{ with secret "secret/data/services/secrets" }}
POSTGRES_SECRETS_HOST="{{ .Data.data.postgres_host }}"
POSTGRES_SECRETS_PORT="{{ .Data.data.postgres_port }}"
POSTGRES_SECRETS_LOGIN="{{ .Data.data.postgres_login }}"
POSTGRES_SECRETS_PASSWORD="{{ .Data.data.postgres_password }}"
POSTGRES_SECRETS_DATABASE="{{ .Data.data.postgres_database }}"
{{ end }}
EOH
        destination = "secrets/vault.env"
        env = true
      }

      config {
        command = "/bin/bash"
        args = [
          "-c",
          "cd ${var.project_root}/services/secrets-service && uv run alembic upgrade head"
        ]
      }

      env {
        PYTHONPATH = "${var.project_root}/services/secrets-service/src"
      }

      resources {
        cpu = 100
        memory = 128
      }
    }
  }
}
