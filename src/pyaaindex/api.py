"""Public API for pyaaindex."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pandas as pd

from ._models import ParsedRecord
from ._store import AAIndexStore
from .constants import AA_CANONICAL

_DEFAULT_STORE = AAIndexStore()


@dataclass(slots=True)
class _FrameBundle:
    payload: pd.DataFrame | list[pd.DataFrame]
    save_plan: list[tuple[str, pd.DataFrame]]


def to_frame(
    target_id: str | Sequence[str],
    pair_format: str = "long",
    *,
    save: bool = False,
    out_dir: str | Path = ".",
    store: AAIndexStore | None = None,
) -> pd.DataFrame | list[pd.DataFrame]:
    """Return cleaned DataFrame output for one or many AAindex ids.

    Behavior for list input:
    - only single-index records (aaindex1): return one merged DataFrame.
    - includes pair records (aaindex2/aaindex3): return a list of DataFrames,
      where pair records are returned as separate DataFrames.

    When `save=True`, DataFrames are stored as CSV files.
    """
    resolved_store = store or _DEFAULT_STORE
    bundle = _build_frame_bundle(target_id, pair_format=pair_format, store=resolved_store)

    if save:
        _write_csv_outputs(bundle.save_plan, out_dir=out_dir)

    return bundle.payload


def to_json(
    target_id: str | Sequence[str],
    pair_format: str = "long",
    orient: str = "records",
    *,
    save: bool = False,
    out_dir: str | Path = ".",
    store: AAIndexStore | None = None,
) -> str | list[str]:
    """Return JSON serialized output for one or many AAindex ids.

    For list input, return type follows `to_frame` semantics:
    - single merged frame -> one JSON string
    - multiple frames -> list of JSON strings
    """
    resolved_store = store or _DEFAULT_STORE
    ids, _ = _normalize_target_ids(target_id)
    bundle = _build_frame_bundle(target_id, pair_format=pair_format, store=resolved_store)

    if isinstance(bundle.payload, list):
        json_payload: str | list[str] = [
            frame.to_json(orient=orient, force_ascii=True) for frame in bundle.payload
        ]
    else:
        json_payload = bundle.payload.to_json(orient=orient, force_ascii=True)

    if save:
        if len(ids) > 1:
            _write_merged_json_output(bundle.payload, out_dir=out_dir, orient=orient)
        else:
            _write_json_outputs(bundle.save_plan, out_dir=out_dir, orient=orient)

    return json_payload


def build_output_stem(record: ParsedRecord) -> str:
    safe_feature = _slugify(record.feature)
    return f"{record.name}_{safe_feature}_aaindex{record.aaindex_type}"


def _build_frame_bundle(
    target_id: str | Sequence[str],
    *,
    pair_format: str,
    store: AAIndexStore,
) -> _FrameBundle:
    ids, is_single_input = _normalize_target_ids(target_id)

    single_items: list[tuple[ParsedRecord, pd.DataFrame]] = []
    pair_items: list[tuple[ParsedRecord, pd.DataFrame]] = []

    for one_id in ids:
        record = store.get(one_id)
        if record.kind == "single":
            single_items.append((record, _single_to_frame(record)))
            continue
        pair_items.append((record, _pair_to_frame(record, pair_format=pair_format)))

    if pair_items:
        if is_single_input and len(pair_items) == 1 and not single_items:
            record, frame = pair_items[0]
            return _FrameBundle(
                payload=frame,
                save_plan=[(build_output_stem(record), frame)],
            )

        payload_list: list[pd.DataFrame] = []
        save_plan: list[tuple[str, pd.DataFrame]] = []

        if single_items:
            merged_single = pd.concat([item[1] for item in single_items], ignore_index=True)
            payload_list.append(merged_single)
            single_name = (
                "aa_index1_result"
                if len(single_items) > 1
                else build_output_stem(single_items[0][0])
            )
            save_plan.append((single_name, merged_single))

        for record, frame in pair_items:
            payload_list.append(frame)
            save_plan.append((build_output_stem(record), frame))

        return _FrameBundle(payload=payload_list, save_plan=save_plan)

    if not single_items:
        raise ValueError("No valid target ids were provided")

    merged_single = pd.concat([item[1] for item in single_items], ignore_index=True)
    if len(single_items) > 1:
        save_stem = "aa_index1_result"
    else:
        save_stem = build_output_stem(single_items[0][0])

    return _FrameBundle(payload=merged_single, save_plan=[(save_stem, merged_single)])


def _normalize_target_ids(target_id: str | Sequence[str]) -> tuple[list[str], bool]:
    if isinstance(target_id, str):
        return [target_id], True

    normalized = [str(item) for item in target_id]
    if not normalized:
        raise ValueError("target_id list must not be empty")
    return normalized, False


def _write_csv_outputs(save_plan: list[tuple[str, pd.DataFrame]], out_dir: str | Path) -> None:
    out_path = Path(out_dir).expanduser().resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    for stem, frame in save_plan:
        frame.to_csv(out_path / f"{stem}.csv", index=False)


def _write_json_outputs(
    save_plan: list[tuple[str, pd.DataFrame]],
    out_dir: str | Path,
    orient: str,
) -> None:
    out_path = Path(out_dir).expanduser().resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    for stem, frame in save_plan:
        (out_path / f"{stem}.json").write_text(
            frame.to_json(orient=orient, force_ascii=True),
            encoding="utf-8",
        )


def _write_merged_json_output(
    payload: pd.DataFrame | list[pd.DataFrame],
    out_dir: str | Path,
    orient: str,
) -> None:
    out_path = Path(out_dir).expanduser().resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    if isinstance(payload, list):
        merged_obj = [json.loads(frame.to_json(orient=orient, force_ascii=True)) for frame in payload]
    else:
        merged_obj = json.loads(payload.to_json(orient=orient, force_ascii=True))

    (out_path / "aa_index_result.json").write_text(
        json.dumps(merged_obj, ensure_ascii=True),
        encoding="utf-8",
    )


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
