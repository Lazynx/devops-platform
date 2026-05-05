job "migrate-auth-service" {
  datacenters = ["dc1"]
  type = "batch"

  group "migrate" {
    count = 1

    task "migrate" {
      driver = "raw_exec"

      vault {}

      template {
        data = <<EOH
{{ with secret "secret/data/services/auth" }}
POSTGRES_AUTH_HOST="{{ .Data.data.postgres_host }}"
POSTGRES_AUTH_PORT="{{ .Data.data.postgres_port }}"
POSTGRES_AUTH_LOGIN="{{ .Data.data.postgres_login }}"
POSTGRES_AUTH_PASSWORD="{{ .Data.data.postgres_password }}"
POSTGRES_AUTH_DATABASE="{{ .Data.data.postgres_database }}"
{{ end }}
EOH
        destination = "secrets/vault.env"
        env = true
      }

      config {
        command = "/bin/bash"
        args = [
          "-c",
          "cd ${var.project_root}/services/auth-service && uv run alembic upgrade head"
        ]
      }

      env {
        PYTHONPATH = "${var.project_root}/services/auth-service/src"
      }

      resources {
        cpu = 100
        memory = 128
      }
    }
  }
}