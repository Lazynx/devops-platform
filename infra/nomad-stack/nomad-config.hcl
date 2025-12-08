datacenter = "dc1"
data_dir = "/Users/Lazynx/VSC/kbtu/devops-platform/infra/nomad-stack/nomad/data"
bind_addr = "0.0.0.0"

server {
  enabled = true
  bootstrap_expect = 1
}

client {
  enabled = true

  network_interface = "en0"

  host_network "public" {
    cidr = "0.0.0.0/0"
  }

  cpu_total_compute = 40000

  options = {
    "driver.allowlist" = "docker"
  }

  reserved {
    cpu    = 1000
    memory = 1024
    disk   = 512
  }

  host_volume "docker-sock" {
    path = "/var/run/docker.sock"
    read_only = false
  }

  host_volume "builds" {
    path = "/Users/Lazynx/VSC/kbtu/devops-platform/infra/nomad-stack/nomad/builds"
    read_only = false
  }
}

plugin "docker" {
  config {
    volumes {
      enabled = true
    }

    allow_privileged = true

    extra_labels = ["job_name", "task_group_name", "task_name"]

    allow_caps = ["all"]
  }
}

consul {
  address = "127.0.0.1:8500"
  auto_advertise = true
  server_auto_join = true
  client_auto_join = true
}

telemetry {
  collection_interval = "1s"
  disable_hostname = false
  prometheus_metrics = true
  publish_allocation_metrics = true
  publish_node_metrics = true
}

vault {
  enabled = true
  address = "http://127.0.0.1:8200"
  token = "dev-root-token"
}