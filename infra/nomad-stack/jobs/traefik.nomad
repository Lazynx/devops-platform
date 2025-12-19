job "traefik" {
  datacenters = ["dc1"]
  type        = "service"

  group "traefik" {
    count = 1

    network {
      port "http" {
        static = 8090
      }
      port "api" {
        static = 8092
      }
    }

    task "traefik" {
      driver = "raw_exec"

      config {
        command = "/opt/homebrew/bin/traefik"
        args = [
          "--api.insecure=true",
          "--api.dashboard=true",
          "--entrypoints.web.address=127.0.0.1:8090",
          "--entrypoints.traefik.address=127.0.0.1:8092",
          "--providers.consulcatalog=true",
          "--providers.consulcatalog.endpoint.address=127.0.0.1:8500",
          "--providers.consulcatalog.exposedByDefault=false",
          "--providers.consulcatalog.prefix=traefik",
          "--ping=true",
          "--log.level=DEBUG"
        ]
      }

      service {
        name = "traefik"
        port = "api"
        address = "127.0.0.1"
        
        check {
          type     = "http"
          path     = "/ping"
          interval = "10s"
          timeout  = "2s"
          method   = "GET"
          port     = "api"
        }
      }
    }
  }
}
