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

### `issuer` vs `base_url`

- **`issuer`** est l'identifiant porté par les jetons émis (claim `iss`) et publié dans le
  document de discovery. C'est une valeur qui doit rester **stable dans le temps**.
- **`base_url`** est uniquement la racine de construction des URL des endpoints exposées
  dans `/.well-known/openid-configuration`. Vous n'en avez généralement pas besoin ;
  par défaut les deux sont identiques.

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
```

## Paramètres à venir (par feature)

Au fur et à mesure de l'implémentation des features, de nouveaux réglages apparaîtront
ici :

- **JWKS** — algorithme de signature (`RS256`, `ES256`…), rotation des clés
- **Tokens** — durée de vie des access tokens / refresh tokens (rotation)
- **Clients** — enregistrement des clients OIDC et leurs autorisations
- **Persistance** — chaîne de connexion du stockage externe (SQL, Mongo…) et
  passage d'un stockage en mémoire monoprocess vers un stockage partagé

## Sécurité

- En production, l'`issuer` **doit** être une URL HTTPS : les clients vérifient l'issuer
  des jetons, et la spec impose le TLS sur les endpoints.
- `PYOIDC_HOST=127.0.0.1` par défaut : n'exposez pas le serveur directement sur
  Internet, toujours derrière un reverse proxy qui termine le TLS.