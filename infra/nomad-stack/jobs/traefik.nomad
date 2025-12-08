job "traefik" {
  datacenters = ["dc1"]
  type = "service"

  group "traefik" {
    count = 1

    network {
      port "http" {
        static = 8082
        host_network = "public"
      }

      port "api" {
        static = 8081
        to     = 8080
        host_network = "public"
      }
    }

    service {
      name = "traefik"
      port = "api"

      tags = [
        "traefik.enable=true",
        "traefik.http.routers.dashboard.rule=Host(`traefik.localhost`)",
        "traefik.http.routers.dashboard.service=api@internal",
        "traefik.http.routers.dashboard.entrypoints=web"
      ]

      check {
        type     = "tcp"
        interval = "10s"
        timeout  = "2s"
      }
    }

    task "traefik" {
      driver = "docker"

      config {
        image = "traefik:v2.10"
        ports = ["http", "api"]

        args = [
          "--api.insecure=true",
          "--api.dashboard=true",
          "--entrypoints.web.address=:8082",
          "--providers.consulcatalog=true",
          "--providers.consulcatalog.endpoint.address=host.docker.internal:8500",
          "--providers.consulcatalog.exposedByDefault=false",
          "--providers.consulcatalog.prefix=traefik",
          "--ping=true",
          "--log.level=DEBUG"
        ]
      }

      resources {
        cpu    = 200
        memory = 512
      }
    }
  }
}
