job "deployment-service" {
  datacenters = ["dc1"]
  type = "service"

  group "deployment-service" {
    count = 2

    network {
      port "http" {}
    }

    task "deployment-service" {
      driver = "raw_exec"

      vault {}

      template {
        data = <<EOH
{{ with secret "secret/data/services/deployment" }}
PYTHONPATH="{{ .Data.data.pythonpath }}"
POSTGRES_DEPLOYMENT_HOST="{{ .Data.data.postgres_host }}"
POSTGRES_DEPLOYMENT_PORT="{{ .Data.data.postgres_port }}"
POSTGRES_DEPLOYMENT_LOGIN="{{ .Data.data.postgres_login }}"
POSTGRES_DEPLOYMENT_PASSWORD="{{ .Data.data.postgres_password }}"
POSTGRES_DEPLOYMENT_DATABASE="{{ .Data.data.postgres_database }}"
KAFKA_BOOTSTRAP_SERVERS="{{ .Data.data.kafka_bootstrap_servers }}"
NEXUS_REGISTRY_URL="{{ .Data.data.nexus_registry_url }}"
NEXUS_USER="{{ .Data.data.nexus_user }}"
NEXUS_PASSWORD="{{ .Data.data.nexus_password }}"
{{ end }}
EOH
        destination = "secrets/vault.env"
        env = true
      }

      config {
        command = "/bin/bash"
        args = [
          "-c",
          "cd /Users/Lazynx/VSC/kbtu/devops-platform/services/deployment-service && uv run uvicorn deployment_service.app:get_app --factory --host 127.0.0.1 --port ${NOMAD_PORT_http} --reload"
        ]
      }

      service {
        name = "deployment-service"
        port = "http"
        address = "127.0.0.1"
        
        tags = [
          "traefik.enable=true",
          "traefik.http.routers.deployment-service.rule=Host(`deployment-service.localhost`)",
          "traefik.http.routers.deployment-service.entrypoints=web",
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