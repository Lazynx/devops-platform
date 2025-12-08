job "registry" {
  datacenters = ["dc1"]
  type = "service"

  group "registry" {
    count = 1

    network {
      port "http" {
        to           = 5000
        static       = 5001
        
        # !!! ВАЖНО: ЭТОЙ СТРОКИ НЕ БЫЛО !!!
        # Она заставляет Docker слушать на 0.0.0.0 (всех IP), включая localhost
        host_network = "public" 
      }
    }

    service {
      name = "registry"
      port = "http"

      # Оставляем реальный IP для Consul, чтобы видеть его в UI
      address = "${attr.unique.network.ip-address}"

      # !!! ТЕГИ TRAEFIK УДАЛЕНЫ ПОЛНОСТЬЮ !!!
      tags = []

      check {
        type     = "tcp"
        interval = "10s"
        timeout  = "2s"
      }
    }

    task "registry" {
      driver = "docker"

      config {
        image = "registry:2.8"
        ports = ["http"]
      }

      resources {
        cpu    = 200
        memory = 256
      }
    }
  }
}