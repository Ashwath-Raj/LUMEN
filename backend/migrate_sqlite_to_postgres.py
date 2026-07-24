from sqlalchemy import create_engine, MetaData, text
from app.core.config import settings

# Source: SQLite
sqlite_engine = create_engine("sqlite:///./lumen.db")

# Destination: PostgreSQL
postgres_engine = create_engine(settings.DATABASE_URL)

sqlite_metadata = MetaData()
sqlite_metadata.reflect(bind=sqlite_engine)

postgres_metadata = MetaData()
postgres_metadata.reflect(bind=postgres_engine)

# Get tables, excluding Alembic's internal version table
tables = [
    table_name
    for table_name in sqlite_metadata.tables
    if table_name != "alembic_version"
]

# Sort tables according to foreign-key dependencies
sorted_tables = sqlite_metadata.sorted_tables

sorted_tables = [
    table
    for table in sorted_tables
    if table.name != "alembic_version"
]

print(f"Found {len(sorted_tables)} application tables to migrate.")

with sqlite_engine.connect() as sqlite_conn:
    with postgres_engine.begin() as postgres_conn:

        # Temporarily disable PostgreSQL foreign-key checks
        postgres_conn.execute(
            text("SET session_replication_role = replica")
        )

        total_rows = 0

        for sqlite_table in sorted_tables:
            table_name = sqlite_table.name

            if table_name not in postgres_metadata.tables:
                print(f"SKIP: {table_name} (not found in PostgreSQL)")
                continue

            postgres_table = postgres_metadata.tables[table_name]

            rows = sqlite_conn.execute(
                sqlite_table.select()
            ).mappings().all()

            if not rows:
                print(f"{table_name}: 0 rows")
                continue

            # Only insert columns that exist in PostgreSQL
            postgres_columns = {
                column.name for column in postgres_table.columns
            }

            insert_columns = [
                column
                for column in sqlite_table.columns
                if column.name in postgres_columns
            ]

            column_names = [column.name for column in insert_columns]

            for row in rows:
                data = {
                    column_name: row[column_name]
                    for column_name in column_names
                }

                postgres_conn.execute(
                    postgres_table.insert().values(**data)
                )

            total_rows += len(rows)

            print(
                f"{table_name}: {len(rows)} rows migrated"
            )

        # Re-enable PostgreSQL foreign-key checks
        postgres_conn.execute(
            text("SET session_replication_role = DEFAULT")
        )

print()
print("=" * 60)
print("MIGRATION COMPLETE")
print("=" * 60)
print(f"Total rows migrated: {total_rows}")