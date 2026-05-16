"""Build the Chroma product index from `Idowenst/jumia_dataset`.

Run after `make install`. Loads the HuggingFace Jumia dataset (~18.4k product records,
already with prices/ratings/descriptions), embeds the title+description, and writes
to the Chroma collection.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from typing import Any

from app.config import get_settings
from app.data.loaders import load_huggingface_jumia
from app.llm import get_llm_client
from app.rag.vector_store import add_products

logger = logging.getLogger(__name__)


async def build() -> int:
    settings = get_settings()
    if not settings.openai_api_key:
        logger.error("OPENAI_API_KEY required for embeddings — set it in .env")
        return 1

    logger.info("Loading Idowenst/jumia_dataset from HuggingFace...")
    ds = load_huggingface_jumia()
    train = ds.get("train") or next(iter(ds.values()))
    logger.info("Loaded %d records", len(train))

    products: list[dict[str, Any]] = []
    for i, row in enumerate(train):
        title = row.get("name", "")
        desc = row.get("description", "")[:1000]
        if not title:
            continue
        products.append(
            {
                "product_id": f"JUMIA-{i:06d}",
                "title": title,
                "category": row.get("category", ""),
                "description": desc,
                "domain": "jumia",
                "price_naira": float(row.get("price") or 0),
                "popularity": min(float(row.get("num_reviews") or 0) / 100, 1.0),
            }
        )

    logger.info("Embedding %d products in batches of 100...", len(products))
    client = get_llm_client(settings.embedding_model)

    batch_size = 100
    for start in range(0, len(products), batch_size):
        batch = products[start : start + batch_size]
        texts = [f"{p['title']} — {p['description']}" for p in batch]
        embeddings = await client.embed(texts)
        add_products(batch, embeddings)
        logger.info("Indexed %d / %d", start + len(batch), len(products))

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
    sys.exit(asyncio.run(build()))
