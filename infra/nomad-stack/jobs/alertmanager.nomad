variable "project_root" {
  type        = string
  description = "Absolute path to the project root directory."
}

job "alertmanager" {
  datacenters = ["dc1"]
  type = "service"

  group "alertmanager" {
    count = 1

    network {
      port "http" {
        static = 9097
      }
    }

    task "alertmanager" {
      driver = "raw_exec"

      config {
        command = "/opt/homebrew/bin/alertmanager"
        args = [
          "--config.file=${NOMAD_TASK_DIR}/alertmanager.yml",
          "--storage.path=${NOMAD_ALLOC_DIR}/data",
          "--web.listen-address=127.0.0.1:${NOMAD_PORT_http}"
        ]
      }

      template {
        source      = "${var.project_root}/infra/monitoring/alertmanager.yml"
        destination = "local/alertmanager.yml"
      }

      resources {
        cpu    = 300
        memory = 256
      }

      service {
        name = "alertmanager"
        port = "http"
        address = "127.0.0.1"

        tags = [
          "monitoring",
          "traefik.enable=true",
          "traefik.http.routers.alertmanager.rule=Host(`alertmanager.localhost`)",
          "traefik.http.routers.alertmanager.entrypoints=web"
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
