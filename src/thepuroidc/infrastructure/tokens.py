"""Émission des jetons id_token / access_token via PyJWT.

Implémentation concrète du port ``TokenManager`` : elle s'appuie sur un
``KeyManager`` injecté pour choisir la clé de signature active et signe
le jeton avec le ``kid`` correspondant (JWS compact, RFC 7519).
"""

from __future__ import annotations

from typing import cast

import jwt as pyjwt
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from thepuroidc.domain.authorization import Scope
from thepuroidc.domain.jwks import JWTAlgorithm, KeyPair
from thepuroidc.interfaces.domain.jwks import KeyManager


class PyJWTTokenManager:
    """Crée des jetons JWT signés à l'aide de la clé de l'algorithme demandé."""

    def __init__(self, key_manager: KeyManager) -> None:
        """Injection du gestionnaire de clés (fournit la clé de signature)."""
        self._key_manager = key_manager

    async def create_id_token(
        self,
        *,
        algorithm: JWTAlgorithm,
        issuer: str,
        subject: str,
        audience: str,
        nonce: str,
        expires_at: int,
        issued_at: int,
        scopes: frozenset[Scope],
    ) -> str:
        """Construit l''id_token'' : identité ``sub`` + audience ``client_id``."""
        payload: dict[str, object] = {
            "iss": issuer,
            "sub": subject,
            "aud": audience,
            "nonce": nonce,
            "exp": expires_at,
            "iat": issued_at,
            "scope": " ".join(sorted(scope.value for scope in scopes)),
        }
        return await self._sign(algorithm, payload)

    async def create_access_token(
        self,
        *,
        algorithm: JWTAlgorithm,
        issuer: str,
        subject: str,
        audience: str,
        expires_at: int,
        issued_at: int,
        scopes: frozenset[Scope],
    ) -> str:
        """Construit l'access_token : identité ``sub`` + scopes accordés."""
        payload: dict[str, object] = {
            "iss": issuer,
            "sub": subject,
            "aud": audience,
            "exp": expires_at,
            "iat": issued_at,
            "scope": " ".join(sorted(scope.value for scope in scopes)),
        }
        return await self._sign(algorithm, payload)

    async def _sign(self, algorithm: JWTAlgorithm, payload: dict[str, object]) -> str:
        """Signe le payload avec la première clé active de l'algorithme."""
        key_pair = await self._first_active_key(algorithm)
        private_key = load_pem_private_key(key_pair.private_key_pem.encode("ascii"), None)
        return cast(
            str,
            pyjwt.encode(
                payload,
                private_key,
                algorithm=algorithm.value,
                headers={"kid": key_pair.kid},
            ),
        )

    async def _first_active_key(self, algorithm: JWTAlgorithm) -> KeyPair:
        """Retourne la première clé active de l'algorithme, en génère si besoin."""
        for key in await self._key_manager.get_active_keys():
            if key.algorithm is algorithm:
                return key
        await self._key_manager.ensure_active_key(4096, algorithm)
        for key in await self._key_manager.get_active_keys():
            if key.algorithm is algorithm:
                return key
        raise RuntimeError(f"Aucune clé active disponible pour l'algorithme {algorithm.value}")
