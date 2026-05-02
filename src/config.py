import os
from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DbConfig(BaseModel):
    host: str = "localhost"
    port: int = 5434
    user: str = "postgres"
    password: str = "postgres"
    name: str = "auth_db"

    @property
    def url(self) -> str:
        from urllib.parse import quote
        return f"postgresql+asyncpg://{quote(self.user, safe='')}:{quote(self.password, safe='')}@{self.host}:{self.port}/{self.name}"


class AuthConfig(BaseModel):
    jwt_secret: str = "your_jwt_secret"
    token_ttl_minutes: int = 60


class GitHubConfig(BaseModel):
    app_id: int = 0
    private_key_path: str = ""
    client_id: str = ""
    client_secret: str = ""
    webhook_secret: str = ""


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8001
    base_url: str = "http://localhost:8001"
    frontend_url: str = "http://localhost:5173"


class DeploymentsServiceConfig(BaseModel):
    base_url: str = "http://localhost:8000"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AUTH_", env_nested_delimiter="__")

    env: str = "local"
    db: DbConfig = DbConfig()
    auth: AuthConfig = AuthConfig()
    github: GitHubConfig = GitHubConfig()
    server: ServerConfig = ServerConfig()
    deployments_service: DeploymentsServiceConfig = DeploymentsServiceConfig()


def load_settings() -> Settings:
    config_path = os.environ.get("CONFIG_PATH")
    if config_path and Path(config_path).exists():
        with open(config_path) as f:
            data = yaml.safe_load(f)
        return Settings(**data)
    return Settings()
