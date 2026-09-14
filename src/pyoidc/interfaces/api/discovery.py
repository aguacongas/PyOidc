"""Route FastAPI d'exposition des métadonnées OpenID Connect Discovery."""

from fastapi import APIRouter

from pyoidc.application.discovery import DiscoveryUseCase
from pyoidc.interfaces.schemas.discovery import DiscoveryDocument


def discovery_router(usecase: DiscoveryUseCase) -> APIRouter:
    router = APIRouter(tags=["discovery"])

    @router.get("/.well-known/openid-configuration", summary="OpenID Connect Discovery")
    def openid_configuration() -> DiscoveryDocument:
        return DiscoveryDocument(**usecase.execute())

    return router
