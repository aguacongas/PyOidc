"""Tests de la feature JWKS (RFC 7517)."""

import base64
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from pyoidc.application.jwks import JWKSetConfig, JWKSetUseCase
from pyoidc.infrastructure.jwks import RSAKeyManager
from pyoidc.infrastructure.settings import Settings
from pyoidc.server import create_app

_ISSUER = "https://id.example"
_ALGORITHM = "RS256"
_KEY_SIZE = 2048


def test_key_manager_generates_rsa_pair() -> None:
    manager = RSAKeyManager()
    key_pair = manager.generate_key_pair(_KEY_SIZE)

    assert key_pair.kid
    assert key_pair.private_key_pem.startswith("-----BEGIN PRIVATE KEY-----")
    assert key_pair.public_key_pem.startswith("-----BEGIN PUBLIC KEY-----")
    assert key_pair.is_active


def test_jwks_use_case_initialise_creates_an_active_key() -> None:
    usecase = JWKSetUseCase(JWKSetConfig(key_size=_KEY_SIZE, algorithm=_ALGORITHM), RSAKeyManager())
    usecase.initialise()

    keys = usecase.get_active_keys()
    assert len(keys) == 1
    assert keys[0].is_active


def test_jwks_endpoint_returns_public_keys() -> None:
    settings = Settings(
        issuer=_ISSUER,
        base_url=_ISSUER,
        jwks_key_size=_KEY_SIZE,
        jwks_algorithm=_ALGORITHM,
    )
    with TestClient(create_app(settings)) as client:
        response = client.get("/.well-known/jwks.json")

    assert response.status_code == 200
    body = response.json()
    assert "keys" in body
    assert len(body["keys"]) == 1
    key = body["keys"][0]
    assert key["kty"] == "RSA"
    assert key["alg"] == _ALGORITHM
    assert key["use"] == "sig"
    assert _is_valid_base64url(key["n"])
    assert _is_valid_base64url(key["e"])
    assert _is_valid_base64url(key["kid"])


def test_jwks_endpoint_keys_are_verifiable_with_pyjwt() -> None:
    settings = Settings(issuer=_ISSUER, base_url=_ISSUER, jwks_key_size=_KEY_SIZE)
    with TestClient(create_app(settings)) as client:
        response = client.get("/.well-known/jwks.json")

    assert response.status_code == 200
    key_set = response.json()["keys"]
    import jwt as pyjwt

    public_key = pyjwt.algorithms.RSAAlgorithm.from_jwk(key_set[0])
    assert public_key is not None


def test_discovery_advertises_jwks_uri() -> None:
    settings = Settings(issuer=_ISSUER, base_url=_ISSUER, jwks_key_size=_KEY_SIZE)
    with TestClient(create_app(settings)) as client:
        discovery = client.get("/.well-known/openid-configuration")
        jwks = client.get("/.well-known/jwks.json")

    assert discovery.status_code == 200
    assert discovery.json()["jwks_uri"] == f"{_ISSUER}/.well-known/jwks.json"
    assert jwks.status_code == 200


def test_rotation_deactivates_expired_key_and_keeps_recent() -> None:
    manager = RSAKeyManager()
    _plant_keys(manager, 91, 1)
    usecase = JWKSetUseCase(JWKSetConfig(key_size=_KEY_SIZE), manager)

    active = usecase.get_active_keys()

    assert len(active) == 1
    assert len(manager._keys) == 2


def test_rotation_removes_expired_keys_and_regenerates_when_all_stale() -> None:
    manager = RSAKeyManager()
    _plant_keys(manager, 100, 98)
    usecase = JWKSetUseCase(JWKSetConfig(key_size=_KEY_SIZE), manager)

    active = usecase.get_active_keys()

    assert len(active) == 1
    assert len(manager._keys) == 1


def _is_valid_base64url(value: str) -> bool:
    padded = value + "=" * (-len(value) % 4)
    base64.urlsafe_b64decode(padded)
    return True


def _plant_keys(manager: RSAKeyManager, *ages_days: int) -> None:
    """Remplit le magasin avec des clés datées artificiellement (en jours)."""
    now = datetime.now(timezone.utc)
    manager._keys = [
        replace(
            manager.generate_key_pair(_KEY_SIZE),
            created_at=now - timedelta(days=age),
        )
        for age in ages_days
    ]
