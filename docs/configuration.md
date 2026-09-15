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
| `PYOIDC_JWKS_KEY_SIZE` | `4096` | Taille des clés RSA générées (bits) pour la signature des jetons. |
| `PYOIDC_JWKS_ALGORITHMS` | `RS256` | Liste (séparée par des virgules) des algorithmes de signature fournis : chacun dispose de ses propres clés publiées dans le JWKS. Supporte `RS256`, `RS384`, `RS512`, `PS256`, `PS384`, `PS512`, `ES256`, `ES384`, `ES512`, `EdDSA`. |
| `PYOIDC_JWKS_ROTATION_DAYS` | `90` | Âge à partir duquel une clé de signature est retirée du JWKS et remplacée. |
| `PYOIDC_JWKS_GRACE_PERIOD_DAYS` | `7` | Délai après la rotation avant suppression définitive de l'ancienne clé en mémoire. |

### `issuer` vs `base_url`

- **`issuer`** est l'identifiant porté par les jetons émis (claim `iss`) et publié dans le
  document de discovery. C'est une valeur qui doit rester **stable dans le temps**.
- **`base_url`** est uniquement la racine de construction des URL des endpoints exposées
  dans `/.well-known/openid-configuration`. Vous n'en avez généralement pas besoin ;
  par défaut les deux sont identiques.

### Signature et rotation des clés (JWKS)

- Au démarrage, une clé est générée **par algorithme configuré** et exposée sur
  `/.well-known/jwks.json` (format JWK, champs `kty`, `kid`, `use`, `alg`, plus `n`/`e`
  pour RSA, `crv`/`x`/`y` pour EC et OKP).
- `PYOIDC_JWKS_ALGORITHMS` permet de choisir les algorithmes fournis : serveur avec
  plusieurs familles en parallèle (RSA + EC + OKP/EdDSA), chacune avec ses clés et son
  cycle de rotation propres.
- À chaque lecture du JWKS, le serveur applique la rotation :
  1. les clés plus vieilles que `rotation_days` sont retirées du JWKS ;
  2. les clés plus vieilles que `rotation_days + grace_period_days` sont supprimées
     en mémoire ;
  3. si aucune clé active ne reste pour un algorithme, une nouvelle clé est générée.
- En cas de rotation, garder les clients qui mettent en cache le JWKS à jour est de
  la responsabilité du client : prévoir un intervalle de rafraîchissement inférieur à
  `rotation_days`.

## Exemples

### Lancement local simple

```sh
PYOIDC_ISSUER=http://localhost:8000 uv run python -m pyoidc
```

### Derrière un reverse proxy TLS (production)

```sh
PYOIDC_ISSUER=https://id.example.com uv run uvicorn pyoidc.server:app --host 127.0.0.1 --port 8000
```

### Fichier `.env`

```sh
PYOIDC_ISSUER=https://id.example.com
PYOIDC_HOST=127.0.0.1
PYOIDC_PORT=8000
PYOIDC_JWKS_ALGORITHMS=RS256,ES256,ES384,EdDSA
```

## Paramètres à venir (par feature)

Au fur et à mesure de l'implémentation des features, de nouveaux réglages apparaîtront
ici :

- **Tokens** — durée de vie des access tokens / refresh tokens (rotation)
- **Clients** — enregistrement des clients OIDC et leurs autorisations
- **Persistance** — chaîne de connexion du stockage externe (SQL, Mongo…) et
  passage d'un stockage en mémoire monoprocess vers un stockage partagé

## Sécurité

- En production, l'`issuer` **doit** être une URL HTTPS : les clients vérifient l'issuer
  des jetons, et la spec impose le TLS sur les endpoints.
- `PYOIDC_HOST=127.0.0.1` par défaut : n'exposez pas le serveur directement sur
  Internet, toujours derrière un reverse proxy qui termine le TLS.