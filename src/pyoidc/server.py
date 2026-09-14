"""Composition root — câblage de l'application FastAPI et injection des dépendances."""

from fastapi import FastAPI

from pyoidc.application.discovery import DiscoveryConfig, DiscoveryUseCase
from pyoidc.infrastructure.settings import Settings
from pyoidc.interfaces.api.discovery import discovery_router

_PACKAGE_VERSION = "0.1.0"


def create_app(settings: Settings | None = None) -> FastAPI:
    """Assemble l'application FastAPI ; câble les usecases avec les réglages fournis."""
    settings = settings if settings is not None else Settings()
    config = DiscoveryConfig(issuer=settings.issuer, base_url=settings.base_url)

    app = FastAPI(
        title="PyOidc",
        version=_PACKAGE_VERSION,
        description="Serveur OpenID Connect conforme aux specs OIDC Core 1.0.",
    )
    app.include_router(discovery_router(DiscoveryUseCase(config)))
    return app


app = create_app()
