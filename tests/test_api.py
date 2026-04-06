import pytest
import pandas as pd
from pyaaindex.api import get_features, to_frame, get_aa_delta
from pyaaindex._store import AAIndexStore

# Mocking some small AAindex data for testing
AAINDEX1_SAMPLE = """
H GRAR740103
D Hydrophobicity index (Grantham, 1974)
I    A/L     R/K     N/M     D/F     C/P     Q/S     E/T     G/W     H/Y     I/V
      0.61   0.60   0.06   0.46   1.07   0.00   0.47   0.07   0.61   1.02
      0.61   1.15   0.78   2.02   1.95   -0.05   0.05   1.02   1.88   1.21
//
"""

AAINDEX2_SAMPLE = """
H ALTS910101
D Amino acid substitution matrices (Altschul, 1991)
M rows = AC, cols = AC
     3.0
    -3.0   12.0
//
"""

@pytest.fixture
def store():
    return AAIndexStore(
        source_texts={
            1: AAINDEX1_SAMPLE.strip(),
            2: AAINDEX2_SAMPLE.strip(),
            3: ""
        }
    )

def test_get_features_idx1(store):
    res = get_features("GRAR740103", store=store)
    df = res['idx1']
    assert isinstance(df, pd.DataFrame)
    assert "GRAR740103" in df.columns
    assert df.loc["A", "GRAR740103"] == 0.61
    assert df.loc["C", "GRAR740103"] == 1.07

def test_get_features_idx2(store):
    res = get_features("ALTS910101", store=store)
    idx2 = res['idx2']
    assert "ALTS910101" in idx2
    # Matrix for A, C
    matrix = idx2["ALTS910101"]
    assert matrix["A"] == [3.0, -3.0]
    assert matrix["C"] == [-3.0, 12.0]

def test_to_frame(store):
    res = get_features("ALTS910101", store=store)
    frames = to_frame(res['idx2'])
    df = frames["ALTS910101"]
    assert isinstance(df, pd.DataFrame)
    assert df.loc["A", "A"] == 3.0
    assert df.loc["C", "A"] == -3.0

def test_get_aa_delta(store):
    # AA=0.61, CC=1.07 -> Delta(A-C) = 0.61 - 1.07 = -0.46
    df = get_aa_delta("GRAR740103", store=store)
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (20, 20)
    assert pytest.approx(df.loc["A", "C"], 0.01) == -0.46
    assert df.loc["A", "A"] == 0.0
