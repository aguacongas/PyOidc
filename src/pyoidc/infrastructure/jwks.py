"""Gestionnaire de clés RSA — implémentation concrète de ``KeyManager``."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import cast

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

from pyoidc.domain.jwks import RSAKeyPair


class RSAKeyManager:
    """Génère et stocke des paires de clés RSA en mémoire."""

    def __init__(self) -> None:
        """Initialise le magasin de clés vide."""
        self._keys: list[RSAKeyPair] = []

    def generate_key_pair(self, key_size: int) -> RSAKeyPair:
        """Génère une paire de clés RSA et l'ajoute au magasin."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            cast(Encoding, Encoding.PEM),
            cast(PrivateFormat, PrivateFormat.PKCS8),
            NoEncryption(),
        ).decode("ascii")
        public_pem = public_key.public_bytes(
            cast(Encoding, Encoding.PEM),
            cast(PublicFormat, PublicFormat.SubjectPublicKeyInfo),
        ).decode("ascii")

        key_pair = RSAKeyPair(
            private_key_pem=private_pem,
            public_key_pem=public_pem,
        )
        self._keys.append(key_pair)
        return key_pair

    def get_active_keys(self) -> list[RSAKeyPair]:
        """Retourne les clés marquées actives."""
        return [k for k in self._keys if k.is_active]

    def mark_expired_keys(self, rotation_days: int, grace_period_days: int) -> int:
        """Marque les clés expirées, supprime celles dépassant la grace period.

        Retourne le nombre de clés supprimées.
        """
        now = datetime.now(timezone.utc)
        rotation_deadline = now - timedelta(days=rotation_days)
        grace_deadline = now - timedelta(days=rotation_days + grace_period_days)
        removed = 0
        surviving: list[RSAKeyPair] = []
        for key in self._keys:
            if key.created_at <= grace_deadline:
                removed += 1
                continue
            if key.created_at <= rotation_deadline and key.is_active:
                surviving.append(replace(key, is_active=False))
            else:
                surviving.append(key)
        self._keys = surviving
        return removed

    def ensure_active_key(self, key_size: int) -> None:
        """Génère une clé si aucune clé active n'est disponible."""
        if not self.get_active_keys():
            self.generate_key_pair(key_size)
