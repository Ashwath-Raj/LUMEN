"""
Data Store adapter — LUMEN_MASTER_SPEC_V3 §26.2.

§26.2 gives exactly four sentences of guidance, reproduced here in full
since they are the entire specification for this module:

    - Types map: INT->number, VARCHAR/TEXT->text, DATE/TIMESTAMP->datetime,
      BOOLEAN/BIT->boolean. Verify decimal handling for latitude/longitude
      before seeding — never store coordinates float-rounded; if a decimal
      type is unavailable, store as text and parse server-side.
    - Data Store enforces relationships less strictly than PostgreSQL, so
      referential integrity also lives in db/repositories/ — every write
      validates parents.
    - Seed via bulk import, not row-by-row.
    - A DATABASE_URL switch runs PostgreSQL locally and Data Store
      deployed, behind one repository interface. Both paths pass the same
      repository test suite.

What this module can honestly implement from that text: the seam itself
— a single function that resolves a backend identifier from
`DATABASE_URL` so callers (and later, a live Catalyst Data Store client)
have exactly one switch point, matching "behind one repository interface"
and "a DATABASE_URL switch runs [...] behind one repository interface."

What this module cannot implement from that text: an actual Catalyst
Data Store driver/connection. The specification gives no SDK name,
connection string format, authentication mechanism, or client library
for Data Store anywhere in the document — §26.1 names "Data Store" as
the Catalyst capability LUMEN uses for its relational database (row 6),
but nowhere specifies how to construct a live connection to it outside a
deployed Catalyst environment. Building a live Data Store connector here
would mean inventing a Catalyst SDK usage the specification does not
describe. Cannot determine a Data Store connection implementation from
the specification.

The `db/repositories/` layer (§28 structural rule 3, §26.2 rule 2) is
already backend-agnostic in the sense the spec requires: every
repository in `semantic_repositories.py` is constructed with a plain
SQLAlchemy `Session` and contains no PostgreSQL-specific SQL, so the same
repository classes run unchanged against any SQLAlchemy-compatible
engine `db/session.py` is pointed at. The "one repository interface"
requirement is satisfied by that design, not by this module — this
module's only job is to name which backend a given `DATABASE_URL` refers
to, for observability/logging purposes, since no behavioural branching
is possible without a real Data Store client to branch to.
"""
from __future__ import annotations

from typing import Literal

from lumen.config import settings

DataStoreBackend = Literal["postgresql", "sqlite", "unknown"]


def active_backend() -> DataStoreBackend:
    """Identify which backend `DATABASE_URL` currently points at.

    This is the one switch point §26.2 describes ("A DATABASE_URL switch
    runs PostgreSQL locally and Data Store deployed, behind one
    repository interface"). It does not construct a connection — that
    remains `db/session.py`'s job — and it cannot recognise a Catalyst
    Data Store URL scheme, since none is specified anywhere in the
    document. Any URL that isn't a recognised PostgreSQL/SQLite dialect
    reports `"unknown"` rather than being guessed at.
    """
    url = settings.DATABASE_URL
    if url.startswith("postgresql"):
        return "postgresql"
    if url.startswith("sqlite"):
        return "sqlite"
    return "unknown"
