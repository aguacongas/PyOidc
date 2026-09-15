"""Implémentation de démonstration du port ``ClaimsProvider``.

Fournit des claims utilisateur en mémoire, issus d'un annuaire de
démonstration. Les données sont des exemples ; une vraie base
d'utilisateurs implémenterait le même port pour alimenter ``/userinfo``.
"""

from __future__ import annotations

from thepuroidc.domain.userinfo import UserClaims


class InMemoryClaimsProvider:
    """Résout les claims depuis un annuaire mémoire chargé au constructeur.

    La table ``_profiles`` mappe un ``sub`` vers son jeu de claims. Un
    sujet inconnu retourne des claims vides (seul ``sub`` est renvoyé
    ensuite par le use case).
    """

    def __init__(self, profiles: dict[str, dict[str, object]] | None = None) -> None:
        """Injection des profils (par défaut : l'annuaire de démonstration)."""
        self._profiles = profiles if profiles is not None else _DEMO_PROFILES

    def get_claims(self, subject: str) -> UserClaims:
        """Retourne les claims de l'utilisateur ``subject`` (vide si inconnu)."""
        return UserClaims(subject=subject, claims=dict(self._profiles.get(subject, {})))


_DEMO_PROFILES: dict[str, dict[str, object]] = {
    "sample-pkce-client": {
        "name": "Alice Martin",
        "family_name": "Martin",
        "given_name": "Alice",
        "middle_name": "Marie",
        "nickname": "alice",
        "preferred_username": "alice-martin",
        "profile": "https://example.com/alice-martin",
        "picture": "https://example.com/alice-martin.jpg",
        "website": "https://alice.example.com",
        "gender": "female",
        "birthdate": "1990-04-12",
        "zoneinfo": "Europe/Paris",
        "locale": "fr-FR",
        "updated_at": 1_738_000_000,
        "email": "alice.martin@example.com",
        "email_verified": True,
        "address": {
            "formatted": "12 rue de la Paix, 75002 Paris, France",
            "street_address": "12 rue de la Paix",
            "locality": "Paris",
            "postal_code": "75002",
            "country": "FR",
        },
        "phone_number": "+33142000000",
        "phone_number_verified": True,
    },
    "web-app": {
        "name": "Alice Martin",
        "family_name": "Martin",
        "given_name": "Alice",
        "preferred_username": "alice-martin",
        "email": "alice.martin@example.com",
        "email_verified": True,
        "updated_at": 1_738_000_000,
    },
}
