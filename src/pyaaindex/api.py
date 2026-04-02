"""Public API for pyaaindex."""

from __future__ import annotations

import pandas as pd

from ._models import ParsedRecord
from ._store import AAIndexStore
from .constants import AA_CANONICAL

_DEFAULT_STORE = AAIndexStore()


def _ordered_pair_labels(record: ParsedRecord) -> list[str]:
    labels = []
    for aa1, aa2, _ in record.pair_values:
        labels.append(aa1)
        labels.append(aa2)
    unique = list(dict.fromkeys(labels))
    canonical = [aa for aa in AA_CANONICAL if aa in unique]
    extras = [aa for aa in unique if aa not in AA_CANONICAL]
    return canonical + extras


def get_features(feature_names: str | list[str], store: AAIndexStore | None = None) -> dict:
    """Fetch AAindex data for one or multiple target IDs and return as structured dictionary format.
    
    Returns a dictionary structured as:
    {
        'idx1': pandas.DataFrame,
        'idx2': dict (JSON format),
        'idx3': dict (JSON format)
    }
    """
    if isinstance(feature_names, str):
        feature_names = [feature_names]

    resolved_store = store or _DEFAULT_STORE

    idx1_records = []
    idx2_records = []
    idx3_records = []

    for f in feature_names:
        record = resolved_store.get(f)
        if record.aaindex_type == 1:
            idx1_records.append(record)
        elif record.aaindex_type == 2:
            idx2_records.append(record)
        elif record.aaindex_type == 3:
            idx3_records.append(record)

    result = {'idx1': None, 'idx2': None, 'idx3': None}

    # Process idx1 (DataFrame of single AA values)
    if idx1_records:
        df_dict = {}
        for record in idx1_records:
            df_dict[record.name] = [record.single_values.get(aa) for aa in AA_CANONICAL]
        
        df1 = pd.DataFrame(df_dict, index=AA_CANONICAL)
        result['idx1'] = df1

    # Process idx2 (Dictionary of pairs)
    if idx2_records:
        json2 = {}
        for record in idx2_records:
            labels = _ordered_pair_labels(record)
            labels_sorted = sorted(labels)
            print(f"[get_features] Alignment order for {record.name} (AAindex2): {labels_sorted}")
            
            matrix = {aa1: {aa2: None for aa2 in labels_sorted} for aa1 in labels_sorted}
            for aa1, aa2, value in record.pair_values:
                matrix[aa1][aa2] = value
                
            json_inner = {aa1: [matrix[aa1][aa2] for aa2 in labels_sorted] for aa1 in labels_sorted}
            json2[record.name] = json_inner
        result['idx2'] = json2

    # Process idx3 (Dictionary of pairs)
    if idx3_records:
        json3 = {}
        for record in idx3_records:
            labels = _ordered_pair_labels(record)
            labels_sorted = sorted(labels)
            print(f"[get_features] Alignment order for {record.name} (AAindex3): {labels_sorted}")
            
            matrix = {aa1: {aa2: None for aa2 in labels_sorted} for aa1 in labels_sorted}
            for aa1, aa2, value in record.pair_values:
                matrix[aa1][aa2] = value
                
            json_inner = {aa1: [matrix[aa1][aa2] for aa2 in labels_sorted] for aa1 in labels_sorted}
            json3[record.name] = json_inner
        result['idx3'] = json3

    return result


def to_frame(json_data: dict) -> dict[str, pd.DataFrame]:
    """Convert AAindex2/AAindex3 json outputs to a dict of DataFrames."""
    result = {}
    for feature_name, matrix_dict in json_data.items():
        sorted_labels = sorted(matrix_dict.keys())
        df = pd.DataFrame.from_dict(matrix_dict, orient='index', columns=sorted_labels)
        result[feature_name] = df
    return result
