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

## Download and Cache

On first call, the package downloads source files from:

- <https://www.genome.jp/ftp/db/community/aaindex/aaindex1>
- <https://www.genome.jp/ftp/db/community/aaindex/aaindex2>
- <https://www.genome.jp/ftp/db/community/aaindex/aaindex3>

Cache location:

- default: `~/.cache/pyaaindex`
- override with: `PYAAINDEX_CACHE_DIR`

## Save JSON with Filename Rule

```python
pyaaindex.to_json("PAIR200001", save=True, out_dir="./out")
```

Saved filename pattern:

- `f"{name}_{feature}_aaindex{1|2|3}.json"`
