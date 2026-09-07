"""Configuration engine (Foundation section F).

Layered configuration:
1. Environment variables / ``.env`` (this module).
2. Per-tenant settings (``platform.tenancy`` / settings table) — resolved at
   runtime by domain services.
3. Feature flags — exposed via :class:`Settings.feature_flags`.

Secrets are never hardcoded. ``.env.example`` documents required variables.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from the environment."""

    model_config = SettingsConfigDict(
        env_prefix="PAEOS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "PAEOS-FX"
    environment: str = Field(default="development")
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # --- Database ---
    database_url: str = Field(
        default="postgresql+psycopg://paeos:paeos@localhost:5432/paeos",
        description="SQLAlchemy database URL (PostgreSQL + PostGIS).",
    )
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # --- Security ---
    jwt_secret: str = Field(
        default="change-me-in-production",
        description="HMAC secret for JWT signing. MUST be overridden in prod.",
    )
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_seconds: int = 3600
    password_min_length: int = 12

    # --- Rate limiting (Phase 12; additive, disabled by default) ---
    rate_limit_enabled: bool = False
    rate_limit_per_minute: int = 600

    # --- Localization ---
    default_locale: str = "en"
    supported_locales: list[str] = Field(default_factory=lambda: ["en", "fil"])
    default_timezone: str = "Asia/Manila"
    default_currency: str = "PHP"

    # --- Jobs / cache ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Feature flags ---
    feature_flags: dict[str, bool] = Field(default_factory=dict)

    # --- Observability ---
    log_level: str = "INFO"
    log_json: bool = True

    @field_validator("environment")
    @classmethod
    def _validate_environment(cls, v: str) -> str:
        allowed = {"development", "test", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {sorted(allowed)}")
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    def feature_enabled(self, flag: str) -> bool:
        return bool(self.feature_flags.get(flag, False))

    def assert_production_safe(self) -> None:
        """Guard against insecure defaults leaking into production."""
        if self.is_production:
            if self.jwt_secret == "change-me-in-production":
                raise RuntimeError("PAEOS_JWT_SECRET must be set in production.")
            if self.debug:
                raise RuntimeError("Debug mode must be disabled in production.")
            if "paeos:paeos@localhost" in self.database_url:
                raise RuntimeError(
                    "PAEOS_DATABASE_URL must not use default credentials in production."
                )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()
