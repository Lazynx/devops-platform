from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / '.env'


class PostgresConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix='POSTGRES_OBSERVABILITY_',
        env_file=ENV_FILE,
    )
    host: str = 'localhost'
    port: int = 5432
    login: str = 'postgres'
    password: str = 'postgres'
    database: str = 'observability_service'

    @computed_field
    @property
    def database_url(self) -> str:
        return f'postgresql+asyncpg://{self.login}:{self.password}@{self.host}:{self.port}/{self.database}'


class KafkaConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix='KAFKA_',
        env_file=ENV_FILE,
    )
    bootstrap_servers: str = 'localhost:9092'


class Settings(BaseSettings):
    postgres: PostgresConfig = PostgresConfig()
    kafka: KafkaConfig = KafkaConfig()
    log_retention_days: int = 30
    metric_retention_days: int = 90

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding='utf-8',
        case_sensitive=False,
    )


settings = Settings()
