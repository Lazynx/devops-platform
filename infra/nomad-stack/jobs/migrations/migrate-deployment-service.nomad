job "migrate-deployment-service" {
  datacenters = ["dc1"]
  type = "batch"

  group "migrate" {
    count = 1

    task "migrate" {
      driver = "raw_exec"

      vault {}

      template {
        data = <<EOH
{{ with secret "secret/data/services/deployment" }}
POSTGRES_DEPLOYMENT_HOST="{{ .Data.data.postgres_host }}"
POSTGRES_DEPLOYMENT_PORT="{{ .Data.data.postgres_port }}"
POSTGRES_DEPLOYMENT_LOGIN="{{ .Data.data.postgres_login }}"
POSTGRES_DEPLOYMENT_PASSWORD="{{ .Data.data.postgres_password }}"
POSTGRES_DEPLOYMENT_DATABASE="{{ .Data.data.postgres_database }}"
{{ end }}
EOH
        destination = "secrets/vault.env"
        env = true
      }

      config {
        command = "/bin/bash"
        args = [
          "-c",
          "cd /Users/Lazynx/VSC/kbtu/devops-platform/services/deployment-service && uv run alembic upgrade head"
        ]
      }

      env {
        PYTHONPATH = "/Users/Lazynx/VSC/kbtu/devops-platform/services/deployment-service/src"
      }

      resources {
        cpu = 100
        memory = 128
      }
    }
  }
}
