"""Tests de la feature JWKS (RFC 7517) — clés multi-algorithmes."""

import base64
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from pytest import raises

from pyoidc.application.jwks import JWKSetConfig, JWKSetUseCase
from pyoidc.domain.jwks import JWTAlgorithm
from pyoidc.infrastructure.jwks import RSAKeyManager
from pyoidc.infrastructure.settings import Settings
from pyoidc.server import create_app

_ISSUER = "https://id.example"
_KEY_SIZE = 2048


def test_key_manager_generates_rsa_pair() -> None:
    manager = RSAKeyManager()
    key_pair = manager.generate_key_pair(_KEY_SIZE, JWTAlgorithm.RS256)

    assert key_pair.algorithm is JWTAlgorithm.RS256
    assert key_pair.kid
    assert key_pair.private_key_pem.startswith("-----BEGIN PRIVATE KEY-----")
    assert key_pair.public_key_pem.startswith("-----BEGIN PUBLIC KEY-----")
    assert key_pair.is_active


def test_key_manager_generates_ec_pair() -> None:
    manager = RSAKeyManager()
    key_pair = manager.generate_key_pair(_KEY_SIZE, JWTAlgorithm.ES256)

    assert key_pair.algorithm is JWTAlgorithm.ES256
    assert key_pair.public_key_pem.startswith("-----BEGIN PUBLIC KEY-----")


def test_jwks_use_case_initialise_creates_one_active_key_per_algorithm() -> None:
    algorithms = (JWTAlgorithm.RS256, JWTAlgorithm.ES256, JWTAlgorithm.ES512)
    usecase = JWKSetUseCase(
        JWKSetConfig(key_size=_KEY_SIZE, algorithms=algorithms), RSAKeyManager()
    )
    usecase.initialise()

    keys = usecase.get_active_keys()
    assert len(keys) == 3
    assert {key.algorithm for key in keys} == set(algorithms)
    assert all(key.is_active for key in keys)


def test_settings_default_to_all_supported_algorithms() -> None:
    settings = Settings()

    assert settings.jwks_algorithms == tuple(algorithm.value for algorithm in JWTAlgorithm)


def test_jwks_endpoint_returns_keys_for_each_configured_algorithm() -> None:
    settings = Settings(
        issuer=_ISSUER,
        base_url=_ISSUER,
        jwks_key_size=_KEY_SIZE,
        jwks_algorithms=("RS256", "ES256"),
    )
    with TestClient(create_app(settings)) as client:
        response = client.get("/.well-known/jwks.json")

    assert response.status_code == 200
    keys = response.json()["keys"]
    assert len(keys) == 2
    by_alg = {key["alg"]: key for key in keys}
    assert set(by_alg) == {"RS256", "ES256"}
    assert by_alg["RS256"]["kty"] == "RSA"
    assert _is_valid_base64url(by_alg["RS256"]["n"])
    assert _is_valid_base64url(by_alg["RS256"]["e"])
    assert by_alg["ES256"]["kty"] == "EC"
    assert by_alg["ES256"]["crv"] == "P-256"
    assert _is_valid_base64url(by_alg["ES256"]["x"])
    assert _is_valid_base64url(by_alg["ES256"]["y"])


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
    _plant_keys(manager, JWTAlgorithm.RS256, 91, 1)
    usecase = JWKSetUseCase(
        JWKSetConfig(key_size=_KEY_SIZE, algorithms=(JWTAlgorithm.RS256,)), manager
    )

    active = usecase.get_active_keys()

    assert len(active) == 1
    assert len(manager._keys) == 2


def test_rotation_removes_expired_keys_and_regenerates_when_all_stale() -> None:
    manager = RSAKeyManager()
    _plant_keys(manager, JWTAlgorithm.RS256, 100, 98)
    usecase = JWKSetUseCase(
        JWKSetConfig(key_size=_KEY_SIZE, algorithms=(JWTAlgorithm.RS256,)), manager
    )

    active = usecase.get_active_keys()

    assert len(active) == 1
    assert len(manager._keys) == 1


def test_rotation_regenerates_a_missing_algorithm_alongside_active_others() -> None:
    manager = RSAKeyManager()
    manager.generate_key_pair(_KEY_SIZE, JWTAlgorithm.RS256)
    _plant_keys(manager, JWTAlgorithm.ES256, 100)
    usecase = JWKSetUseCase(
        JWKSetConfig(key_size=_KEY_SIZE, algorithms=(JWTAlgorithm.ES256, JWTAlgorithm.RS256)),
        manager,
    )

    active = usecase.get_active_keys()

    assert {key.algorithm for key in active} == {JWTAlgorithm.ES256, JWTAlgorithm.RS256}


def test_settings_reject_unsupported_algorithm() -> None:
    with raises(ValueError):
        Settings(jwks_algorithms=("RS256", "HS256"))


def _is_valid_base64url(value: str) -> bool:
    padded = value + "=" * (-len(value) % 4)
    base64.urlsafe_b64decode(padded)
    return True


def _plant_keys(manager: RSAKeyManager, algorithm: JWTAlgorithm, *ages_days: int) -> None:
    """Remplit le magasin avec des clés datées artificiellement (en jours)."""
    now = datetime.now(timezone.utc)
    manager._keys = [
        replace(
            manager.generate_key_pair(_KEY_SIZE, algorithm),
            created_at=now - timedelta(days=age),
        )
        for age in ages_days
    ]
