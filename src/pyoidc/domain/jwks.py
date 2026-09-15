"""Entités et contrat de gestion des clés JWT (RFC 7517 — JSON Web Key)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Protocol
from uuid import uuid4


class KeyType(str, Enum):
    """Famille de clé cryptographique publiée dans un JWK (RFC 7518 §6)."""

    RSA = "RSA"
    EC = "EC"


class JWTAlgorithm(str, Enum):
    """Algorithmes de signature supportés (JWA RFC 7518)."""

    RS256 = "RS256"
    RS384 = "RS384"
    RS512 = "RS512"
    PS256 = "PS256"
    PS384 = "PS384"
    PS512 = "PS512"
    ES256 = "ES256"
    ES384 = "ES384"
    ES512 = "ES512"

    @property
    def key_type(self) -> KeyType:
        """Type de clé JWK (``kty``) associé à l'algorithme."""
        if self in (
            JWTAlgorithm.RS256,
            JWTAlgorithm.RS384,
            JWTAlgorithm.RS512,
            JWTAlgorithm.PS256,
            JWTAlgorithm.PS384,
            JWTAlgorithm.PS512,
        ):
            return KeyType.RSA
        return KeyType.EC

    @property
    def curve(self) -> str:
        """Courbe JWK (``crv``), vide pour les clés RSA."""
        return {
            JWTAlgorithm.ES256: "P-256",
            JWTAlgorithm.ES384: "P-384",
            JWTAlgorithm.ES512: "P-521",
        }.get(self, "")


ALL_SIGNING_ALGORITHMS: tuple[JWTAlgorithm, ...] = tuple(JWTAlgorithm)


@dataclass(frozen=True, slots=True)
class KeyPair:
    """Paire de clés pour la signature JWT, quel que soit l'algorithme.

    Les clés sont stockées au format PEM (texte) pour rester indépendantes
    de toute bibliothèque cryptographique dans le domaine.
    """

    algorithm: JWTAlgorithm
    kid: str = field(default_factory=lambda: f"{uuid4().hex[:12]}")
    private_key_pem: str = ""
    public_key_pem: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True


class KeyManager(Protocol):
    """Interface de gestion des paires de clés de signature.

    L'infrastructure fournit l'implémentation concrète (cryptography).
    """

    async def generate_key_pair(self, key_size: int, algorithm: JWTAlgorithm) -> KeyPair:
        """Génère une nouvelle paire de clés et l'ajoute au magasin."""
        ...

    async def get_active_keys(self) -> list[KeyPair]:
        """Retourne les clés encore actives (non expirées)."""
        ...

    async def mark_expired_keys(self, rotation_days: int, grace_period_days: int) -> int:
        """Passe les clés périmées en inactives, supprime celles hors grace period.

        Retourne le nombre de clés supprimées.
        """
        ...

    async def ensure_active_key(self, key_size: int, algorithm: JWTAlgorithm) -> None:
        """S'assure qu'au moins une clé active de l'algorithme existe."""
        ...
