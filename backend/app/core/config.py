"""Application configuration."""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )

    # Environment
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # OpenAI
    OPENAI_API_KEY: str

    # Gmail API
    GMAIL_CREDENTIALS_PATH: str = "./credentials.json"
    GMAIL_TOKEN_PATH: str = "./token.json"
    GMAIL_POLLING_INTERVAL_MINUTES: int = 10

    # S3 Storage
    S3_ENDPOINT: str = "https://s3.amazonaws.com"
    S3_BUCKET: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_REGION: str = "us-east-1"

    # Agent Configuration
    DEFAULT_LLM_MODEL: str = "gpt-4-turbo-preview"
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-3-small"
    MAX_CONTEXT_MESSAGES: int = 10
    CONFIDENCE_THRESHOLD: float = 0.7
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == "production"


settings = Settings()
