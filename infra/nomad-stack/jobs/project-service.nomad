variable "project_root" {
  type        = string
  description = "Absolute path to the project root directory."
}

job "project-service" {
  datacenters = ["dc1"]
  type = "service"

  group "project-service" {
    count = 2

    network {
      port "http" {}
    }

    task "project-service" {
      driver = "raw_exec"

      vault {}

      template {
        data = <<EOH
{{ with secret "secret/data/services/project" }}
PYTHONPATH="{{ .Data.data.pythonpath }}"
POSTGRES_PROJECT_HOST="{{ .Data.data.postgres_host }}"
POSTGRES_PROJECT_PORT="{{ .Data.data.postgres_port }}"
POSTGRES_PROJECT_LOGIN="{{ .Data.data.postgres_login }}"
POSTGRES_PROJECT_PASSWORD="{{ .Data.data.postgres_password }}"
POSTGRES_PROJECT_DATABASE="{{ .Data.data.postgres_database }}"
KAFKA_BOOTSTRAP_SERVERS="{{ .Data.data.kafka_bootstrap_servers }}"
AUTH_SERVICE_URL="{{ .Data.data.auth_service_url }}"
SECRETS_SERVICE_URL="{{ .Data.data.secrets_service_url }}"
DEPLOYMENT_SERVICE_URL="{{ .Data.data.deployment_service_url }}"
{{ end }}
EOH
        destination = "secrets/vault.env"
        env = true
      }

      config {
        command = "/bin/bash"
        args = [
          "-c",
          "cd ${var.project_root}/services/project-service && uv run uvicorn project_service.app:get_app --factory --host 127.0.0.1 --port ${NOMAD_PORT_http} --reload"
        ]
      }

      service {
        name = "project-service"
        port = "http"
        address = "127.0.0.1"
        
        tags = [
          "traefik.enable=true",
          "traefik.http.routers.project-service.rule=Host(`project-service.localhost`)",
          "traefik.http.routers.project-service.entrypoints=web",
        ]

        check {
          type = "http"
          path = "/api/v1/system/health"
          interval = "10s"
          timeout = "2s"
          method = "GET"
        }
      }
    }
  }
}