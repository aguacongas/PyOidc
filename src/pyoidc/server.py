"""Composition root — câblage de l'application FastAPI et injection des dépendances."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from pyoidc.application.discovery import DiscoveryConfig, DiscoveryUseCase
from pyoidc.application.jwks import JWKSetConfig, JWKSetUseCase
from pyoidc.infrastructure.jwks import RSAKeyManager
from pyoidc.infrastructure.settings import Settings
from pyoidc.interfaces.api.discovery import discovery_router
from pyoidc.interfaces.api.jwks import jwk_set_router

_PACKAGE_VERSION = "0.1.0"


def create_app(settings: Settings | None = None) -> FastAPI:
    """Assemble l'application FastAPI ; câble les usecases avec les réglages fournis."""
    settings = settings if settings is not None else Settings()
    config = DiscoveryConfig(issuer=settings.issuer, base_url=settings.base_url)

    key_manager = RSAKeyManager()
    jwks_config = JWKSetConfig(
        key_size=settings.jwks_key_size,
        algorithm=settings.jwks_algorithm,
        rotation_days=settings.jwks_rotation_days,
        grace_period_days=settings.jwks_grace_period_days,
    )
    jwks_usecase = JWKSetUseCase(jwks_config, key_manager)

    @asynccontextmanager
    async def _lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
        """Génère la clé initiale au démarrage du serveur."""
        jwks_usecase.initialise()
        yield

    app = FastAPI(
        title="PyOidc",
        version=_PACKAGE_VERSION,
        description="Serveur OpenID Connect conforme aux specs OIDC Core 1.0.",
        lifespan=_lifespan,
    )
    app.include_router(discovery_router(DiscoveryUseCase(config)))
    app.include_router(jwk_set_router(jwks_usecase, settings.jwks_algorithm))
    return app


app = create_app()
