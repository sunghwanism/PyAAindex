"""Data structures for parsed AAindex records."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ParsedRecord:
    name: str
    feature: str
    description: str
    aaindex_type: int
    kind: str  # "single" or "pair"
    single_values: dict[str, float | None] = field(default_factory=dict)
    pair_values: list[tuple[str, str, float | None]] = field(default_factory=list)
