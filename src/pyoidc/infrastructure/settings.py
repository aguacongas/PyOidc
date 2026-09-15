"""Configuration de l'infrastructure (variable d'environnement, .env)."""

from functools import cached_property
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from pyoidc.domain.jwks import ALL_SIGNING_ALGORITHMS, JWTAlgorithm


class Settings(BaseSettings):
    """Réglages du serveur, surchargeables via l'environnement (préfixe `PYOIDC_`)."""

    model_config = SettingsConfigDict(env_prefix="PYOIDC_", env_file=".env", extra="ignore")

    issuer: str = "http://localhost:8000"
    base_url: str = ""
    host: str = "127.0.0.1"
    port: int = 8000

    # JWKS (RFC 7517)
    jwks_key_size: int = 4096
    jwks_algorithms: Annotated[tuple[str, ...], NoDecode] = tuple(
        algorithm.value for algorithm in ALL_SIGNING_ALGORITHMS
    )
    jwks_rotation_days: int = 90
    jwks_grace_period_days: int = 7

    @field_validator("jwks_algorithms", mode="before")
    @classmethod
    def _split_algorithms(cls, value: object) -> object:
        """Transforme `PYOIDC_JWKS_ALGORITHMS="RS256,ES256"` en tuple."""
        if isinstance(value, str):
            return tuple(part.strip() for part in value.split(",") if part.strip())
        return value

    @field_validator("jwks_algorithms")
    @classmethod
    def _validate_algorithms(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Garantit que chaque algorithme configuré est supporté."""
        unknown = [
            name
            for name in value
            if name not in JWTAlgorithm.__members__ and name not in JWTAlgorithm._value2member_map_
        ]
        if unknown:
            raise ValueError(f"Algorithmes de signature non supportés : {', '.join(unknown)}")
        return value

    @cached_property
    def jwks_signing_algorithms(self) -> tuple[JWTAlgorithm, ...]:
        """Algorithmes de signature résolus en membres JWTAlgorithm."""
        return tuple(JWTAlgorithm(name) for name in self.jwks_algorithms)
