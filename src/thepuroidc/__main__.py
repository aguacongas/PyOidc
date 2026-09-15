"""Point d'entrée local : `uv run python -m thepuroidc`."""

import uvicorn

from thepuroidc.infrastructure.settings import Settings
from thepuroidc.server import create_app


def main() -> None:
    """Lance le serveur Uvicorn avec les réglages d'environnement (THEPUROIDC_*)."""
    settings = Settings()
    uvicorn.run(create_app(settings), host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
