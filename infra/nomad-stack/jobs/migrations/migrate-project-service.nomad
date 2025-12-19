job "migrate-project-service" {
  datacenters = ["dc1"]
  type = "batch"

  group "migrate" {
    count = 1

    task "migrate" {
      driver = "raw_exec"

      vault {}

      template {
        data = <<EOH
{{ with secret "secret/data/services/project" }}
POSTGRES_PROJECT_HOST="{{ .Data.data.postgres_host }}"
POSTGRES_PROJECT_PORT="{{ .Data.data.postgres_port }}"
POSTGRES_PROJECT_LOGIN="{{ .Data.data.postgres_login }}"
POSTGRES_PROJECT_PASSWORD="{{ .Data.data.postgres_password }}"
POSTGRES_PROJECT_DATABASE="{{ .Data.data.postgres_database }}"
{{ end }}
EOH
        destination = "secrets/vault.env"
        env = true
      }

      config {
        command = "/bin/bash"
        args = [
          "-c",
          "cd /Users/Lazynx/VSC/kbtu/devops-platform/services/project-service && uv run alembic upgrade head"
        ]
      }

      env {
        PYTHONPATH = "/Users/Lazynx/VSC/kbtu/devops-platform/services/project-service/src"
      }

      resources {
        cpu = 100
        memory = 128
      }
    }
  }
}
