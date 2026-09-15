# Configuration du serveur

La configuration se fait par **variables d'environnement** (préfixe `PYOIDC_`) ou par
fichier **`.env`** placé à la racine du projet (chargé automatiquement au démarrage).
Elle est lue au démarrage par [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).

## Paramètres actuels

| Variable | Défaut | Description |
| --- | --- | --- |
| `PYOIDC_ISSUER` | `http://localhost:8000` | Identifiant public de l'émetteur : l'URL où le serveur est joignable. Doit être stable et, en production, en **HTTPS**. |
| `PYOIDC_BASE_URL` | *(issuer)* | Base utilisée pour construire les URL des endpoints publiées dans le document de discovery (`/authorize`, `/token`, `/userinfo`, `/.well-known/jwks.json`, …). Par défaut : l'issuer. |
| `PYOIDC_HOST` | `127.0.0.1` | Interface réseau sur laquelle écoute le serveur Uvicorn. |
| `PYOIDC_PORT` | `8000` | Port d'écoute. |
| `PYOIDC_KEY_STORE_TYPE` | `memory` | Type de stockage des clés de signature (`memory` pour le développement local, `sql` pour la production). |
| `PYOIDC_KEY_STORE_DSN` | `sqlite:///pyoidc_keys.db` | Chaîne de connexion SQLAlchemy du magasin de clés (utilisée lorsque `KEY_STORE_TYPE=sql`). |
| `PYOIDC_JWKS_KEY_SIZE` | `4096` | Taille des clés RSA générées (bits) pour la signature des jetons. |
| `PYOIDC_JWKS_ALGORITHMS` | *(tous)* | Liste (séparée par des virgules) des algorithmes de signature fournis. Supporte `RS256`, `RS384`, `RS512`, `PS256`, `PS384`, `PS512`, `ES256`, `ES384`, `ES512`. |
| `PYOIDC_JWKS_ROTATION_DAYS` | `90` | Âge à partir duquel une clé de signature est retirée du JWKS et remplacée. |
| `PYOIDC_JWKS_GRACE_PERIOD_DAYS` | `7` | Délai après la rotation avant suppression définitive de l'ancienne clé. |

### `issuer` vs `base_url`

- **`issuer`** est l'identifiant porté par les jetons émis (claim `iss`) et publié dans le
  document de discovery. C'est une valeur qui doit rester **stable dans le temps**.
- **`base_url`** est uniquement la racine de construction des URL des endpoints exposées
  dans `/.well-known/openid-configuration`. Par défaut les deux sont identiques.

### Stockage des clés et multi-instance

La variable `KEY_STORE_TYPE` définit comment les clés de signature sont persistées.
C'est le paramètre qui permet de **loadbalancer** plusieurs instances du serveur
et de reprendre après un redémarrage.

| `KEY_STORE_TYPE` | Comportement | Usage |
| --- | --- | --- |
| `memory` | Stockage en mémoire (Process-local, sans persistance) | Développement local, tests unitaires |
| `sql` | Stockage SQL via SQLAlchemy (SQLite, PostgreSQL, MySQL) | Production, load balancing multi-instance |

**Chargement de la DSN** : quand le type est `sql`, le DSN `KEY_STORE_DSN` est
réécrit automatiquement vers le dialecte asynchrone (ex. `sqlite:///keys.db` →
`sqlite+aiosqlite:///keys.db`).

### Clés RSA et ECDSA (JWKS)

- Au démarrage, une clé est générée **par algorithme configuré** et exposée sur
  `/.well-known/jwks.json` (format JWK, champs `kty`, `kid`, `use`, `alg`, plus `n`/`e`
  pour RSA, `crv`/`x`/`y` pour EC).
- `PYOIDC_JWKS_ALGORITHMS` permet de choisir les algorithmes fournis.
- La rotation est déclenchée à chaque lecture du JWKS : les clés plus vieilles que
  `rotation_days` sont retirées, les clés hors `grace_period_days` sont supprimées,
  et une nouvelle clé est générée si nécessaire.

## Exemples

### Lancement local simple (en mémoire)

```sh
PYOIDC_ISSUER=http://localhost:8000 uv run python -m pyoidc
```

### Stockage SQL pour la production

```sh
PYOIDC_ISSUER=https://id.example.com
PYOIDC_KEY_STORE_TYPE=sql
PYOIDC_KEY_STORE_DSN=postgresql+asyncpg://pyoidc:secret@db-host/pyoidc
```

### Derrière un reverse proxy TLS

```sh
PYOIDC_ISSUER=https://id.example.com uv run uvicorn pyoidc.server:app --host 127.0.0.1 --port 8000
```

## Notes d'implémentation

- Les clés privées sont stockées en texte PEM ; le repository SQL utilise une table
  `key_pairs` avec une colonne `kid` (identifiant unique, clé primaire) et une colonne
  `is_active` (booléen) pour gérer la rotation.
- Les contrats (ports) de gestion des clés (`KeyManager`) et de persistance
  (`KeyPairRepository`) sont des Protocol vivant dans `pyoidc/interfaces/` ;
  seules les implémentations `memory` et `sql` sont livrées dans cette version.
  Des implémentations Redis et MongoDB peuvent être ajoutées comme extras optionnels.
- Toutes les opérations sont asynchrones (`async/await`), compatibles avec l'event loop
  de FastAPI.
