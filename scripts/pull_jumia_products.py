"""Pull real Jumia products from `Idowenst/jumia_dataset` and write product
JSONs into data/sample/products/ for the expanded eval + demo.

Strategy:
  - Stratify by category to get coverage of the major Nigerian e-commerce
    verticals (electronics, fashion, beauty, home, mobile, computing, baby,
    automotive).
  - Within each category, take the top-K by num_reviews (proxy for "real
    product people actually bought") with rating between 3.0 and 5.0 (filter
    out obvious fakes/noise).
  - Normalise to our Product schema (product_id, title, category, brand,
    price_naira, description, domain="jumia").
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from pathlib import Path

from datasets import load_dataset
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_ROOT / "data" / "sample" / "products"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger("pull_jumia")

# Categories we want representative coverage of. The dataset uses lowercase
# spaceless slugs; we map them to display-ready names.
# Per-category cap of 9999 = "take everything that passes". We want a huge,
# diverse product library so eval test sets and the demo product index have
# real Nigerian-market coverage.
TARGET_CATEGORIES: dict[str, int] = {
    "phones-and-tablets":   9999,
    "computing":            9999,
    "electronics":          9999,
    "appliances":           9999,
    "fashion":              9999,
    "health-and-beauty":    9999,
    "baby-products":        9999,
    "home-and-office":      9999,
    "gaming":               9999,
    "supermarket":          9999,
    "musical-instruments":  9999,
    "sporting-goods":       9999,  # may or may not exist in the slug list
    "automobile":           9999,
    "books-stationery":     9999,
}
# Filters relaxed to maximum inclusion. Rating filter dropped entirely so we
# capture the full 0-5 distribution (some products genuinely have low scores).
RATING_MIN, RATING_MAX = 0.0, 5.0
MIN_NUM_REVIEWS = 1       # at least one review = real product
DESCRIPTION_MIN_LEN = 40  # tighter, just to drop empty/placeholder rows


def _slugify(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9\-_ ]", "", s).strip()
    s = re.sub(r"\s+", "-", s)
    return s.upper()[:50] or "PRODUCT"


def _extract_brand(name: str) -> str | None:
    """Heuristic brand extraction — first word that looks like a known brand."""
    name = (name or "").strip()
    if not name:
        return None
    first_word = name.split(" ", 1)[0]
    # If first word is all-caps or capitalised and not a number, assume brand
    if first_word.isupper() or (first_word[0].isupper() and not first_word.isdigit()):
        return first_word
    return None


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    existing = {p.stem for p in OUT_DIR.glob("*.json")}
    logger.info("existing product files: %d", len(existing))

    logger.info("loading Idowenst/jumia_dataset (streaming)...")
    ds = load_dataset("Idowenst/jumia_dataset", split="train", streaming=True)

    # Bucket products by category, keeping only those that pass the filters.
    by_category: dict[str, list[dict]] = defaultdict(list)
    seen = 0
    for row in tqdm(ds, desc="scanning"):
        seen += 1
        if seen > 50_000:  # cap on scan to avoid all-day streaming
            break
        cat = (row.get("category") or "").lower()
        if cat not in TARGET_CATEGORIES:
            continue
        name = row.get("name") or ""
        if not name or len(name) < 5:
            continue
        rating = float(row.get("rating") or 0.0)
        if not (RATING_MIN <= rating <= RATING_MAX):
            continue
        n_rev = int(row.get("num_reviews") or 0)
        if n_rev < MIN_NUM_REVIEWS:
            continue
        desc = row.get("description") or ""
        if len(desc) < DESCRIPTION_MIN_LEN:
            continue
        by_category[cat].append({
            "name": name,
            "category": cat,
            "rating": rating,
            "num_reviews": n_rev,
            "price": float(row.get("price") or 0.0),
            "old_price": float(row.get("old_price") or 0.0),
            "description": desc,
            "discount": row.get("discount") or "",
            "seller": row.get("seller") or "",
            "product_url": row.get("product_url") or "",
        })

    logger.info("scanned %d rows, kept %d categories", seen, len(by_category))

    written, skipped_dup = 0, 0
    for cat, target in TARGET_CATEGORIES.items():
        bucket = by_category.get(cat, [])
        # Top-K by num_reviews
        bucket.sort(key=lambda r: r["num_reviews"], reverse=True)
        picks = bucket[:target]
        logger.info("  %s: %d candidates → keeping top %d", cat, len(bucket), len(picks))
        for p in picks:
            product_id = _slugify(p["name"])
            if product_id in existing:
                skipped_dup += 1
                continue
            brand = _extract_brand(p["name"])
            data = {
                "product_id": product_id,
                "title": p["name"],
                "category": cat,
                "brand": brand,
                "price_naira": int(round(p["price"])) if p["price"] else None,
                "discount": p.get("discount") or None,
                "description": p["description"][:1500],
                "seller": p.get("seller") or None,
                "source": "jumia_real",
                "domain": "jumia",
            }
            (OUT_DIR / f"{product_id}.json").write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            written += 1
            existing.add(product_id)

    logger.info("✅ wrote %d new product files (skipped %d dups)", written, skipped_dup)
    logger.info("   total products now: %d", len(list(OUT_DIR.glob('*.json'))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
