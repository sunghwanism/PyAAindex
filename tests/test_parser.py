from pyaaindex._parse import parse_source_text


def test_parse_single_entry_extracts_hydrophobic_feature() -> None:
    text = ("""
H GRAR740103
D Hydrophobicity index (Grantham, 1974)
I A/L R/K N/M D/F C/P Q/S E/T G/W H/Y I/V
 1 2 3 4 5 6 7 8 9 10
 11 12 13 14 15 16 17 18 19 20
//
""").strip()

    parsed = parse_source_text(text, aaindex_type=1)
    record = parsed["GRAR740103"]

    assert record.feature == "hydrophobic"
    assert record.single_values["A"] == 1.0
    assert record.single_values["C"] == 5.0
    assert record.single_values["V"] == 20.0


def test_parse_pair_triangular_expands_symmetrically() -> None:
    text = ("""
H PAIR200001
D Pair contact energies (Example, 2026)
M rows = ACD, cols = ACD
 1 2 3 4 5 6
//
""").strip()

    parsed = parse_source_text(text, aaindex_type=2)
    record = parsed["PAIR200001"]

    as_map = {(aa1, aa2): value for aa1, aa2, value in record.pair_values}

    assert as_map[("C", "A")] == 2.0
    assert as_map[("A", "C")] == 2.0
    assert as_map[("D", "D")] == 6.0
