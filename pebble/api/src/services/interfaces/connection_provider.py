from typing import Any, Protocol


class DatabaseConnectionProvider(Protocol):
    """Azure client boundary for PostgreSQL: local URL or managed-identity token."""

    def connect(self) -> Any:
        """Return a new psycopg2 connection."""
        ...
