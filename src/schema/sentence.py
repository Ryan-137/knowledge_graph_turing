from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentRecord:
    doc_id: str
    source_id: str
    title: str
    tier: int
    language: str
    clean_text: str
