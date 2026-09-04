from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_SECRET_KEY = "dev-insecure-change-me-in-production"
_INSECURE_BOOTSTRAP_PASSWORD = "arthsetu-admin"


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

    # Background jobs normally run on a worker thread pool. Tests (and any
    # environment that wants deterministic, synchronous execution) set this
    # to run jobs inline on the submitting thread instead.
    JOBS_SYNC: bool = False
    JOBS_MAX_WORKERS: int = 2

    # --- Auth -------------------------------------------------------------
    # MUST be overridden in any non-local environment. Generate with:
    #   python -c "import secrets; print(secrets.token_urlsafe(48))"
    SECRET_KEY: str = _INSECURE_SECRET_KEY
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # First-run bootstrap admin (created by the seeder / on empty user table).
    BOOTSTRAP_ADMIN_USERNAME: str = "admin"
    BOOTSTRAP_ADMIN_PASSWORD: str = _INSECURE_BOOTSTRAP_PASSWORD

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @model_validator(mode="after")
    def _refuse_insecure_production_config(self) -> "Settings":
        """Fail fast rather than silently serve a production deployment
        with the dev SECRET_KEY or bootstrap admin password still in place."""
        if self.APP_ENV.lower() == "production":
            if self.SECRET_KEY == _INSECURE_SECRET_KEY:
                raise ValueError(
                    "SECRET_KEY must be overridden when APP_ENV=production "
                    "(python -c \"import secrets; print(secrets.token_urlsafe(48))\")"
                )
            if self.BOOTSTRAP_ADMIN_PASSWORD == _INSECURE_BOOTSTRAP_PASSWORD:
                raise ValueError(
                    "BOOTSTRAP_ADMIN_PASSWORD must be overridden when APP_ENV=production"
                )
        return self


settings = Settings()
