"""Generate diverse Nigerian personas via OpenAI gpt-4o-mini.

Takes a demographic matrix and generates one persona per cell, calibrated to:
  - region (NW / NE / NC / SW / SE / SS — Nigeria's 6 geopolitical zones)
  - age band (Gen Z 18-25 / Millennial 26-40 / Gen X 41-55 / Boomer 55+)
  - register tier (nigerian_pidgin / code_mixed / nigerian_english / standard_english)
  - income band (lower / middle / upper-middle / high)
  - occupation archetype (trader / professional / student / civil_servant / tech / agriculture / healthcare / creative)
  - religion (christian / muslim / traditional)

Output: one JSON file per persona under data/sample/personas/.

Free tier note: gpt-4o-mini is ~$0.15 / 1M input tokens. Each persona is ~800
output tokens. 19 personas = ~15k tokens output ≈ $0.01. Trivial.

Run:
  python scripts/generate_personas.py --n 19
  python scripts/generate_personas.py --dry-run   # show matrix, write nothing
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from openai import OpenAI

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")
logger = logging.getLogger("gen_personas")

OUT_DIR = PROJECT_ROOT / "data" / "sample" / "personas"

# Provider preference: NIM (free) → OpenAI → Anthropic (paid fallback).
# Set via env: PROVIDER=nvidia|openai|anthropic.
PROVIDER = os.getenv("PERSONA_GEN_PROVIDER", "auto")
# Verified NIM model IDs (see app/llm/client.py + notebooks/01_build_corpus.ipynb).
NIM_MODEL = os.getenv("NIM_MODEL", "nvidia/llama-3.1-nemotron-70b-instruct")
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"


# Hand-picked demographic cells covering the diversity we want. Each cell is
# a tuple of strings the LLM fills in around.
PERSONA_SPECS: list[dict[str, str]] = [
    # Gen Z / Pidgin / SW / urban
    {"name": "kelechi_lagos", "region": "South-West (Lagos)", "age_band": "Gen Z (22)",
     "register_tier": "nigerian_pidgin", "income": "lower-middle (₦80k/mo)",
     "occupation": "ride-hailing driver (Bolt + uber)", "religion": "christian (pentecostal)"},
    {"name": "amaka_anambra", "region": "South-East (Onitsha, Anambra)", "age_band": "Gen Z (24)",
     "register_tier": "code_mixed", "income": "middle (₦150k/mo)",
     "occupation": "Instagram fashion vendor + content creator", "religion": "christian (catholic)"},
    {"name": "fatima_sokoto", "region": "North-West (Sokoto)", "age_band": "Gen Z (20)",
     "register_tier": "nigerian_english", "income": "lower (₦40k/mo allowance)",
     "occupation": "ABU undergraduate (medicine, year 3)", "religion": "muslim (sunni)"},
    {"name": "deborah_calabar", "region": "South-South (Calabar)", "age_band": "Gen Z (23)",
     "register_tier": "code_mixed", "income": "lower-middle (₦90k/mo)",
     "occupation": "nail tech + freelance MUA", "religion": "christian (pentecostal)"},

    # Millennial / various
    {"name": "ngozi_enugu", "region": "South-East (Enugu)", "age_band": "Millennial (32)",
     "register_tier": "nigerian_english", "income": "upper-middle (₦650k/mo)",
     "occupation": "bank operations officer (Access Bank)", "religion": "christian (anglican)"},
    {"name": "musa_kaduna", "region": "North-West (Kaduna)", "age_band": "Millennial (35)",
     "register_tier": "nigerian_english", "income": "middle (₦220k/mo)",
     "occupation": "secondary school physics teacher", "religion": "muslim (sunni)"},
    {"name": "tobi_ibadan", "region": "South-West (Ibadan)", "age_band": "Millennial (29)",
     "register_tier": "code_mixed", "income": "upper-middle (₦800k/mo)",
     "occupation": "fintech product manager (Lagos-based remote)", "religion": "christian (pentecostal)"},
    {"name": "blessing_warri", "region": "South-South (Warri, Delta)", "age_band": "Millennial (34)",
     "register_tier": "nigerian_pidgin", "income": "middle (₦180k/mo)",
     "occupation": "petty trader (cosmetics + mobile accessories)", "religion": "christian (pentecostal)"},
    {"name": "ibrahim_maiduguri", "region": "North-East (Maiduguri, Borno)", "age_band": "Millennial (38)",
     "register_tier": "nigerian_english", "income": "middle (₦200k/mo)",
     "occupation": "NGO logistics coordinator (IDP camps)", "religion": "muslim (sunni)"},
    {"name": "ada_owerri", "region": "South-East (Owerri)", "age_band": "Millennial (31)",
     "register_tier": "code_mixed", "income": "middle (₦170k/mo)",
     "occupation": "nurse (public hospital)", "religion": "christian (catholic)"},

    # Gen X
    {"name": "olumide_lagos", "region": "South-West (Victoria Island, Lagos)", "age_band": "Gen X (47)",
     "register_tier": "standard_english", "income": "high (₦4M/mo)",
     "occupation": "oil & gas executive (Shell / Chevron level)", "religion": "christian (anglican)"},
    {"name": "halima_jos", "region": "North-Central (Jos, Plateau)", "age_band": "Gen X (45)",
     "register_tier": "nigerian_english", "income": "middle (₦280k/mo)",
     "occupation": "civil servant — ministry of agriculture", "religion": "muslim (sunni)"},
    {"name": "emeka_aba", "region": "South-East (Aba, Abia)", "age_band": "Gen X (52)",
     "register_tier": "nigerian_pidgin", "income": "upper-middle (₦900k/mo, variable)",
     "occupation": "Aba spare-parts merchant (auto parts trader)", "religion": "christian (catholic)"},
    {"name": "yemisi_abeokuta", "region": "South-West (Abeokuta, Ogun)", "age_band": "Gen X (49)",
     "register_tier": "nigerian_english", "income": "middle (₦230k/mo)",
     "occupation": "primary school headmistress", "religion": "christian (pentecostal)"},
    {"name": "garba_kano", "region": "North-West (Kano)", "age_band": "Gen X (54)",
     "register_tier": "nigerian_english", "income": "high (₦1.8M/mo)",
     "occupation": "Sabon Gari market wholesaler (textiles)", "religion": "muslim (sunni)"},

    # Boomer
    {"name": "chief_okonkwo", "region": "South-East (Nnewi, Anambra)", "age_band": "Boomer (62)",
     "register_tier": "nigerian_english", "income": "high (₦3M/mo)",
     "occupation": "retired civil servant — pensioner + landlord (3 properties)",
     "religion": "christian (catholic)"},
    {"name": "alhaji_yusuf", "region": "North-West (Kano)", "age_band": "Boomer (66)",
     "register_tier": "nigerian_english", "income": "high (₦5M/mo)",
     "occupation": "transport business owner (passenger + cargo fleet)",
     "religion": "muslim (sunni)"},

    # Diaspora-leaning / tech
    {"name": "tomide_abuja_remote", "region": "FCT Abuja (remote-working class)",
     "age_band": "Millennial (28)", "register_tier": "standard_english",
     "income": "high (₦3M/mo USD-equivalent)", "occupation": "remote senior software engineer (US fintech)",
     "religion": "christian (non-denominational)"},

    # Agricultural Nigerian (huge demographic, often missed)
    {"name": "mama_grace_benue", "region": "North-Central (Makurdi, Benue)", "age_band": "Gen X (50)",
     "register_tier": "nigerian_pidgin", "income": "lower (₦60k/mo seasonal)",
     "occupation": "smallholder farmer (yam + rice) + market trader",
     "religion": "christian (pentecostal)"},
]


SYSTEM = """You are an expert in Nigerian consumer behaviour, sociolinguistics, and market research.
You build PERSONA records for a Nigerian customer-simulation system. Personas must be authentic,
specific, and avoid stereotype caricature. Every detail (markers, anchors, intensity calibration)
must be plausible for the actual Nigerian person described."""


PROMPT_TEMPLATE = """Generate a complete persona JSON for the following Nigerian person.

DEMOGRAPHIC CELL:
  Name slug:          {name}
  Region:             {region}
  Age band:           {age_band}
  Register tier:      {register_tier}
  Income band:        {income}
  Occupation:         {occupation}
  Religion:           {religion}

OUTPUT — return ONLY a JSON object with these fields (no markdown, no commentary):
{{
  "user_id": "{name}",
  "demographics": {{
    "age_range": "<exact age range bucket>",
    "location": "<specific city / area>",
    "occupation": "<concise>"
  }},
  "hedonic_utilitarian": <float 0.0-1.0; how much they buy for pleasure vs utility>,
  "intensity_calibration": {{
    "<intensifier word THEY would actually use>": <rating 1.0-5.0 that word maps to for them>,
    ...
  }},  // 5-7 entries, with words/phrases native to this person's register and language
  "communal_individual": <float 0.0-1.0; how communal their framing is>,
  "aspect_priority": {{
    "<aspect they care about>": <weight summing to ~1.0>,
    ...
  }},  // 4-6 aspects realistic for this person's purchases
  "register_tier": "{register_tier}",
  "register_markers": [
    "<actual phrase this person would say>", ...
  ],  // 5-8 phrases authentic to register × region × religion. AVOID generic "abeg/wahala" for everyone.
  "register_confidence": <0.7-0.95>,
  "review_anchors": [
    {{
      "review_id": "anchor_<2-letter-initial>01",
      "product_id": "<plausible Jumia product they recently bought>",
      "rating": <1-5>,
      "text": "<3-4 sentence review IN THEIR VOICE, showing register, intensity, aspect priorities, communal framing>"
    }},
    {{ ... }}
  ],  // 2-3 anchors. Anchors must read AUTHENTICALLY — not stereotyped.
  "history_count": <realistic for their income/age, 5-60>,
  "extraction_source": "manual",
  "schema_version": "1.0"
}}

GUIDELINES:
- For Muslim/Hausa speakers in the North: include "Alhamdulillah", "Mashallah", "wallahi" where natural.
- For Yoruba code-switching: include "ah", "se", "now" tagged sentence-finally where natural.
- For Igbo code-switching: include "biko", "nna", "ehee", "see ehn" where natural.
- For Pidgin: "wahala", "abeg", "dey", "e shock me", "no shaking" — but DO NOT make every persona a Pidgin caricature.
- Standard English speakers: write cleanly. NO Pidgin markers. They're real too.
- High-income personas care about brand prestige; low-income personas care about durability + value.
- Anchors must show the persona's specific concerns (school for teachers, fleet for transport, etc.)
"""


def _pick_provider() -> str:
    """Pick the first provider whose API key is populated."""
    if PROVIDER != "auto":
        return PROVIDER
    if os.getenv("NVIDIA_API_KEY"):
        return "nvidia"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    return "none"


def _strip_json(text: str) -> str:
    # Strip code fences if model wrapped output in ```json … ```
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", (text or "").strip(),
                  flags=re.MULTILINE)


def generate_one(spec: dict) -> dict | None:
    """Generate one persona JSON via the first available provider."""
    user = PROMPT_TEMPLATE.format(**spec)
    provider = _pick_provider()

    if provider == "nvidia":
        api_key = os.getenv("NVIDIA_API_KEY")
        client = OpenAI(api_key=api_key, base_url="https://integrate.api.nvidia.com/v1")
        model = NIM_MODEL
        kwargs: dict = {}  # NIM doesn't reliably support response_format
    elif provider == "openai":
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"),
                        base_url=os.getenv("OPENAI_BASE_URL") or None)
        model = "gpt-4o-mini"
        kwargs = {"response_format": {"type": "json_object"}}
    elif provider == "anthropic":
        try:
            import anthropic
        except ImportError:
            logger.error("anthropic package not installed")
            return None
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        try:
            resp = client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=2000,
                system=SYSTEM,
                messages=[{"role": "user", "content": user}],
                temperature=0.7,
            )
            return json.loads(_strip_json(resp.content[0].text))
        except Exception as e:
            logger.warning("  anthropic failed for %s: %s", spec["name"], str(e)[:200])
            return None
    else:
        logger.error("no API key set for any provider")
        return None

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user},
            ],
            temperature=0.7,
            max_tokens=2000,
            **kwargs,
        )
        text = resp.choices[0].message.content
        return json.loads(_strip_json(text))
    except Exception as e:
        logger.warning("  %s failed for %s: %s", provider, spec["name"], str(e)[:200])
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=len(PERSONA_SPECS),
                    help="Number of personas to generate (default: all)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="Overwrite existing persona files")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    existing = {p.stem for p in OUT_DIR.glob("*.json")}
    logger.info("existing personas: %d (%s)", len(existing), sorted(existing))

    specs = PERSONA_SPECS[:args.n]
    logger.info("will generate %d personas via provider=%s", len(specs), _pick_provider())

    if args.dry_run:
        for s in specs:
            logger.info("  %s | %s | %s | %s",
                        s["name"], s["region"], s["register_tier"], s["occupation"])
        return 0

    written, skipped, failed = 0, 0, 0
    for spec in specs:
        if spec["name"] in existing and not args.force:
            skipped += 1
            continue
        logger.info("→ %s (%s, %s)", spec["name"], spec["register_tier"], spec["occupation"][:40])
        persona = generate_one(spec)
        if not persona:
            failed += 1
            continue
        # Sanity-validate
        if not isinstance(persona, dict) or "user_id" not in persona:
            logger.warning("  malformed output for %s; skipping", spec["name"])
            failed += 1
            continue
        # Pin user_id to our slug regardless of what model returned
        persona["user_id"] = spec["name"]
        out_path = OUT_DIR / f"{spec['name']}.json"
        out_path.write_text(json.dumps(persona, indent=2, ensure_ascii=False), encoding="utf-8")
        written += 1

    logger.info("✅ %d written, %d skipped (existed), %d failed", written, skipped, failed)
    total = len(list(OUT_DIR.glob("*.json")))
    logger.info("   total personas now: %d", total)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
