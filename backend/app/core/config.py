from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "ArthSetu"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # Local dev defaults to a portable SQLite file. Override via the
    # DATABASE_URL env var (e.g. postgresql+psycopg2://user:pass@host/db).
    DATABASE_URL: str = "sqlite:///./arthsetu_dev.db"

    # Comma-separated list of allowed browser origins for CORS.
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    LOG_LEVEL: str = "INFO"

    # --- Auth -------------------------------------------------------------
    # MUST be overridden in any non-local environment. Generate with:
    #   python -c "import secrets; print(secrets.token_urlsafe(48))"
    SECRET_KEY: str = "dev-insecure-change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # First-run bootstrap admin (created by the seeder / on empty user table).
    BOOTSTRAP_ADMIN_USERNAME: str = "admin"
    BOOTSTRAP_ADMIN_PASSWORD: str = "arthsetu-admin"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
