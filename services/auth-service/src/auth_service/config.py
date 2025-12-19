from pathlib import Path

from pydantic import SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / '.env'

class PostgresConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix='POSTGRES_AUTH_',
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


class JWTConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix='JWT_',
        env_file=ENV_FILE,
    )
    secret_key: SecretStr = SecretStr('')
    algorithm: str = 'HS256'
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 60


class GithubOAuthConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix='GITHUB_OAUTH_',
        env_file=ENV_FILE,
    )
    client_id: str = 'your_client_id'
    client_secret: str = 'your_client_secret'
    redirect_uri: str = 'http://localhost:8000/api/v1/auth/github/callback'


class RedisConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix='REDIS_',
        env_file=ENV_FILE,
    )
    host: str = 'localhost'
    port: int = 6379
    password: str | None = None
    db: int = 0

    @computed_field
    @property
    def url(self) -> str:
        if self.password:
            return f'redis://:{self.password}@{self.host}:{self.port}/{self.db}'
        return f'redis://{self.host}:{self.port}/{self.db}'


class KafkaConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix='KAFKA_',
        env_file=ENV_FILE,
    )
    bootstrap_servers: str = ''


class Settings(BaseSettings):
    secret_key: SecretStr = SecretStr('')
    frontend_url: str = 'http://localhost:3000'
    postgres: PostgresConfig = PostgresConfig()
    jwt: JWTConfig = JWTConfig()
    redis: RedisConfig = RedisConfig()
    github_oauth: GithubOAuthConfig = GithubOAuthConfig()
    kafka: KafkaConfig = KafkaConfig()

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding='utf-8',
        case_sensitive=False,
    )

settings = Settings()

