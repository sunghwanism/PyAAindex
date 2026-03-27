from pathlib import Path

from pyaaindex import to_frame, to_json
from pyaaindex._store import AAIndexStore
from pyaaindex.constants import AA_CANONICAL


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _build_store() -> AAIndexStore:
    return AAIndexStore(
        source_texts={
            1: (FIXTURE_DIR / "aaindex1_sample.txt").read_text(encoding="utf-8"),
            2: (FIXTURE_DIR / "aaindex2_sample.txt").read_text(encoding="utf-8"),
            3: (FIXTURE_DIR / "aaindex3_sample.txt").read_text(encoding="utf-8"),
        }
    )


def test_to_frame_single_is_wide_with_stable_amino_order() -> None:
    store = _build_store()
    df = to_frame("GRAR740103", store=store)

    expected_columns = ["name", "feature", *AA_CANONICAL]
    assert list(df.columns) == expected_columns
    assert df.loc[0, "name"] == "GRAR740103"
    assert df.loc[0, "feature"] == "hydrophobic"
    assert df.loc[0, "A"] == 1.0
    assert df.loc[0, "C"] == 5.0


def test_to_frame_pair_auto_resolves_source_and_returns_long() -> None:
    store = _build_store()
    df = to_frame("PAIR200001", store=store)

    assert list(df.columns) == ["name", "feature", "aa1", "aa2", "value"]

    data = {(str(r.aa1), str(r.aa2)): r.value for r in df.itertuples(index=False)}
    assert data[("A", "C")] == 2.0
    assert data[("D", "C")] == 5.0


def test_to_json_can_save_with_required_filename_pattern(tmp_path: Path) -> None:
    store = _build_store()
    payload = to_json("PAIR200001", save=True, out_dir=tmp_path, store=store)

    matches = list(tmp_path.glob("PAIR200001_*_aaindex2.json"))
    assert len(matches) == 1

    saved_text = matches[0].read_text(encoding="utf-8")
    assert saved_text == payload
    assert isinstance(payload, str)
    assert payload.startswith("[")


def test_to_frame_pair_matrix_format() -> None:
    store = _build_store()
    df = to_frame("PAIR300001", pair_format="matrix", store=store)

    assert "name" in df.columns
    assert "feature" in df.columns
    assert "Y" in df.columns
    assert "W" in df.columns


def test_to_frame_list_of_single_ids_returns_one_merged_dataframe() -> None:
    store = _build_store()
    df = to_frame(["GRAR740103", "EXMP000002"], store=store)

    assert df.shape[0] == 2
    assert list(df.columns) == ["name", "feature", *AA_CANONICAL]
    assert list(df["name"]) == ["GRAR740103", "EXMP000002"]


def test_to_frame_list_with_pairs_returns_multiple_dataframes() -> None:
    store = _build_store()
    frames = to_frame(["GRAR740103", "PAIR200001", "PAIR300001"], store=store)

    assert isinstance(frames, list)
    assert len(frames) == 3
    assert set(frames[0].columns) >= {"name", "feature", "A", "C"}
    assert set(frames[1].columns) == {"name", "feature", "aa1", "aa2", "value"}
    assert set(frames[2].columns) == {"name", "feature", "aa1", "aa2", "value"}


def test_to_frame_list_single_save_uses_aa_index1_result_filename(tmp_path: Path) -> None:
    store = _build_store()
    to_frame(["GRAR740103", "EXMP000002"], save=True, out_dir=tmp_path, store=store)

    assert (tmp_path / "aa_index1_result.csv").exists()


def test_to_frame_list_mixed_save_writes_grouped_and_pair_files(tmp_path: Path) -> None:
    store = _build_store()
    to_frame(["GRAR740103", "EXMP000002", "PAIR200001"], save=True, out_dir=tmp_path, store=store)

    assert (tmp_path / "aa_index1_result.csv").exists()
    pair_files = list(tmp_path.glob("PAIR200001_*_aaindex2.csv"))
    assert len(pair_files) == 1


def test_to_json_list_with_pairs_returns_json_list() -> None:
    store = _build_store()
    payload = to_json(["GRAR740103", "PAIR200001"], store=store)

    assert isinstance(payload, list)
    assert len(payload) == 2
    assert payload[0].startswith("[")
    assert payload[1].startswith("[")
