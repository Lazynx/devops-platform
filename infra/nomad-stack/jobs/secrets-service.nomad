job "secrets-service" {
  datacenters = ["dc1"]
  type = "service"

  group "secrets-service" {
    count = 2

    network {
      port "http" {}
    }

    task "secrets-service" {
      driver = "raw_exec"

      vault {}

      template {
        data = <<EOH
{{ with secret "secret/data/services/secrets" }}
PYTHONPATH="{{ .Data.data.pythonpath }}"
POSTGRES_SECRETS_HOST="{{ .Data.data.postgres_host }}"
POSTGRES_SECRETS_PORT="{{ .Data.data.postgres_port }}"
POSTGRES_SECRETS_LOGIN="{{ .Data.data.postgres_login }}"
POSTGRES_SECRETS_PASSWORD="{{ .Data.data.postgres_password }}"
POSTGRES_SECRETS_DATABASE="{{ .Data.data.postgres_database }}"
KAFKA_BOOTSTRAP_SERVERS="{{ .Data.data.kafka_bootstrap_servers }}"
VAULT_URL="{{ .Data.data.vault_url }}"
VAULT_TOKEN="{{ .Data.data.vault_token }}"
VAULT_MOUNT_POINT="{{ .Data.data.vault_mount_point }}"
{{ end }}
EOH
        destination = "secrets/vault.env"
        env = true
      }

      config {
        command = "/bin/bash"
        args = [
          "-c",
          "cd /Users/Lazynx/VSC/kbtu/devops-platform/services/secrets-service && uv run uvicorn secrets_service.app:get_app --factory --host 127.0.0.1 --port ${NOMAD_PORT_http} --reload"
        ]
      }

      service {
        name = "secrets-service"
        port = "http"
        address = "127.0.0.1"
        
        tags = [
          "traefik.enable=true",
          "traefik.http.routers.secrets-service.rule=Host(`secrets-service.localhost`)",
          "traefik.http.routers.secrets-service.entrypoints=web",
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