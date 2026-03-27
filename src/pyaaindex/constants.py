"""Project-wide constants for pyaaindex."""

from __future__ import annotations

AA_CANONICAL: tuple[str, ...] = (
    "A",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "K",
    "L",
    "M",
    "N",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "V",
    "W",
    "Y",
)

SOURCE_FILENAMES: dict[int, str] = {
    1: "aaindex1",
    2: "aaindex2",
    3: "aaindex3",
}

DEFAULT_BASE_URL = "https://www.genome.jp/ftp/db/community/aaindex"
DEFAULT_CACHE_DIRNAME = "pyaaindex"
