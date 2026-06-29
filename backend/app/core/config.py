from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', case_sensitive=True)

    APP_NAME: str = 'Collab Whiteboard'
    ENV: str = Field(default='local', description='local/test/production')
    DEBUG: bool = False
    API_PREFIX: str = '/api'

    DATABASE_URL: str = Field(default='postgresql+asyncpg://whiteboard:whiteboard@postgres:5432/whiteboard')
    SECRET_KEY: str = Field(default='change-me-local-only')
    JWT_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    CORS_ORIGINS: str = 'http://localhost:5173,http://localhost:8080'

    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, value: str, info):
        env = info.data.get('ENV', 'local')
        if env == 'production' and (not value or value in {'change-me', 'change-me-local-only'} or len(value) < 32):
            raise ValueError('Unsafe SECRET_KEY is forbidden in production')
        return value

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',') if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
