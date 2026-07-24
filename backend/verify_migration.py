import sqlite3

from sqlalchemy import create_engine, text

from app.core.config import settings


# SQLite source
sqlite_conn = sqlite3.connect("lumen.db")


# PostgreSQL destination
postgres_engine = create_engine(settings.DATABASE_URL)
postgres_conn = postgres_engine.connect()


# Get application tables from SQLite
tables = [
    row[0]
    for row in sqlite_conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
          AND name != 'alembic_version'
        ORDER BY name
        """
    )
]


mismatches = []


print("=" * 60)
print("LUMEN SQLite → PostgreSQL Migration Verification")
print("=" * 60)
print()


for table in tables:

    sqlite_count = sqlite_conn.execute(
        f'SELECT COUNT(*) FROM "{table}"'
    ).fetchone()[0]

    postgres_count = postgres_conn.execute(
        text(f'SELECT COUNT(*) FROM "{table}"')
    ).scalar()

    status = "OK" if sqlite_count == postgres_count else "MISMATCH"

    print(
        f"{table:<35} "
        f"SQLite: {sqlite_count:<6} "
        f"PostgreSQL: {postgres_count:<6} "
        f"[{status}]"
    )

    if sqlite_count != postgres_count:
        mismatches.append(
            (
                table,
                sqlite_count,
                postgres_count,
            )
        )


print()
print("=" * 60)
print(f"Tables checked: {len(tables)}")
print("=" * 60)


if mismatches:

    print()
    print("MISMATCHES FOUND:")
    print()

    for table, sqlite_count, postgres_count in mismatches:
        print(
            f"{table}: "
            f"SQLite={sqlite_count}, "
            f"PostgreSQL={postgres_count}"
        )

else:

    print()
    print("SUCCESS!")
    print("ALL ROW COUNTS MATCH")
    print("SQLite and PostgreSQL contain the same data.")


sqlite_conn.close()
postgres_conn.close()
postgres_engine.dispose()