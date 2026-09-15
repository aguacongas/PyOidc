"""Fabrique des repositories de clés — choisit l'implémentation selon la configuration."""

from __future__ import annotations

from pyoidc.infrastructure.settings import Settings
from pyoidc.interfaces.repositories.key_pair_repository import KeyPairRepository


def build_key_pair_repository(settings: Settings) -> KeyPairRepository:
    """Retourne le repository de clés correspondant à ``key_store_type``."""
    if settings.key_store_type == "memory":
        from pyoidc.infrastructure.persistence.memory import InMemoryKeyPairRepository

        return InMemoryKeyPairRepository()
    if settings.key_store_type == "sql":
        from pyoidc.infrastructure.persistence.sql import SQLKeyPairRepository

        return SQLKeyPairRepository(settings.key_store_dsn)
    raise ValueError(f"Type de stockage de clés non supporté : {settings.key_store_type}")
