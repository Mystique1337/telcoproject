"""Naija Persona Agent — Streamlit Judge Demo.

Run locally:
    NPA_API_URL=http://localhost:8765 streamlit run demo/streamlit_app.py

Features:
- 5 Nigerian persona archetypes (Chinwe, Tunde, Aisha, Femi, Ifeoma)
- 6 sample products (Tecno, inverter, foundation, MacBook, iron, Anikulapo movie)
- Per-request model selector — pick which LLM handles each task
- Side-by-side compare: NaijaReviewer-8B vs Vanilla Claude/GPT-4o
- Reasoning trace viewer
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import requests
import streamlit as st


API_URL = os.getenv("NPA_API_URL", "http://localhost:8765")
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PERSONA_DIR = PROJECT_ROOT / "data" / "sample" / "personas"
PRODUCT_DIR = PROJECT_ROOT / "data" / "sample" / "products"


st.set_page_config(
    page_title="Naija Persona Agent",
    page_icon="🇳🇬",
    layout="wide",
)

st.title("🇳🇬 Naija Persona Agent")
st.caption(
    "Nigerian-context LLM agent for review simulation (Task 1) + personalised recommendation (Task 2). "
    "Pick a persona, pick a product, see how the fine-tuned NaijaReviewer-8B handles it — and compare "
    "against vanilla frontier models side-by-side."
)


# ============================================================
# Model registry — what the user can pick from
# ============================================================
MODEL_REGISTRY = {
    "🇳🇬 NaijaReviewer-8B (fine-tuned, local)": "lmstudio:naija-reviewer-8b",
    "Claude Sonnet 4 (Anthropic)":              "anthropic:claude-sonnet-4-20250514",
    "GPT-4o (OpenAI)":                          "openai:gpt-4o",
    "GPT-4o mini (OpenAI)":                     "openai:gpt-4o-mini",
    "Llama 3.1 8B base (Ollama)":               "ollama:llama3.1:8b-instruct",
}


# ============================================================
# Sidebar — API status + about
# ============================================================
with st.sidebar:
    st.header("About")
    st.markdown(
        """
        - **Task 1**: persona + product → review + rating
        - **Task 2**: persona → ranked product recommendations

        Backed by **NaijaReviewer-8B** — Llama 3.1 8B QLoRA fine-tune on ~20k
        Nigerian product reviews (Jumia + synthetic + AfriSenti Pidgin).

        [GitHub](https://github.com/Mystique1337/telcoproject) ·
        [🤗 Model](https://huggingface.co/Mystique1337/naija-reviewer-8b) ·
        [📄 Paper](#)
        """
    )
    st.divider()
    st.subheader("API status")
    try:
        r = requests.get(f"{API_URL}/health", timeout=3)
        if r.status_code == 200:
            info = r.json()
            st.success(f"✅ Connected: {API_URL}")
            with st.expander("Config"):
                st.json(info.get("components", {}))
        else:
            st.error(f"❌ HTTP {r.status_code}: {r.text[:100]}")
    except Exception as e:
        st.error(f"❌ Unreachable: {e}")
        st.caption(f"Run: `NPA_API_URL={API_URL} streamlit run demo/streamlit_app.py`")


# ============================================================
# Data loaders
# ============================================================
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


def _persona_one_liner(p: dict) -> str:
    d = p.get("demographics", {})
    loc = d.get("location", "")
    occ = d.get("occupation", "")
    reg = p.get("register_tier", "")
    bits = [b for b in (loc, occ, reg.replace("_", " ")) if b]
    return " · ".join(bits)


# ============================================================
# Tabs
# ============================================================
tab1, tab2 = st.tabs(["📝 Simulate Review (Task 1)", "🎯 Recommend (Task 2)"])


# ============ Task 1 — Simulate Review ============
with tab1:
    st.subheader("Generate a Nigerian product review")
    st.caption("Pick a persona, a product, then choose which LLM should write the review.")

    col_left, col_right = st.columns(2)
    with col_left:
        persona_key = st.selectbox(
            "Persona",
            list(personas.keys()),
            format_func=lambda k: f"{personas[k].get('user_id', k)} — {_persona_one_liner(personas[k])}",
            key="t1_persona",
        )
        persona = personas[persona_key]
        with st.expander("View persona JSON", expanded=False):
            st.json(persona)

    with col_right:
        product_key = st.selectbox(
            "Product",
            list(products.keys()),
            format_func=lambda k: f"{products[k].get('title', k)[:50]}",
            key="t1_product",
        )
        product = products[product_key]
        with st.expander("View product JSON", expanded=False):
            st.json(product)

    st.divider()

    # Compare mode toggle
    compare_mode = st.toggle(
        "**🆚 Compare side-by-side** (NaijaReviewer vs vanilla LLM)",
        value=True,
        key="t1_compare",
    )

    if compare_mode:
        col_a, col_b = st.columns(2)
        with col_a:
            model_a = st.selectbox(
                "Model A (left)",
                list(MODEL_REGISTRY.keys()),
                index=0,  # default to NaijaReviewer
                key="t1_model_a",
            )
        with col_b:
            model_b = st.selectbox(
                "Model B (right)",
                list(MODEL_REGISTRY.keys()),
                index=1,  # default to Claude
                key="t1_model_b",
            )
    else:
        model_a = st.selectbox(
            "Model",
            list(MODEL_REGISTRY.keys()),
            index=0,
            key="t1_model_single",
        )
        model_b = None

    if st.button("Generate Review", type="primary", use_container_width=True, key="t1_go"):
        def _call(model_label: str):
            backbone = MODEL_REGISTRY[model_label]
            payload = {
                "persona": persona,
                "product": product,
                "include_reasoning": True,
                "backbone_override": backbone,
            }
            try:
                resp = requests.post(f"{API_URL}/simulate-review", json=payload, timeout=120)
                resp.raise_for_status()
                return resp.json(), None
            except Exception as exc:
                return None, str(exc)

        if compare_mode:
            col_a, col_b = st.columns(2)
            with col_a:
                with st.spinner(f"Generating with {model_a}..."):
                    data_a, err_a = _call(model_a)
                if err_a:
                    st.error(err_a)
                elif data_a:
                    st.success(f"⭐ {data_a['rating']}/5 · {data_a['register_tier']} · {data_a.get('latency_ms', 0)} ms")
                    st.markdown(f"**{model_a}**")
                    st.markdown(f"> {data_a['review']}")
                    st.caption(f"💡 {data_a['rationale']}")
                    if data_a.get("reasoning_trace"):
                        with st.expander("🧠 Reasoning trace"):
                            st.json(data_a["reasoning_trace"])
            with col_b:
                with st.spinner(f"Generating with {model_b}..."):
                    data_b, err_b = _call(model_b)
                if err_b:
                    st.error(err_b)
                elif data_b:
                    st.success(f"⭐ {data_b['rating']}/5 · {data_b['register_tier']} · {data_b.get('latency_ms', 0)} ms")
                    st.markdown(f"**{model_b}**")
                    st.markdown(f"> {data_b['review']}")
                    st.caption(f"💡 {data_b['rationale']}")
                    if data_b.get("reasoning_trace"):
                        with st.expander("🧠 Reasoning trace"):
                            st.json(data_b["reasoning_trace"])
        else:
            with st.spinner(f"Generating with {model_a}..."):
                data, err = _call(model_a)
            if err:
                st.error(err)
            elif data:
                st.success(f"⭐ {data['rating']}/5 · {data['register_tier']} · {data.get('latency_ms', 0)} ms")
                st.markdown(f"**Review**")
                st.markdown(f"> {data['review']}")
                st.caption(f"💡 {data['rationale']}")
                if data.get("reasoning_trace"):
                    with st.expander("🧠 Reasoning trace"):
                        st.json(data["reasoning_trace"])


# ============ Task 2 — Recommend ============
with tab2:
    st.subheader("Recommend products for a Nigerian persona")
    st.caption("Pick a persona, then choose which LLM should rank the products.")

    persona_key_2 = st.selectbox(
        "Persona",
        list(personas.keys()),
        format_func=lambda k: f"{personas[k].get('user_id', k)} — {_persona_one_liner(personas[k])}",
        index=1,  # default to Tunde — recommendation use case
        key="t2_persona",
    )
    persona_2 = personas[persona_key_2]

    col_x, col_y = st.columns([2, 1])
    with col_x:
        reranker_choice = st.selectbox(
            "Re-ranker model",
            list(MODEL_REGISTRY.keys()),
            index=1,  # default Claude — better for ranking reasoning
            key="t2_model",
        )
    with col_y:
        k = st.slider("Top-K", 1, 10, 5, key="t2_k")

    if st.button("Generate Recommendations", type="primary", use_container_width=True, key="t2_go"):
        payload = {
            "persona": persona_2,
            "domain": "jumia",
            "k": k,
            "include_reasoning": True,
            "reranker_override": MODEL_REGISTRY[reranker_choice],
        }
        with st.spinner(f"Ranking with {reranker_choice}..."):
            try:
                resp = requests.post(f"{API_URL}/recommend", json=payload, timeout=120)
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:
                st.error(str(exc))
                data = None

        if data and data.get("recommendations"):
            st.success(f"✅ {len(data['recommendations'])} recommendations · {data.get('latency_ms', 0)} ms")
            for item in data["recommendations"]:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**#{item['rank']} · {item.get('title') or item['product_id']}**")
                        st.caption(f"💡 {item['rationale']}")
                    with col2:
                        st.metric("Score", f"{item['score']:.2f}")
                    st.divider()
            if data.get("reasoning_trace"):
                with st.expander("🧠 Reasoning trace"):
                    st.json(data["reasoning_trace"])
        elif data:
            st.warning(
                "No recommendations returned. The product index may be empty — run "
                "`python scripts/build_product_index.py` to populate it with the 18k Jumia catalog."
            )


# ============================================================
# Footer
# ============================================================
st.divider()
st.caption(
    "🎓 Submission to the Nigerian AI Agents Hackathon, May 2026 — "
    "Team Franca & Ashinze. "
    f"API: `{API_URL}`"
)
