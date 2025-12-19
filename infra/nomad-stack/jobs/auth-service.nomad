job "auth-service" {
  datacenters = ["dc1"]
  type = "service"

  group "auth-service" {
    count = 2

    network {
      port "http" {}
    }

    task "auth-service" {
      driver = "raw_exec"

      vault {}

      template {
        data = <<EOH
{{ with secret "secret/data/services/auth" }}
PYTHONPATH="{{ .Data.data.pythonpath }}"
POSTGRES_AUTH_HOST="{{ .Data.data.postgres_host }}"
POSTGRES_AUTH_PORT="{{ .Data.data.postgres_port }}"
POSTGRES_AUTH_LOGIN="{{ .Data.data.postgres_login }}"
POSTGRES_AUTH_PASSWORD="{{ .Data.data.postgres_password }}"
POSTGRES_AUTH_DATABASE="{{ .Data.data.postgres_database }}"
REDIS_HOST="{{ .Data.data.redis_host }}"
REDIS_PORT="{{ .Data.data.redis_port }}"
KAFKA_BOOTSTRAP_SERVERS="{{ .Data.data.kafka_bootstrap_servers }}"
JWT_SECRET_KEY="{{ .Data.data.jwt_secret_key }}"
GITHUB_OAUTH_CLIENT_ID="{{ .Data.data.github_oauth_client_id }}"
GITHUB_OAUTH_CLIENT_SECRET="{{ .Data.data.github_oauth_client_secret }}"
GITHUB_OAUTH_REDIRECT_URI="{{ .Data.data.github_oauth_redirect_uri }}"
FRONTEND_URL="{{ .Data.data.frontend_url }}"
{{ end }}
EOH
        destination = "secrets/vault.env"
        env = true
      }

      config {
        command = "/bin/bash"
        args = [
          "-c",
          "cd /Users/Lazynx/VSC/kbtu/devops-platform/services/auth-service && uv run uvicorn auth_service.app:get_app --factory --host 127.0.0.1 --port ${NOMAD_PORT_http} --reload"
        ]
      }

      service {
        name = "auth-service"
        port = "http"
        address = "127.0.0.1"
        
        tags = [
          "traefik.enable=true",
          "traefik.http.routers.auth-service.rule=Host(`auth-service.localhost`)",
          "traefik.http.routers.auth-service.entrypoints=web",
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