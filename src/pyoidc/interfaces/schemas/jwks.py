"""Schémas du JSON Web Key Set (RFC 7517)."""

from __future__ import annotations

import base64
from typing import cast

from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    PublicFormat,
    load_pem_public_key,
)
from pydantic import BaseModel

from pyoidc.domain.jwks import JWTAlgorithm, KeyPair


class JWKKeyResponse(BaseModel):
    """Clé publique au format JSON Web Key (RFC 7517 §4).

    Les champs présents dépendent de la famille de clé : ``n``/``e`` pour
    RSA, ``crv``/``x``/``y`` pour EC et OKP.
    """

    kty: str
    kid: str
    use: str = "sig"
    alg: str
    crv: str | None = None
    n: str | None = None
    e: str | None = None
    x: str | None = None
    y: str | None = None

    @classmethod
    def from_key_pair(cls, key_pair: KeyPair) -> JWKKeyResponse:
        """Convertit une paire de clés (PEM) en JWK public."""
        public_key = load_pem_public_key(key_pair.public_key_pem.encode("ascii"))

        common = {
            "kty": key_pair.algorithm.key_type.value,
            "kid": key_pair.kid,
            "use": "sig",
            "alg": key_pair.algorithm.value,
        }
        if isinstance(public_key, rsa.RSAPublicKey):
            common.update(
                n=_int_to_base64url(public_key.public_numbers().n),
                e=_int_to_base64url(public_key.public_numbers().e),
            )
        elif isinstance(public_key, ec.EllipticCurvePublicKey):
            number = public_key.public_numbers()
            common.update(
                crv=_crv_for(key_pair.algorithm),
                x=_int_to_base64url(number.x),
                y=_int_to_base64url(number.y),
            )
        elif isinstance(public_key, ed25519.Ed25519PublicKey):
            raw = public_key.public_bytes(
                cast(Encoding, Encoding.Raw),
                cast(PublicFormat, PublicFormat.Raw),
            )
            common.update(
                crv=_crv_for(key_pair.algorithm),
                x=_to_base64url(raw),
            )
        return cls(**common)


class JWKSetResponse(BaseModel):
    """Jeu de clés JWK (RFC 7517 §5)."""

    keys: list[JWKKeyResponse]


def _crv_for(algorithm: JWTAlgorithm) -> str:
    """Retourne la courbe JWK associée à un algorithme EC/OKP."""
    return algorithm.curve


def _int_to_base64url(value: int) -> str:
    """Encode un entier non signé en base64url (RFC 7515 §6.1)."""
    byte_length = max(1, (value.bit_length() + 7) // 8)
    return _to_base64url(value.to_bytes(byte_length, "big"))


def _to_base64url(value: bytes) -> str:
    """Encode des octets en base64url sans padding (RFC 7515 §6.1)."""
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")
