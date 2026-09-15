"""Gestionnaire de clés de signature — implémentation concrète de ``KeyManager``."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Protocol, cast

from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

from pyoidc.domain.jwks import JWTAlgorithm, KeyPair

_RSA_ALGORITHMS = (
    JWTAlgorithm.RS256,
    JWTAlgorithm.RS384,
    JWTAlgorithm.RS512,
    JWTAlgorithm.PS256,
    JWTAlgorithm.PS384,
    JWTAlgorithm.PS512,
)

_EC_ALGORITHMS = (JWTAlgorithm.ES256, JWTAlgorithm.ES384, JWTAlgorithm.ES512)

_EC_CURVES: dict[JWTAlgorithm, ec.EllipticCurve] = {
    JWTAlgorithm.ES256: ec.SECP256R1(),
    JWTAlgorithm.ES384: ec.SECP384R1(),
    JWTAlgorithm.ES512: ec.SECP521R1(),
}


class _PEMPrivateKey(Protocol):
    """Interface de sérialisation minimale d'une clé privée (toutes familles)."""

    def private_bytes(
        self,
        encoding: Encoding,
        fmt: PrivateFormat,
        encryption_algorithm: NoEncryption,
    ) -> bytes: ...

    def public_key(self) -> _PEMPublicKey: ...


class _PEMPublicKey(Protocol):
    """Interface de sérialisation minimale d'une clé publique (toutes familles)."""

    def public_bytes(
        self,
        encoding: Encoding,
        fmt: PublicFormat,
    ) -> bytes: ...


class RSAKeyManager:
    """Génère et stocke des paires de clés de signature en mémoire.

    Supporte les familles RSA (RS*, PS*), EC (ES*) et OKP (Ed25519) :
    le type de clé générée dépend de l'algorithme demandé.
    """

    def __init__(self) -> None:
        """Initialise le magasin de clés vide."""
        self._keys: list[KeyPair] = []

    def generate_key_pair(self, key_size: int, algorithm: JWTAlgorithm) -> KeyPair:
        """Génère une paire de clés pour l'algorithme et l'ajoute au magasin."""
        key_pair = _generate_key_pair(key_size, algorithm)
        self._keys.append(key_pair)
        return key_pair

    def get_active_keys(self) -> list[KeyPair]:
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
        surviving: list[KeyPair] = []
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

    def ensure_active_key(self, key_size: int, algorithm: JWTAlgorithm) -> None:
        """Génère une clé de l'algorithme si aucune clé active n'est disponible."""
        active = [k for k in self.get_active_keys() if k.algorithm is algorithm]
        if not active:
            self.generate_key_pair(key_size, algorithm)


def _generate_key_pair(key_size: int, algorithm: JWTAlgorithm) -> KeyPair:
    """Génère une paire de clés PEM adaptée à l'algorithme demandé."""
    if algorithm in _RSA_ALGORITHMS:
        pk: _PEMPrivateKey = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    elif algorithm in _EC_ALGORITHMS:
        pk = cast(_PEMPrivateKey, ec.generate_private_key(_EC_CURVES[algorithm]))
    else:
        pk = cast(_PEMPrivateKey, ed25519.Ed25519PrivateKey.generate())

    private_pem = pk.private_bytes(
        cast(Encoding, Encoding.PEM),
        cast(PrivateFormat, PrivateFormat.PKCS8),
        NoEncryption(),
    ).decode("ascii")
    public_pem = (
        pk.public_key()
        .public_bytes(
            cast(Encoding, Encoding.PEM),
            cast(PublicFormat, PublicFormat.SubjectPublicKeyInfo),
        )
        .decode("ascii")
    )

    return KeyPair(
        algorithm=algorithm,
        private_key_pem=private_pem,
        public_key_pem=public_pem,
    )
