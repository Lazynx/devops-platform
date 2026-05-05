variable "project_root" {
  type        = string
  description = "Absolute path to the project root directory."
}

job "logstash" {
  datacenters = ["dc1"]
  type = "service"

  group "logstash" {
    count = 1

    network {
      port "http" {
        static = 9600
      }
    }

    task "logstash" {
      driver = "raw_exec"

      config {
        command = "bash"
        args = [
          "-c",
          "export LS_JAVA_OPTS='-Xms1g -Xmx2g' && /opt/homebrew/bin/logstash --path.data ${NOMAD_ALLOC_DIR}/data -f ${NOMAD_TASK_DIR}/logstash.conf"
        ]
      }

      template {
        data = <<EOH
input {
  kafka {
    bootstrap_servers => "kafka.service.consul:9094"
    topics => ["service-logs"]
    codec => "json"
    auto_offset_reset => "latest"
  }
}

output {
  opensearch {
    hosts => ["http://opensearch.service.consul:9200"]
    index => "logs-%%{service}-%%{+YYYY.MM.dd}"
    ssl_certificate_verification => false
  }
}
EOH
        destination = "local/logstash.conf"
      }

      resources {
        cpu = 1000
        memory = 2560
      }

      service {
        name = "logstash"
        port = "http"
        address = "127.0.0.1"
        
        check {
          type = "http"
          path = "/"
          interval = "30s"
          timeout = "5s"
          method = "GET"
        }
      }
    }
  }
}