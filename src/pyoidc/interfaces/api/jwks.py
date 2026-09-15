"""Route FastAPI d'exposition du JSON Web Key Set (RFC 7517)."""

from __future__ import annotations

from fastapi import APIRouter

from pyoidc.application.jwks import JWKSetUseCase
from pyoidc.interfaces.schemas.jwks import JWKKeyResponse, JWKSetResponse


def jwk_set_router(usecase: JWKSetUseCase) -> APIRouter:
    """Construit le routeur FastAPI exposant les clés publiques du serveur."""
    router = APIRouter(tags=["jwks"])

    @router.get("/.well-known/jwks.json", summary="JSON Web Key Set")
    def jwk_set() -> JWKSetResponse:
        keys = [JWKKeyResponse.from_key_pair(key_pair) for key_pair in usecase.get_active_keys()]
        return JWKSetResponse(keys=keys)

    return router
