"""Populate the Chroma product index from disk products.

Embeds the 6,657 (or however many) products under data/sample/products/
into the Chroma vector store, so the recommend agent can do semantic
retrieval instead of lexical sampling.

Embedding backend (auto-picked, no API key needed by default):

    1. sentence-transformers local (default; free, ~80MB model, runs on CPU)
       — model: sentence-transformers/all-MiniLM-L6-v2
       — pip install handled by requirements.txt

    2. OpenAI text-embedding-3-small (if OPENAI_API_KEY is set)
       — pass --provider openai
       — ~$0.03 for 6,657 products

    3. NVIDIA NIM embeddings (if NVIDIA_API_KEY is set)
       — pass --provider nvidia
       — free tier

Run:
    python scripts/build_product_index.py                    # local (default)
    python scripts/build_product_index.py --provider openai  # if you prefer
    python scripts/build_product_index.py --reset            # wipe + rebuild
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from app.rag.vector_store import add_products, get_chroma_client, get_product_collection

logger = logging.getLogger("build_index")

PRODUCTS_DIR = PROJECT_ROOT / "data" / "sample" / "products"


# --------------------------------------------------------------------------- #
# Loading                                                                      #
# --------------------------------------------------------------------------- #

def _load_disk_products() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not PRODUCTS_DIR.exists():
        logger.error("missing %s — run scripts/pull_jumia_products.py first", PRODUCTS_DIR)
        return out
    for f in PRODUCTS_DIR.glob("*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            if d.get("title") and d.get("description"):
                out.append(d)
        except Exception:
            continue
    return out


# --------------------------------------------------------------------------- #
# Embedding providers                                                          #
# --------------------------------------------------------------------------- #

def _embed_sentence_transformers(texts: list[str]) -> list[list[float]]:
    """Local embeddings via sentence-transformers/all-MiniLM-L6-v2."""
    from sentence_transformers import SentenceTransformer
    logger.info("loading sentence-transformers/all-MiniLM-L6-v2 (one-time)...")
    model = SentenceTransformer("paraphrase-MiniLM-L6-v2", device="cpu")
    logger.info("encoding %d texts...", len(texts))
    embs = model.encode(texts, batch_size=64, show_progress_bar=True, convert_to_numpy=True)
    return embs.tolist()


def _embed_openai(texts: list[str]) -> list[list[float]]:
    """OpenAI text-embedding-3-small."""
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    client = OpenAI(api_key=api_key, base_url=os.getenv("OPENAI_BASE_URL") or None)
    out: list[list[float]] = []
    batch = 100
    for i in range(0, len(texts), batch):
        chunk = texts[i:i + batch]
        resp = client.embeddings.create(model="text-embedding-3-small", input=chunk)
        out.extend([e.embedding for e in resp.data])
        logger.info("  openai embedded %d/%d", min(i + batch, len(texts)), len(texts))
    return out


def _embed_nvidia(texts: list[str]) -> list[list[float]]:
    """NVIDIA NIM embeddings (free tier)."""
    from openai import OpenAI
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY not set")
    client = OpenAI(api_key=api_key, base_url="https://integrate.api.nvidia.com/v1")
    out: list[list[float]] = []
    batch = 50
    for i in range(0, len(texts), batch):
        chunk = texts[i:i + batch]
        resp = client.embeddings.create(model="nvidia/nv-embedqa-e5-v5", input=chunk)
        out.extend([e.embedding for e in resp.data])
        logger.info("  nvidia embedded %d/%d", min(i + batch, len(texts)), len(texts))
    return out


EMBEDDERS = {
    "local": _embed_sentence_transformers,
    "openai": _embed_openai,
    "nvidia": _embed_nvidia,
}


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=list(EMBEDDERS), default="local",
                    help="Embedding backend (default: local sentence-transformers)")
    ap.add_argument("--reset", action="store_true",
                    help="Drop the existing collection before indexing")
    ap.add_argument("--limit", type=int, default=None,
                    help="Embed at most this many products (debug)")
    args = ap.parse_args()

    products = _load_disk_products()
    logger.info("loaded %d products from disk", len(products))
    if not products:
        return 1
    if args.limit:
        products = products[:args.limit]
        logger.info("limited to %d for this run", len(products))

    # Optionally reset the collection (Chroma's get_or_create reuses by name)
    if args.reset:
        client = get_chroma_client()
        try:
            client.delete_collection("products_v1")
            logger.info("deleted existing 'products_v1' collection")
        except Exception:
            pass

    coll = get_product_collection()
    existing_ids = set()
    if coll.count() > 0 and not args.reset:
        try:
            existing_ids = set(coll.get(limit=20000).get("ids") or [])
        except Exception:
            pass
        logger.info("collection has %d existing items; skipping their ids", len(existing_ids))

    to_index = [p for p in products
                if (p.get("product_id") or p.get("title")) and
                   (p.get("product_id") or p.get("title")) not in existing_ids]
    if not to_index:
        logger.info("nothing new to index — collection up to date")
        return 0
    logger.info("will embed %d new products via provider=%s", len(to_index), args.provider)

    # Pad IDs / ensure shape
    for p in to_index:
        if not p.get("product_id"):
            p["product_id"] = p["title"][:60]

    # Embed
    embed_fn = EMBEDDERS[args.provider]
    texts = [f"{p['title']} — {p['category']} — {(p['description'] or '')[:800]}"
             for p in to_index]
    embeddings = embed_fn(texts)

    # Batch-add to Chroma so we don't overwhelm it on huge lists
    batch = 200
    for i in range(0, len(to_index), batch):
        add_products(to_index[i:i + batch], embeddings[i:i + batch])
    logger.info("✅ indexed %d products. collection size now: %d",
                len(to_index), coll.count())
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
    sys.exit(main())
