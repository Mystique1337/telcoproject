"""Embed disk products into Pinecone via llama-text-embed-v2.

Mirrors `scripts/build_product_index.py` (which targets Chroma) but uses
the production-grade Pinecone path with asymmetric retrieval, matching
the TAM-ESCO Skills Extractor V2 architecture.

Run:
    python scripts/build_pinecone_index.py                  # incremental
    python scripts/build_pinecone_index.py --reset          # wipe + rebuild
    python scripts/build_pinecone_index.py --limit 100      # debug

Reads PINECONE_API_KEY + NPA_PINECONE_INDEX from .env.
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

from app.rag import pinecone_store

logger = logging.getLogger("build_pinecone")
PRODUCTS_DIR = PROJECT_ROOT / "data" / "sample" / "products"


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="Clear the namespace first")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--namespace", default=pinecone_store.DEFAULT_NAMESPACE)
    args = ap.parse_args()

    if not pinecone_store.pinecone_available():
        logger.error("PINECONE_API_KEY not set in .env")
        return 1

    products = _load_disk_products()
    logger.info("loaded %d products from disk", len(products))
    if not products:
        return 1
    if args.limit:
        products = products[:args.limit]

    if args.reset:
        pinecone_store.reset_namespace(args.namespace)
        import time
        time.sleep(2)  # let the delete propagate

    existing = pinecone_store.index_count(args.namespace)
    logger.info("pinecone index '%s' / ns '%s' currently has %d vectors",
                pinecone_store.PINECONE_INDEX, args.namespace, existing)

    # Resume support — skip ids already in the index (idempotent upsert is fine,
    # but skipping saves embedding tokens, which is the actual bottleneck).
    if existing > 0 and not args.reset:
        try:
            index = pinecone_store.get_product_index()
            existing_ids = set()
            # Pinecone doesn't have a cheap "list ids" — use list() if available
            from pinecone.exceptions import PineconeException
            try:
                for batch in index.list(namespace=args.namespace, limit=1000):
                    existing_ids.update(batch)
            except (AttributeError, PineconeException):
                logger.warning("could not enumerate existing ids; will rely on idempotent upsert")
            if existing_ids:
                before = len(products)
                products = [
                    p for p in products
                    if str(p.get("product_id") or p.get("title", ""))[:120] not in existing_ids
                ]
                logger.info("resume: skipping %d already-indexed; %d remaining",
                            before - len(products), len(products))
        except Exception as e:
            logger.warning("resume check failed: %s", e)

    if not products:
        logger.info("nothing to do — namespace already up to date")
        return 0

    n = pinecone_store.upsert_products(products, namespace=args.namespace)
    logger.info("✅ upserted %d products. namespace size now: %d",
                n, pinecone_store.index_count(args.namespace))
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
    sys.exit(main())
