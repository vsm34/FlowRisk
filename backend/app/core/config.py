from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "FlowRisk"
    debug: bool = False
    environment: str = "development"  # development, production

    # Database
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/flowrisk"

    # CORS (comma-separated origins)
    cors_allowed_origins: str | None = None

    # Dev features (NEVER enable in production)
    flowrisk_dev_bypass_auth: bool = False


settings = Settings()
