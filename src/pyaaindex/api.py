"""Public API for pyaaindex."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from ._models import ParsedRecord
from ._store import AAIndexStore
from .constants import AA_CANONICAL

_DEFAULT_STORE = AAIndexStore()


def to_frame(
    target_id: str,
    pair_format: str = "long",
    *,
    store: AAIndexStore | None = None,
) -> pd.DataFrame:
    """Return a cleaned DataFrame for an AAindex id.

    Args:
        target_id: AAindex accession id, e.g., "GRAR740103".
        pair_format: Output format for pair data (aaindex2/aaindex3). "long" or "matrix".
        store: Optional injected store (primarily for tests).
    """
    resolved_store = store or _DEFAULT_STORE
    record = resolved_store.get(target_id)

    if record.kind == "single":
        return _single_to_frame(record)
    return _pair_to_frame(record, pair_format=pair_format)


def to_json(
    target_id: str,
    pair_format: str = "long",
    orient: str = "records",
    *,
    save: bool = False,
    out_dir: str | Path = ".",
    store: AAIndexStore | None = None,
) -> str:
    """Return JSON serialized output for an AAindex id.

    When `save=True`, this also writes a JSON file with this name pattern:
    "{name}_{feature}_aaindex{1|2|3}.json"
    """
    resolved_store = store or _DEFAULT_STORE
    record = resolved_store.get(target_id)
    frame = to_frame(target_id, pair_format=pair_format, store=resolved_store)
    json_text = frame.to_json(orient=orient, force_ascii=True)

    if save:
        filename = build_output_stem(record) + ".json"
        out_path = Path(out_dir).expanduser().resolve() / filename
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json_text, encoding="utf-8")

    return json_text


def build_output_stem(record: ParsedRecord) -> str:
    safe_feature = _slugify(record.feature)
    return f"{record.name}_{safe_feature}_aaindex{record.aaindex_type}"


def _single_to_frame(record: ParsedRecord) -> pd.DataFrame:
    row: dict[str, object] = {
        "name": record.name,
        "feature": record.feature,
    }

    for aa in AA_CANONICAL:
        row[aa] = record.single_values.get(aa)

    return pd.DataFrame([row])


def _pair_to_frame(record: ParsedRecord, pair_format: str) -> pd.DataFrame:
    if pair_format not in {"long", "matrix"}:
        raise ValueError("pair_format must be either 'long' or 'matrix'")

    long_rows = [
        {
            "name": record.name,
            "feature": record.feature,
            "aa1": aa1,
            "aa2": aa2,
            "value": value,
        }
        for aa1, aa2, value in record.pair_values
    ]
    long_df = pd.DataFrame(long_rows)

    if pair_format == "long":
        return _sort_pair_long(long_df)

    matrix_df = (
        long_df.pivot_table(index="aa1", columns="aa2", values="value", aggfunc="first")
        if not long_df.empty
        else pd.DataFrame()
    )

    ordered_labels = _ordered_pair_labels(record)
    matrix_df = matrix_df.reindex(index=ordered_labels, columns=ordered_labels)
    matrix_df = matrix_df.reset_index().rename(columns={"aa1": "row"})
    matrix_df.insert(0, "feature", record.feature)
    matrix_df.insert(0, "name", record.name)
    return matrix_df


def _ordered_pair_labels(record: ParsedRecord) -> list[str]:
    labels = []
    for aa1, aa2, _ in record.pair_values:
        labels.append(aa1)
        labels.append(aa2)
    unique = list(dict.fromkeys(labels))
    canonical = [aa for aa in AA_CANONICAL if aa in unique]
    extras = [aa for aa in unique if aa not in AA_CANONICAL]
    return canonical + extras


def _sort_pair_long(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame

    ordered = [aa for aa in AA_CANONICAL if aa in set(frame["aa1"]) | set(frame["aa2"])]
    extras = sorted((set(frame["aa1"]) | set(frame["aa2"])) - set(ordered))
    categories = ordered + extras

    frame = frame.copy()
    frame["aa1"] = pd.Categorical(frame["aa1"], categories=categories, ordered=True)
    frame["aa2"] = pd.Categorical(frame["aa2"], categories=categories, ordered=True)
    return frame.sort_values(["aa1", "aa2"]).reset_index(drop=True)


def _slugify(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "_", value.strip()).strip("_")
    return token.lower() if token else "feature"
