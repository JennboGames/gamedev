"""Apply or roll back the plain SQL migrations in ./migrations.

Usage (from api/):  python migrate.py [up|down|status]
Reads DATABASE_URL from the environment, falling back to api/local.settings.json.
"""

import json
import os
import sys
from pathlib import Path

import psycopg2

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
SETTINGS_FILE = Path(__file__).parent / "local.settings.json"


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url and SETTINGS_FILE.exists():
        url = (
            json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            .get("Values", {})
            .get("DATABASE_URL")
        )
    if not url:
        sys.exit("DATABASE_URL is not set.")
    return url


def _versions() -> list[str]:
    return sorted(p.name.removesuffix(".up.sql") for p in MIGRATIONS_DIR.glob("*.up.sql"))


def _applied(cur) -> set[str]:  # noqa: ANN001
    cur.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
    )
    cur.execute("SELECT version FROM schema_migrations")
    return {row[0] for row in cur.fetchall()}


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "up"
    if command not in ("up", "down", "status"):
        sys.exit("Usage: python migrate.py [up|down|status]")

    connection = psycopg2.connect(_database_url())
    try:
        with connection, connection.cursor() as cur:
            applied = _applied(cur)
            versions = _versions()

            if command == "status":
                for version in versions:
                    print(f"{'applied' if version in applied else 'pending'}  {version}")
            elif command == "up":
                for version in (v for v in versions if v not in applied):
                    cur.execute((MIGRATIONS_DIR / f"{version}.up.sql").read_text(encoding="utf-8"))
                    cur.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (version,))
                    print(f"applied  {version}")
            else:
                latest = [v for v in reversed(versions) if v in applied][:1]
                for version in latest:
                    cur.execute(
                        (MIGRATIONS_DIR / f"{version}.down.sql").read_text(encoding="utf-8")
                    )
                    cur.execute("DELETE FROM schema_migrations WHERE version = %s", (version,))
                    print(f"rolled back  {version}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
