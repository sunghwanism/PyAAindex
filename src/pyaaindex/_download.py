"""Download and cache helpers for AAindex sources."""

from __future__ import annotations

import os
from pathlib import Path
from urllib.request import urlopen

from .constants import DEFAULT_BASE_URL, DEFAULT_CACHE_DIRNAME, SOURCE_FILENAMES


def get_cache_dir() -> Path:
    override = os.getenv("PYAAINDEX_CACHE_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / ".cache" / DEFAULT_CACHE_DIRNAME


def get_or_download_source(source_number: int) -> str:
    if source_number not in SOURCE_FILENAMES:
        raise ValueError(f"Unsupported aaindex type: {source_number}")

    cache_dir = get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)

    filename = SOURCE_FILENAMES[source_number]
    path = cache_dir / filename

    if not path.exists():
        url = f"{DEFAULT_BASE_URL}/{filename}"
        if not url.startswith(("http://", "https://")):
            raise ValueError(f"Refusing to download from unsafe URL scheme: {url}")
        try:
            with urlopen(url, timeout=30) as response:  # nosec B310
                content = response.read().decode("utf-8")
        except Exception as exc:  # pragma: no cover - network failures are env-dependent
            raise RuntimeError(
                f"Failed to download {url}. "
                "Set PYAAINDEX_CACHE_DIR with pre-downloaded files if running offline."
            ) from exc
        path.write_text(content, encoding="utf-8")

    return path.read_text(encoding="utf-8")
