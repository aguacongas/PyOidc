"""Repository en mémoire — implémentation de test/développement monoprocess.

Les clés ne survivent pas à la vie du processus : à utiliser pour les
tests unitaires et le développement local uniquement.
"""

from __future__ import annotations

from pyoidc.domain.jwks import KeyPair


class InMemoryKeyPairRepository:
    """Maintient les paires de clés dans un dictionnaire en mémoire."""

    def __init__(self) -> None:
        """Initialise le magasin vide."""
        self._keys: dict[str, KeyPair] = {}

    async def save(self, key_pair: KeyPair) -> None:
        """Stocke la paire de clés (insertion ou mise à jour par ``kid``)."""
        self._keys[key_pair.kid] = key_pair

    async def find_all(self) -> list[KeyPair]:
        """Retourne toutes les paires de clés, dans l'ordre d'insertion."""
        return list(self._keys.values())

    async def update(self, key_pair: KeyPair) -> None:
        """Remplace la paire de clés existante (par ``kid``)."""
        self._keys[key_pair.kid] = key_pair

    async def delete(self, kid: str) -> None:
        """Retire la paire de clés identifiée par ``kid``, ignoré si absente."""
        self._keys.pop(kid, None)

    async def initialise(self) -> None:
        """Rien à préparer : le magasin existe dès la construction."""

    async def close(self) -> None:
        """Rien à libérer."""
