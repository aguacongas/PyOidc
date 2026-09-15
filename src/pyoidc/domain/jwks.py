"""Entités de gestion des clés JWT (RFC 7517 — JSON Web Key)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class RSAKeyPair:
    """Paire de clés RSA pour la signature JWT.

    Les clés sont stockées au format PEM (texte) pour rester indépendantes
    de toute bibliothèque cryptographique dans le domaine.
    """

    kid: str = field(default_factory=lambda: f"{uuid4().hex[:12]}")
    private_key_pem: str = ""
    public_key_pem: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True


class KeyManager(Protocol):
    """Interface de gestion des paires de clés RSA.

    L'infrastructure fournit l'implémentation concrète (cryptography).
    """

    def generate_key_pair(self, key_size: int) -> RSAKeyPair:
        """Génère une nouvelle paire de clés RSA et l'ajoute au magasin."""
        ...

    def get_active_keys(self) -> list[RSAKeyPair]:
        """Retourne les clés encore actives (non expirées)."""
        ...

    def mark_expired_keys(self, rotation_days: int, grace_period_days: int) -> int:
        """Passe les clés périmées en inactives, supprime celles hors grace period.

        Retourne le nombre de clés supprimées.
        """
        ...

    def ensure_active_key(self, key_size: int) -> None:
        """S'assure qu'au moins une clé active existe ; en génère une si besoin."""
        ...
