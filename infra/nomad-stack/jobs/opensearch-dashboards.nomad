job "opensearch-dashboards" {
  datacenters = ["dc1"]
  type        = "service"

  group "opensearch-dashboards" {
    count = 1

    network {
      port "http" {
        static = 5601
      }
    }

    task "opensearch-dashboards" {
      driver = "raw_exec"

      config {
        command = "/opt/homebrew/bin/opensearch-dashboards"
        # Assuming default config location or we can pass a config file via args if needed.
        # Usually environment variables are easier for simple overrides.
      }

      env {
        OPENSEARCH_HOSTS = "http://127.0.0.1:9200"
        SERVER_HOST = "0.0.0.0"
        DISABLE_SECURITY_DASHBOARDS_PLUGIN = "true" # If applicable to the brew version
      }
      
      # If we need a custom config file, we can template it and point to it.
      # But for brew install, it might use /opt/homebrew/etc/opensearch-dashboards/opensearch_dashboards.yml
      # Let's try setting env vars first.

      service {
        name = "opensearch-dashboards"
        port = "http"
        address = "127.0.0.1"
        
        tags = [
          "traefik.enable=true",
          "traefik.http.routers.opensearch-dashboards.rule=Host(`opensearch-dashboards.localhost`)",
          "traefik.http.routers.opensearch-dashboards.entrypoints=web",
        ]

        check {
          type     = "http"
          path     = "/api/status"
          interval = "30s"
          timeout  = "10s"
          method   = "GET"
        }
      }
    }
  }
}
