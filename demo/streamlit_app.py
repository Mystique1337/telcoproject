"""Naija Persona Agent — Streamlit Judge Demo.

Stub for Franca. Wire to the FastAPI backend at NPA_API_URL (defaults to localhost:8000).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import requests
import streamlit as st


API_URL = os.getenv("NPA_API_URL", "http://localhost:8000")
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PERSONA_DIR = PROJECT_ROOT / "data" / "sample" / "personas"
PRODUCT_DIR = PROJECT_ROOT / "data" / "sample" / "products"


st.set_page_config(
    page_title="Naija Persona Agent",
    page_icon="🇳🇬",
    layout="wide",
)

st.title("Naija Persona Agent")
st.caption("Nigerian-context LLM agent for review simulation and personalised recommendation.")


# ---------- sidebar ----------
with st.sidebar:
    st.header("About")
    st.markdown(
        """
        - **Task 1**: Generate a Nigerian product review + rating
        - **Task 2**: Recommend products to a Nigerian persona

        Backed by a fine-tuned **NaijaReviewer-8B** (Llama 3.1 8B QLoRA) when configured,
        with Claude Sonnet 4 as fallback.

        [GitHub](https://github.com/Mystique1337/telcoproject) · [Paper](#)
        """
    )
    api_status_placeholder = st.empty()
    try:
        r = requests.get(f"{API_URL}/health", timeout=2)
        api_status_placeholder.success(f"✅ API reachable at {API_URL}")
    except Exception:  # noqa: BLE001
        api_status_placeholder.error(f"❌ API unreachable at {API_URL}")


# ---------- helpers ----------
@st.cache_data
def load_personas() -> dict[str, dict]:
    out = {}
    for f in sorted(PERSONA_DIR.glob("*.json")):
        out[f.stem] = json.loads(f.read_text(encoding="utf-8"))
    return out


@st.cache_data
def load_products() -> dict[str, dict]:
    out = {}
    for f in sorted(PRODUCT_DIR.glob("*.json")):
        out[f.stem] = json.loads(f.read_text(encoding="utf-8"))
    return out


personas = load_personas()
products = load_products()


# ---------- tabs ----------
tab1, tab2 = st.tabs(["📝 Simulate Review (Task 1)", "🎯 Recommend (Task 2)"])


# ============ Task 1 ============
with tab1:
    st.subheader("Review Simulation")
    col_a, col_b = st.columns(2)

    with col_a:
        persona_key = st.selectbox("Persona", list(personas.keys()), index=0)
        persona = personas[persona_key]
        with st.expander("View persona JSON"):
            st.json(persona)

    with col_b:
        product_key = st.selectbox("Product", list(products.keys()), index=0)
        product = products[product_key]
        with st.expander("View product JSON"):
            st.json(product)

    if st.button("Generate Review", type="primary", use_container_width=True):
        with st.spinner("Generating..."):
            try:
                resp = requests.post(
                    f"{API_URL}/simulate-review",
                    json={"persona": persona, "product": product, "include_reasoning": True},
                    timeout=30,
                )
                data = resp.json()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Request failed: {exc}")
                data = None

        if data:
            st.success(f"⭐ Rating: {data['rating']}/5 · register: {data['register_tier']}")
            st.markdown(f"**Review**\n\n{data['review']}")
            st.caption(f"**Rationale**: {data['rationale']}")
            if data.get("reasoning_trace"):
                with st.expander("🧠 Reasoning trace"):
                    st.json(data["reasoning_trace"])

    st.divider()
    st.caption(
        "💡 *Compare-with-vanilla-Claude panel coming Day 3 — Franca, add a second API call here "
        "using a 'baseline' persona stripped of register markers + aspect priority and render "
        "side-by-side.*"
    )


# ============ Task 2 ============
with tab2:
    st.subheader("Personalised Recommendations")
    persona_key_2 = st.selectbox("Persona", list(personas.keys()), index=1, key="rec_persona")
    persona_2 = personas[persona_key_2]
    k = st.slider("How many recommendations?", 1, 10, 5)

    if st.button("Generate Recommendations", type="primary", use_container_width=True):
        with st.spinner("Ranking products..."):
            try:
                resp = requests.post(
                    f"{API_URL}/recommend",
                    json={
                        "persona": persona_2,
                        "domain": "jumia",
                        "k": k,
                        "include_reasoning": True,
                    },
                    timeout=30,
                )
                data = resp.json()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Request failed: {exc}")
                data = None

        if data and data.get("recommendations"):
            for item in data["recommendations"]:
                with st.container():
                    st.markdown(f"**#{item['rank']} · {item.get('title', item['product_id'])}**")
                    st.caption(f"Score: {item['score']:.2f} · {item['rationale']}")
                    st.divider()
            if data.get("reasoning_trace"):
                with st.expander("🧠 Reasoning trace"):
                    st.json(data["reasoning_trace"])
        elif data:
            st.warning("No recommendations returned. Add more products to `data/sample/products/`.")
