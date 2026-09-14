"""Schémas du JSON Web Key Set (RFC 7517)."""

from __future__ import annotations

import base64

from cryptography.hazmat.primitives.serialization import load_pem_public_key
from pydantic import BaseModel

from pyoidc.domain.jwks import RSAKeyPair


class JWKKeyResponse(BaseModel):
    """Clé publique RSA au format JSON Web Key (RFC 7517 §4)."""

    kty: str
    kid: str
    use: str = "sig"
    alg: str
    n: str
    e: str

    @classmethod
    def from_key_pair(cls, key_pair: RSAKeyPair, algorithm: str) -> JWKKeyResponse:
        """Convertit une paire de clés RSA (PEM) en JWK public."""
        numbers = load_pem_public_key(key_pair.public_key_pem.encode("ascii"))
        public_numbers = numbers.public_numbers()
        return cls(
            kty="RSA",
            kid=key_pair.kid,
            use="sig",
            alg=algorithm,
            n=_int_to_base64url(public_numbers.n),
            e=_int_to_base64url(public_numbers.e),
        )


class JWKSetResponse(BaseModel):
    """Jeu de clés JWK (RFC 7517 §5)."""

    keys: list[JWKKeyResponse]


def _int_to_base64url(value: int) -> str:
    """Encode un entier non signé en base64url (RFC 7515 §6.1)."""
    byte_length = max(1, (value.bit_length() + 7) // 8)
    return base64.urlsafe_b64encode(value.to_bytes(byte_length, "big")).rstrip(b"=").decode("ascii")
