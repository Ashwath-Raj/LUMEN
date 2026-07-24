"""
Knowledge base tables — LUMEN_MASTER_SPEC_V3 §3.6 (Session 13, §15).

Two `lumen_` tables, defined verbatim from §3.6's DDL block:

    lumen_kb_document(doc_id PK, kind, title, source, effective_from,
                      classification, checksum)
    lumen_kb_chunk(chunk_id PK, doc_id FK, ordinal, text, embedding_ref,
                   token_count)

`embedding_ref` exists per §3.6 but stays NULL in Session 13: §15.2 rule 4's
"embed via QuickML" step is the exact Session 13/14 boundary (QuickML is the
§16 orchestrator's provider and §26.1 Catalyst adoption) — refs are filled
when that lands. Nothing here embeds.

`classification` is per-document (§15.1 assigns one per corpus kind and
§15.2 rule 2 requires every chunk to carry it via its doc); the §4.2 register
row `lumen_kb_*` (INTERNAL) classifies the tables themselves.
"""
from __future__ import annotations

from sqlalchemy import Column, Date, ForeignKey, Integer, String, Text

from lumen.db.session import Base


class LumenKbDocument(Base):
    __tablename__ = "lumen_kb_document"

    doc_id = Column(String(80), primary_key=True)
    kind = Column(String(20))            # act | section | crime_taxonomy | case_brief | sop (§15.1)
    title = Column(String(300))
    source = Column(String(200))
    effective_from = Column(Date)
    classification = Column(String(20))  # PUBLIC | INTERNAL | CONFIDENTIAL (§15.1)
    checksum = Column(String(64))        # sha256 of source text — re-ingest detection (§15.2 r4)


class LumenKbChunk(Base):
    __tablename__ = "lumen_kb_chunk"

    chunk_id = Column(String(100), primary_key=True)
    doc_id = Column(String(80), ForeignKey("lumen_kb_document.doc_id"))
    ordinal = Column(Integer)
    text = Column(Text)
    embedding_ref = Column(String(120))  # NULL until QuickML embedding (Session 14+)
    token_count = Column(Integer)
