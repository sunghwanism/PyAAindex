# PyAAindex

`pyaaindex` provides cleaned pandas DataFrames from AAindex (`aaindex1`, `aaindex2`, `aaindex3`).

## Install

```bash
pip install pyaaindex
```

## Quick Start

```python
from pyaaindex.api import get_features, to_frame

# Fetch features by ID. The package automatically resolves across aaindex1, 2, and 3.
data = get_features(["ARGP820101", "ALTS910101"])

# data['idx1'] -> single pandas.DataFrame for aaindex1 features
# data['idx2'] -> dict formatted for aaindex2 pair matrices
# data['idx3'] -> dict formatted for aaindex3 pair matrices

print(data['idx1'])
#             A     C     D     E     F  ...
# ARGP...  0.61  1.07  0.46  0.47  2.02

# Pair matrices are returned as `{feature_name: {aa1: [values]}}` where [values] are sorted alphabetically based on aa2.
print(data['idx2']['ALTS910101']['A'])
# [3.0, -3.0, 0.0, ...]

# Convert JSON array matrices to pandas DataFrames
frames = to_frame(data['idx2'])

for feature_id, df in frames.items():
    print(f"--- {feature_id} ---")
    print(df.head())
# Returns full DataFrames where rows=aa1, columns=aa2
```

## Calculating Delta Matrix (AAindex1 Differences)

You can calculate the pair-wise difference $(aa_1 - aa_2)$ for any `AAindex1` feature using the `get_aa_delta` function. This generates a $20 \times 20$ matrix (DataFrame) representing the delta of a specific amino acid feature.

```python
from pyaaindex.api import get_aa_delta

# Calculate the difference matrix for property 'ARGP820101'
delta_df = get_aa_delta("ARGP820101")

print(delta_df.shape)  # (20, 20)
print(delta_df.head())
#             A     C     D     E     F  ...
# A  0.00 -0.46  0.15  0.14 -1.41
# C  0.46  0.00  0.61  0.60 -0.95
# D -0.15 -0.61  0.00 -0.01 -1.56
# E -0.14 -0.60  0.01  0.00 -1.55
# F  1.41  0.95  1.56  1.55  0.00
```

## Output Shapes

### `idx1` (single amino-acid index)

The `idx1` key returns a single **pandas DataFrame**.
- **Index**: Canonical amino acids (`A, C, D, E, F, G, H, I, K, L, M, N, P, Q, R, S, T, V, W, Y`).
- **Columns**: The calculated feature weights.

### `idx2` and `idx3` (pair data)

The `idx2` and `idx3` keys return a **Python dictionary (JSON-friendly)**.
- **Structure**: `{feature_name: {amino_acid_1: [values]}}`
- **Sorting**: The `[values]` are strictly aligned in alphabetical order by `aa2`.

To manipulate `idx2` or `idx3` as Pandas DataFrames, pass the dictionary payload into `to_frame()`:

```python
# Convert dict -> Dict[str, pd.DataFrame]
frames = to_frame(data['idx2'])

# Process each DataFrame
for feature_id, df in frames.items():
    # 'df' contains the dataframe for 'feature_id'
    pass
```
This utility dynamically restores the alphabetical columns and assigns the index for instant usability.

## Acknowledgments

1. <https://www.genome.jp/aaindex/>
2. Kawashima, S., Pokarowski, P., Pokarowska, M., Kolinski, A., Katayama, T., and Kanehisa, M.; AAindex: amino acid index database, progress report 2008. Nucleic Acids Res. 36, D202-D205 (2008). [PMID:17998252]
