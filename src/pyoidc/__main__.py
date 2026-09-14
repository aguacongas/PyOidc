"""Point d'entrée local : `uv run python -m pyoidc`."""

import uvicorn

from pyoidc.infrastructure.settings import Settings
from pyoidc.server import create_app


def main() -> None:
    settings = Settings()
    uvicorn.run(create_app(settings), host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
