def generate_build_job_hcl(
    project_id: str,
    version: str,
    github_repo_url: str,
    github_token: str | None,
    dockerfile_path: str,
    build_context: str,
    registry_url: str,
    nexus_user: str,
    nexus_password: str,
    repository_name: str = 'docker-hosted',
) -> str:
    image_tag = f"{registry_url}/{repository_name}/project-{project_id}:{version}"
    
    # Embed token in URL for private repos: https://TOKEN@github.com/owner/repo
    if github_token and "github.com" in github_repo_url:
        authenticated_url = github_repo_url.replace("https://github.com", f"https://{github_token}@github.com")
    else:
        authenticated_url = github_repo_url
    
    import logging
    logger = logging.getLogger(__name__)
    job_hcl = f"""
job "build-{project_id}-{version}" {{
  datacenters = ["dc1"]
  type = "batch"

  group "build" {{
    count = 1

    task "build-and-push" {{
      driver = "docker"

      config {{
        image = "docker:cli"
        args = [
          "sh",
          "-c",
          "echo '{nexus_password}' | docker login {registry_url} -u {nexus_user} --password-stdin && apk add git && git clone {authenticated_url} repo && cd repo && docker build -t {image_tag} -f {dockerfile_path} {build_context} && docker push {image_tag}"
        ]
        volumes = [
          "/var/run/docker.sock:/var/run/docker.sock"
        ]
        network_mode = "host"
      }}

      env {{
        DOCKER_BUILDKIT = "1"
      }}

      resources {{
        cpu    = 500
        memory = 512
      }}
    }}
  }}
}}
"""
    logger.info(f"Generated build job HCL for {project_id}:\\n{job_hcl}")
    return job_hcl

def generate_deploy_job_hcl(
    deployment_id: str,
    project_id: str,
    project_name: str,
    version: str,
    image_url: str,
    port: int,
    secrets: list[dict],
    nexus_user: str,
    nexus_password: str,
    registry_url: str,
    start_command: str = "python manage.py runserver 0.0.0.0:$PORT",
) -> str:
    template_content = ""
    if secrets:
        # Since all secrets should now share the same vault_path (per the new bunched storage strategy),
        # we can take the path from the first secret.
        first_secret = secrets[0]
        vault_path = first_secret.get('vault_path')
        
        if vault_path:
            template_lines = []
            template_lines.append(f'{{{{ with secret "secret/data/{vault_path}" }}}}')
            for secret in secrets:
                key = secret.get('key')
                if key:
                    # Secrets are stored as key-values in the 'data' field of the KV v2 response.
                    # e.g. .Data.data.KEY
                    template_lines.append(f'{key}="{{{{ .Data.data.{key} }}}}"')
            template_lines.append(f'{{{{ end }}}}')

            template_content = "\n".join(template_lines)

    escaped_cmd = start_command.replace('\\', '\\\\').replace('"', '\\"')

    template_stanza = ""
    if template_content:
        template_stanza = f"""
      template {{
        data = <<EOH
{template_content}
EOH
        destination = "secrets/vault.env"
        env = true
      }}
"""

    return f"""
job "app-{deployment_id}" {{
  datacenters = ["dc1"]
  type = "service"

  group "app" {{
    count = 1

    network {{
      port "http" {{
        to = {port}
      }}
    }}

    task "server" {{
      driver = "docker"

      vault {{
        policies = ["project-{project_id}-read"]
      }}

{template_stanza}

      config {{
        image = "{image_url}"
        ports = ["http"]
        command = "sh"
        args = ["-c", "{escaped_cmd}"]
        
        auth {{
          username = "{nexus_user}"
          password = "{nexus_password}"
          server_address = "{registry_url}"
        }}
      }}

      env {{
        PORT = "{port}"
      }}

      service {{
        name = "app-{deployment_id}"
        port = "http"
        address_mode = "host"

        tags = [
          "traefik.enable=true",
          "traefik.http.routers.app-{deployment_id}.rule=Host(`{project_name}-{deployment_id[:8]}.localhost`)",
          "traefik.http.routers.app-{deployment_id}.entrypoints=web"
        ]

        check {{
          type         = "tcp"
          port         = "http"
          address_mode = "host"
          interval     = "10s"
          timeout      = "2s"
        }}
      }}

      resources {{
        cpu    = 256
        memory = 256
      }}
    }}
  }}
}}
"""