"""Fondations communes aux repositories SQL (SQLAlchemy 2.0 asynchrone)."""

from __future__ import annotations

from sqlalchemy import make_url
from sqlalchemy.orm import DeclarativeBase

_ASYNC_DIALECTS = {
    "sqlite": "aiosqlite",
    "postgresql": "asyncpg",
    "mysql": "aiomysql",
}


class PersistenceBase(DeclarativeBase):
    """Base déclarative partagée par toutes les tables de persistance SQL."""


def async_dsn(dsn: str) -> str:
    """Adapte un DSN SQLAlchemy synchrone vers son dialecte asynchrone."""
    url = make_url(dsn)
    driver = _ASYNC_DIALECTS.get(url.get_backend_name())
    if driver is not None and url.drivername == url.get_backend_name():
        async_url = url.set(drivername=f"{url.get_backend_name()}+{driver}")
        return async_url.render_as_string(hide_password=False)
    return dsn
