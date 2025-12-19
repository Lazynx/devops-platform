from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / '.env'


class PostgresConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix='POSTGRES_DEPLOYMENT_',
        env_file=ENV_FILE,
    )
    host: str = 'localhost'
    port: int = 5432
    login: str = 'postgres'
    password: str = 'postgres'
    database: str = 'deployment_db'

    @computed_field
    @property
    def database_url(self) -> str:
        return f'postgresql+asyncpg://{self.login}:{self.password}@{self.host}:{self.port}/{self.database}'


class KafkaConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix='KAFKA_',
        env_file=ENV_FILE,
    )
    bootstrap_servers: str = 'localhost:9094'
    username: str = 'devops_platform'
    password: str = 'platform-secret'


class Settings(BaseSettings):
    auth_service_url: str = 'http://auth-service.service.consul:8000'
    secrets_service_url: str = 'http://secrets-service.service.consul:8003'
    nomad_url: str = 'http://nomad.service.consul:4646'
    nexus_registry_url: str = 'nexus.service.consul:8082'
    nexus_docker_repository: str = 'docker-hosted'
    nexus_user: str = 'admin'
    nexus_password: str = 'admin123'
    postgres: PostgresConfig = PostgresConfig()
    kafka: KafkaConfig = KafkaConfig()

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding='utf-8',
        case_sensitive=False,
    )


settings = Settings()
