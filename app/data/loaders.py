"""Dataset loaders.

Sources supported:
- HuggingFace Datasets (`Idowenst/jumia_dataset` — products with ratings, no review text)
- Local parquet / CSV / JSONL
- Bundled sample files in `data/sample/`
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Iterator

logger = logging.getLogger(__name__)


def load_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    """Yield records from a JSONL file."""
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def load_huggingface_jumia() -> Any:
    """Load `Idowenst/jumia_dataset` from HuggingFace Datasets.

    NOTE: This dataset has product metadata + aggregate ratings + review COUNTS but
    NO individual review text. We use it for the product index (Task 2) and supplement
    with directly-scraped reviews + synthetic for Task 1 fine-tuning.
    """
    from datasets import load_dataset  # local import — heavy dep

    logger.info("loading Idowenst/jumia_dataset from HuggingFace")
    return load_dataset("Idowenst/jumia_dataset")


def load_sample_personas(sample_dir: Path) -> list[dict[str, Any]]:
    """Load the 5 Nigerian persona archetypes bundled in `data/sample/personas/`."""
    personas: list[dict[str, Any]] = []
    for f in sorted(sample_dir.glob("*.json")):
        try:
            personas.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001
            logger.warning("could not parse %s", f)
    return personas
