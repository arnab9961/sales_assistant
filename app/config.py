import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Sunset Kuakata Operations Intelligence"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Privacy & Anonymization
    ANONYMIZE_NAMES: bool = True

    # Database URLs
    # Defaults to Supabase IPv4 pooler if not specified in env
    DATABASE_URL: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://sales_app.ccivcmvwhjireufzuvxs:SalesApp2026!Secure@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres"
        )
    )
    DATABASE_RO_URL: Optional[str] = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_RO_URL",
            "postgresql+psycopg2://sales_app.ccivcmvwhjireufzuvxs:SalesApp2026!Secure@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres"
        )
    )

    # Groq LLM API
    GROQ_API_KEY: Optional[str] = Field(default_factory=lambda: os.getenv("GROQ_API_KEY", None))
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    # Webhooks
    WEBHOOK_API_KEY: str = "change_me_webhook_secret_key_12345"
    N8N_WEBHOOK_URL: Optional[str] = None

    # Data directory
    DATA_DIR: str = "data"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
