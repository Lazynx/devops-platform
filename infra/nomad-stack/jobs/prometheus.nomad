job "prometheus" {
  datacenters = ["dc1"]
  type = "service"

  group "prometheus" {
    count = 1

    network {
      port "http" {
        static = 9090
      }
    }

    task "prometheus" {
      driver = "raw_exec"

      config {
        command = "/opt/homebrew/bin/prometheus"
        args = [
          "--config.file=${NOMAD_TASK_DIR}/prometheus.yml",
          "--storage.tsdb.path=${NOMAD_ALLOC_DIR}/data",
          "--web.listen-address=127.0.0.1:${NOMAD_PORT_http}",
          "--web.console.templates=/opt/homebrew/opt/prometheus/etc/prometheus/consoles",
          "--web.console.libraries=/opt/homebrew/opt/prometheus/etc/prometheus/console_libraries"
        ]
      }

      template {
        source      = "${var.project_root}/infra/monitoring/prometheus.yml"
        destination = "local/prometheus.yml"
      }

      template {
        source      = "${var.project_root}/infra/monitoring/nomad_alerts.yml"
        destination = "local/nomad_alerts.yml"
      }

      resources {
        cpu    = 500
        memory = 512
      }

      service {
        name = "prometheus"
        port = "http"
        address = "127.0.0.1"

        tags = [
          "monitoring",
          "traefik.enable=true",
          "traefik.http.routers.prometheus.rule=Host(`prometheus.localhost`)",
          "traefik.http.routers.prometheus.entrypoints=web"
        ]

        check {
          type     = "http"
          path     = "/-/healthy"
          interval = "10s"
          timeout  = "2s"
          method   = "GET"
        }
      }
    }
  }
}
