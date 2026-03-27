"""Parsing logic for aaindex1, aaindex2, and aaindex3 flat files."""

from __future__ import annotations

import re
from collections import defaultdict

from ._models import ParsedRecord
from .constants import AA_CANONICAL

_NUMERIC_RE = re.compile(r"^[+-]?(?:\d*\.\d+|\d+\.?)(?:[Ee][+-]?\d+)?$")
_PAIR_TOKEN_RE = re.compile(r"^[A-Za-z]/[A-Za-z]$")
_ROWS_RE = re.compile(r"rows\s*=\s*([A-Za-z*,\s]+?)(?:\s*,\s*cols|\s*$)", re.IGNORECASE)
_COLS_RE = re.compile(r"cols\s*=\s*([A-Za-z*,\s]+)", re.IGNORECASE)
_STOPWORDS = {
    "index",
    "matrix",
    "matrices",
    "scale",
    "scores",
    "score",
    "parameter",
    "parameters",
    "potential",
    "potentials",
    "values",
    "value",
}

_SENTINEL = object()


def parse_source_text(source_text: str, aaindex_type: int) -> dict[str, ParsedRecord]:
    records: dict[str, ParsedRecord] = {}
    for entry_lines in _split_entries(source_text):
        fields = _parse_entry_fields(entry_lines)
        name = _extract_name(fields)
        if not name:
            continue

        description = " ".join(fields.get("D", [])).strip()
        feature = _extract_feature(description)

        if aaindex_type == 1:
            single_values = _parse_single_values(fields.get("I", []))
            record = ParsedRecord(
                name=name,
                feature=feature,
                description=description,
                aaindex_type=aaindex_type,
                kind="single",
                single_values=single_values,
            )
        else:
            pair_values = _parse_pair_values(fields.get("M", []))
            record = ParsedRecord(
                name=name,
                feature=feature,
                description=description,
                aaindex_type=aaindex_type,
                kind="pair",
                pair_values=pair_values,
            )

        records[name] = record

    return records


def _split_entries(source_text: str) -> list[list[str]]:
    entries: list[list[str]] = []
    current: list[str] = []

    for raw_line in source_text.splitlines():
        line = raw_line.rstrip("\n")
        if line.strip() == "//":
            if current:
                entries.append(current)
                current = []
            continue
        if line.strip():
            current.append(line)

    if current:
        entries.append(current)

    return entries


def _parse_entry_fields(entry_lines: list[str]) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = defaultdict(list)
    last_key: str | None = None

    for line in entry_lines:
        if line.startswith(" "):
            if last_key is not None:
                fields[last_key].append(line.strip())
            continue

        key = line[0]
        value = line[1:].strip()
        fields[key].append(value)
        last_key = key

    return dict(fields)


def _extract_name(fields: dict[str, list[str]]) -> str:
    header = fields.get("H", [])
    if not header:
        return ""
    return header[0].split()[0]


def _extract_feature(description: str) -> str:
    if not description:
        return "unknown"

    head = description.split("(", 1)[0].strip().lower()
    if "hydrophob" in head:
        return "hydrophobic"

    tokens = re.findall(r"[a-z0-9]+", head)
    filtered: list[str] = []
    for token in tokens:
        token = "hydrophobic" if token.startswith("hydrophob") else token
        if token in _STOPWORDS:
            continue
        filtered.append(token)

    if not filtered:
        return "feature"

    return "_".join(filtered[:4])


def _parse_single_values(i_lines: list[str]) -> dict[str, float | None]:
    tokens: list[str] = []
    for line in i_lines:
        tokens.extend(line.split())

    pair_tokens: list[str] = []
    numeric_values: list[float | None] = []

    for token in tokens:
        if _PAIR_TOKEN_RE.match(token):
            pair_tokens.append(token.upper())
            continue

        parsed = _parse_numeric_token(token)
        if parsed is not _SENTINEL:
            numeric_values.append(parsed)

    amino_order = _parse_single_amino_order(pair_tokens)
    if len(numeric_values) < len(amino_order):
        raise ValueError("Invalid aaindex1 entry: fewer numeric values than amino-acid labels")

    values_by_aa: dict[str, float | None] = {}
    for idx, aa in enumerate(amino_order):
        values_by_aa[aa] = numeric_values[idx]

    # Guarantee a stable output order by keeping only canonical amino acids here.
    return {aa: values_by_aa.get(aa) for aa in AA_CANONICAL}


def _parse_single_amino_order(pair_tokens: list[str]) -> list[str]:
    if len(pair_tokens) >= 10:
        first_half = [token.split("/")[0] for token in pair_tokens[:10]]
        second_half = [token.split("/")[1] for token in pair_tokens[:10]]
        order = first_half + second_half
        if len(order) == len(set(order)):
            return order

    return list(AA_CANONICAL)


def _parse_pair_values(m_lines: list[str]) -> list[tuple[str, str, float | None]]:
    if not m_lines:
        return []

    merged = " ".join(m_lines)
    rows = _extract_axis_tokens(_ROWS_RE.search(merged), fallback=list(AA_CANONICAL))
    cols = _extract_axis_tokens(_COLS_RE.search(merged), fallback=list(AA_CANONICAL))

    numeric_text = _ROWS_RE.sub(" ", merged)
    numeric_text = _COLS_RE.sub(" ", numeric_text)
    raw_tokens = numeric_text.replace(",", " ").split()

    values: list[float | None] = []
    for token in raw_tokens:
        parsed = _parse_numeric_token(token)
        if parsed is not _SENTINEL:
            values.append(parsed)

    full_count = len(rows) * len(cols)
    tri_count = len(rows) * (len(rows) + 1) // 2 if len(rows) == len(cols) else -1

    if len(values) == full_count:
        return _pair_values_full(rows, cols, values)
    if len(values) == tri_count:
        return _pair_values_triangular(rows, cols, values)

    # Fallback: best-effort row-major fill with whatever values are available.
    pairs: list[tuple[str, str, float | None]] = []
    idx = 0
    for row in rows:
        for col in cols:
            if idx >= len(values):
                return pairs
            pairs.append((row, col, values[idx]))
            idx += 1
    return pairs


def _extract_axis_tokens(match: re.Match[str] | None, fallback: list[str]) -> list[str]:
    if not match:
        return fallback

    axis_raw = match.group(1)
    tokens = [char for char in axis_raw if char.isalpha() or char == "*"]
    return tokens or fallback


def _pair_values_full(
    rows: list[str], cols: list[str], values: list[float | None]
) -> list[tuple[str, str, float | None]]:
    pairs: list[tuple[str, str, float | None]] = []
    idx = 0
    for row in rows:
        for col in cols:
            pairs.append((row, col, values[idx]))
            idx += 1
    return pairs


def _pair_values_triangular(
    rows: list[str], cols: list[str], values: list[float | None]
) -> list[tuple[str, str, float | None]]:
    pairs: list[tuple[str, str, float | None]] = []
    idx = 0

    for i, row in enumerate(rows):
        for j in range(i + 1):
            value = values[idx]
            idx += 1
            col = cols[j]
            pairs.append((row, col, value))

            if i != j:
                mirrored_row = rows[j]
                mirrored_col = cols[i]
                pairs.append((mirrored_row, mirrored_col, value))

    return pairs


def _parse_numeric_token(token: str) -> float | None | object:
    cleaned = token.strip().rstrip(",")
    if not cleaned:
        return _SENTINEL

    upper = cleaned.upper()
    if upper in {"NA", "N/A", "-"}:
        return None

    if not _NUMERIC_RE.match(cleaned):
        return _SENTINEL

    return float(cleaned)
