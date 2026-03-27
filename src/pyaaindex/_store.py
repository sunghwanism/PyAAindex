"""In-memory store that unifies aaindex1/2/3 lookup by record id."""

from __future__ import annotations

from dataclasses import dataclass, field

from ._download import get_or_download_source
from ._models import ParsedRecord
from ._parse import parse_source_text


@dataclass(slots=True)
class AAIndexStore:
    source_texts: dict[int, str] | None = None
    _records: dict[str, ParsedRecord] | None = field(init=False, default=None)

    def get(self, target_id: str) -> ParsedRecord:
        records = self._ensure_records()
        try:
            return records[target_id]
        except KeyError as exc:
            raise KeyError(f"AAindex id '{target_id}' was not found in aaindex1/2/3") from exc

    def has(self, target_id: str) -> bool:
        return target_id in self._ensure_records()

    def _ensure_records(self) -> dict[str, ParsedRecord]:
        if self._records is None:
            self._records = self._load_all_records()
        return self._records

    def _load_all_records(self) -> dict[str, ParsedRecord]:
        combined: dict[str, ParsedRecord] = {}

        for aaindex_type in (1, 2, 3):
            if self.source_texts is not None and aaindex_type in self.source_texts:
                source_text = self.source_texts[aaindex_type]
            else:
                source_text = get_or_download_source(aaindex_type)

            parsed = parse_source_text(source_text, aaindex_type=aaindex_type)
            combined.update(parsed)

        return combined
