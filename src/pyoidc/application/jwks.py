"""Cas d'utilisation : gestion du JSON Web Key Set (JWKS)."""

from __future__ import annotations

from dataclasses import dataclass

from pyoidc.domain.jwks import JWTAlgorithm, KeyManager, KeyPair


@dataclass(frozen=True, slots=True)
class JWKSetConfig:
    """Paramètres de gestion des clés JWKS."""

    key_size: int = 4096
    algorithms: tuple[JWTAlgorithm, ...] = (JWTAlgorithm.RS256,)
    rotation_days: int = 90
    grace_period_days: int = 7


class JWKSetUseCase:
    """Gère le cycle de vie des clés et l'exposition du JWKS.

    S'appuie sur un ``KeyManager`` injecté pour la génération et le
    stockage des clés (Clean Architecture — pas de dépendance directe
    vers ``cryptography``). Chaque algorithme configuré possède ses
    propres clés, publiées en parallèle dans le JWKS.
    """

    def __init__(self, config: JWKSetConfig, key_manager: KeyManager) -> None:
        """Injection de la configuration et du gestionnaire de clés."""
        self._config = config
        self._key_manager = key_manager

    def initialise(self) -> None:
        """Génère une clé initiale par algorithme si le magasin est vide."""
        for algorithm in self._config.algorithms:
            self._key_manager.ensure_active_key(self._config.key_size, algorithm)

    def get_active_keys(self) -> list[KeyPair]:
        """Retourne les clés actives prêtes à être exposées dans le JWKS."""
        self._rotate_if_needed()
        return self._key_manager.get_active_keys()

    def _rotate_if_needed(self) -> None:
        """Effectue la rotation : marque les clés expirées, nettoie les obsolètes."""
        removed = self._key_manager.mark_expired_keys(
            self._config.rotation_days, self._config.grace_period_days
        )
        if removed > 0:
            for algorithm in self._config.algorithms:
                active = [
                    key for key in self._key_manager.get_active_keys() if key.algorithm is algorithm
                ]
                if not active:
                    self._key_manager.ensure_active_key(self._config.key_size, algorithm)
