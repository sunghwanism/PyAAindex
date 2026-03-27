# PyAAindex

`pyaaindex` provides cleaned pandas DataFrames from AAindex (`aaindex1`, `aaindex2`, `aaindex3`).

## Install

```bash
pip install pyaaindex
```

## Quick Start

```python
import pyaaindex

# The package automatically finds the id across aaindex1/2/3
# (you do not need to specify which source file it belongs to).
target_id = "GRAR740103"
df = pyaaindex.to_frame(target_id)

# JSON serialization
payload = pyaaindex.to_json(target_id)

# CSV save
pyaaindex.to_frame(target_id, save=True, out_dir="./out")
```

## Output Shapes

### `aaindex1` (single amino-acid index)

Returns one-row wide DataFrame:

- `name`
- `feature`
- `A, C, D, E, F, G, H, I, K, L, M, N, P, Q, R, S, T, V, W, Y`

### `aaindex2` / `aaindex3` (pair data)

Default: long format with columns:

- `name`
- `feature`
- `aa1`
- `aa2`
- `value`

Optional matrix output:

```python
df_matrix = pyaaindex.to_frame("PAIR_ID", pair_format="matrix")
```

## Multiple Inputs

```python
# 1) only aaindex1 ids -> one merged DataFrame
single_df = pyaaindex.to_frame(["GRAR740103", "EXMP000002"])

# 2) includes pair ids -> list of DataFrames
frames = pyaaindex.to_frame(["GRAR740103", "PAIR200001", "PAIR300001"])
```

Rules:

- If pair ids are included (`aaindex2/3`), pair outputs are returned as separate DataFrames.
- Non-pair ids (`aaindex1`) are merged into one DataFrame.

## Download and Cache

On first call, the package downloads source files from:

- <https://www.genome.jp/ftp/db/community/aaindex/aaindex1>
- <https://www.genome.jp/ftp/db/community/aaindex/aaindex2>
- <https://www.genome.jp/ftp/db/community/aaindex/aaindex3>

Cache location:

- default: `~/.cache/pyaaindex`
- override with: `PYAAINDEX_CACHE_DIR`

## Save File Naming Rules

```python
pyaaindex.to_frame(["GRAR740103", "EXMP000002"], save=True, out_dir="./out")
pyaaindex.to_frame(["GRAR740103", "PAIR200001"], save=True, out_dir="./out")
pyaaindex.to_json(["GRAR740103", "PAIR200001"], save=True, out_dir="./out")
```

CSV/JSON filename rules:

- One merged `aaindex1` DataFrame with multiple rows: `aa_index1_result.csv` (and `aa_index1_result.json` for `to_json`)
- Pair outputs: `f"{name}_{feature}_aaindex{1|2|3}.csv"` (or `.json`)
