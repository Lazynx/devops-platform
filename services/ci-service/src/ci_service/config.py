from pathlib import Path

from pydantic import SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / '.env'

class PostgresConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix='POSTGRES_PROJECT_',
        env_file=ENV_FILE,
    )
    host: str= 'localhost'
    port: int = 5432
    login: str = 'postgres'
    password: str = 'postgres'
    database: str = 'test_task'

    @computed_field
    @property
    def database_url(self) -> str:
        return f'postgresql+asyncpg://{self.login}:{self.password}@{self.host}:{self.port}/{self.database}'


class Settings(BaseSettings):
    secret_key: SecretStr = SecretStr('')
    auth_service_url: str = 'http://localhost:8000'
    github_api_url: str = 'https://api.github.com'
    webhook_url: str = 'http://localhost:8001'
    postgres: PostgresConfig = PostgresConfig()

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding='utf-8',
        case_sensitive=False,
    )

settings = Settings()

