"""Configuration de l'infrastructure (variable d'environnement, .env)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Réglages du serveur, surchargeables via l'environnement (préfixe `PYOIDC_`)."""

    model_config = SettingsConfigDict(env_prefix="PYOIDC_", env_file=".env", extra="ignore")

    issuer: str = "http://localhost:8000"
    base_url: str = ""
    host: str = "127.0.0.1"
    port: int = 8000

    # JWKS (RFC 7517)
    jwks_key_size: int = 4096
    jwks_algorithm: str = "RS256"
    jwks_rotation_days: int = 90
    jwks_grace_period_days: int = 7
