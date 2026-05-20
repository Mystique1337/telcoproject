"""Naija Persona Agent — Streamlit Judge Demo (v2).

Run locally:
    NPA_API_URL=http://localhost:8765 streamlit run demo/streamlit_app.py

Updated for v5 capabilities:
- 24-persona library (filter by register tier / region)
- 6,657 real Jumia product catalogue (search by name, filter by category)
- 3 tabs: Simulate Review (Task A), Recommend (Task B), Multi-turn Recommend
- Surfaces cold_start / cross_domain / multi_turn flags as badges
- Pretty-prints the narrative reasoning trace (no longer raw JSON)
- Sidebar: live eval headline numbers from paper/results.json
- Per-request backbone_override + reranker_override visible
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
RESULTS_PATH = PROJECT_ROOT / "paper" / "results.json"


st.set_page_config(
    page_title="Naija Persona Agent",
    page_icon="🇳🇬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# Constants
# ============================================================
MODEL_REGISTRY: dict[str, str] = {
    "🇳🇬 NaijaReviewer-8B (fine-tuned, local)": "lmstudio:naija-reviewer-8b",
    "Claude Sonnet 4 (Anthropic)":              "anthropic:claude-sonnet-4-20250514",
    "GPT-4o (OpenAI)":                          "openai:gpt-4o",
    "GPT-4o mini (OpenAI)":                     "openai:gpt-4o-mini",
    "Llama 3.3 70B (NIM, free tier)":           "nvidia:meta/llama-3.3-70b-instruct",
    "Llama 3.1 8B base (Ollama)":               "ollama:llama3.1:8b-instruct",
}

REGISTER_TIERS = ["all", "nigerian_pidgin", "code_mixed", "nigerian_english", "standard_english"]


# ============================================================
# Header
# ============================================================
st.title("🇳🇬 Naija Persona Agent")
st.caption(
    "Open-weight Nigerian-context LLM agent for review simulation + personalised "
    "recommendation. 24 personas × 6,657 real Jumia products. Pick a persona, "
    "pick a product, see how the fine-tuned **NaijaReviewer-8B** handles it — "
    "and compare against frontier models side-by-side."
)


# ============================================================
# Data loaders
# ============================================================
@st.cache_data
def load_personas() -> dict[str, dict]:
    out = {}
    for f in sorted(PERSONA_DIR.glob("*.json")):
        try:
            out[f.stem] = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
    return out


@st.cache_data
def load_products() -> dict[str, dict]:
    out = {}
    for f in sorted(PRODUCT_DIR.glob("*.json")):
        try:
            out[f.stem] = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
    return out


@st.cache_data
def load_results_headline() -> dict:
    """Read paper/results.json for live eval numbers in the sidebar."""
    if not RESULTS_PATH.exists():
        return {}
    try:
        d = json.loads(RESULTS_PATH.read_text())
    except Exception:
        return {}
    t1 = d.get("task1_user_modeling", {})
    t2 = d.get("task2_recommendation", {})
    naija_t1 = t1.get("naija_reviewer_8b", {}) or {}
    claude_t1 = t1.get("claude_sonnet_4", {}) or {}
    naija_t2 = t2.get("naija_reviewer_8b", {}) or {}
    claude_t2 = t2.get("claude_sonnet_4", {}) or {}
    return {
        "naija_rmse": naija_t1.get("RMSE"),
        "claude_rmse": claude_t1.get("RMSE"),
        "naija_bert": (naija_t1.get("BERTScore") or {}).get("F1"),
        "claude_bert": (claude_t1.get("BERTScore") or {}).get("F1"),
        "naija_rougeL": (naija_t1.get("ROUGE") or {}).get("rougeL"),
        "claude_rougeL": (claude_t1.get("ROUGE") or {}).get("rougeL"),
        "naija_overall": (naija_t1.get("AgentSociety") or {}).get("overall_quality"),
        "claude_overall": (claude_t1.get("AgentSociety") or {}).get("overall_quality"),
        "naija_ndcg10": naija_t2.get("NDCG_at_10"),
        "claude_ndcg10": claude_t2.get("NDCG_at_10"),
        "naija_hr5": naija_t2.get("HR_at_5"),
        "claude_hr5": claude_t2.get("HR_at_5"),
        "n_task1": naija_t1.get("n_valid"),
        "n_task2": naija_t2.get("n_valid"),
    }


personas = load_personas()
products = load_products()
results = load_results_headline()


# ============================================================
# Helpers
# ============================================================
def _persona_one_liner(p: dict) -> str:
    d = p.get("demographics", {}) or {}
    loc = d.get("location", "")
    occ = d.get("occupation", "")
    reg = (p.get("register_tier") or "").replace("_", " ")
    bits = [b for b in (loc, occ, reg) if b]
    return " · ".join(bits)


def _persona_label(p: dict, key: str) -> str:
    uid = p.get("user_id", key)
    return f"{uid} — {_persona_one_liner(p)}"


def _product_label(p: dict, key: str) -> str:
    title = (p.get("title") or key)[:70]
    cat = p.get("category", "")
    price = p.get("price_naira")
    price_str = f" · ₦{int(price):,}" if price else ""
    return f"{title}  ({cat}{price_str})"


def _filter_personas(personas: dict, tier: str, search: str) -> dict:
    out = {}
    s = search.lower().strip()
    for k, p in personas.items():
        if tier != "all" and p.get("register_tier") != tier:
            continue
        if s:
            blob = f"{k} {p.get('user_id','')} {_persona_one_liner(p)}".lower()
            if s not in blob:
                continue
        out[k] = p
    return out


def _filter_products(products: dict, cat: str, search: str, limit: int = 500) -> dict:
    out = {}
    s = search.lower().strip()
    for k, p in products.items():
        if cat != "all" and p.get("category") != cat:
            continue
        if s and s not in (p.get("title") or "").lower():
            continue
        out[k] = p
        if len(out) >= limit:
            break
    return out


def _format_score(val, fmt: str = "{:.3f}") -> str:
    return fmt.format(val) if isinstance(val, (int, float)) else "—"


def _render_reasoning_trace(trace: list[dict]) -> None:
    """Pretty-print the narrative reasoning trace (replaces raw JSON dump)."""
    if not trace:
        return
    for i, node in enumerate(trace, start=1):
        name = node.get("node", "step")
        summary = node.get("summary")
        st.markdown(f"**{i}. {name}**")
        if summary:
            st.markdown(f"  > {summary}")
        else:
            # Fall back to compact JSON for nodes without a summary
            tech = {k: v for k, v in node.items() if k not in ("node", "summary")}
            if tech:
                st.caption(" · ".join(f"{k}={v}" for k, v in tech.items()))


def _render_response_flags(data: dict) -> None:
    """Render cold_start / cross_domain / multi_turn flags as colored badges."""
    flags = []
    if data.get("cold_start"):
        flags.append(("🧊 Cold-start path", "blue"))
    if data.get("cross_domain"):
        flags.append(("🌍 Cross-domain retrieval", "violet"))
    if data.get("multi_turn"):
        flags.append(("💬 Multi-turn", "orange"))
    for label, color in flags:
        st.markdown(
            f'<span style="background-color:#{ {"blue":"e0f0ff","violet":"f0e0ff","orange":"ffefdb"}[color] };'
            f' padding:4px 10px; border-radius:12px; margin-right:6px; font-size:0.85em;">{label}</span>',
            unsafe_allow_html=True,
        )


# ============================================================
# Sidebar
# ============================================================
with st.sidebar:
    st.header("🇳🇬 Naija Persona Agent")
    st.markdown(
        "Open-weight Nigerian-context LLM agent system. Two-task hackathon submission "
        "+ v0 engine of the **NaijaPersona** synthetic customer-panel platform."
    )

    st.divider()

    # ─── Live eval headlines from paper/results.json ───
    st.subheader("📊 Live eval (v2, n=100)")
    if results:
        c1, c2 = st.columns(2)
        c1.metric("RMSE  ↓",
                  _format_score(results.get("naija_rmse")),
                  f'vs Claude {_format_score(results.get("claude_rmse"))}',
                  delta_color="inverse")
        c2.metric("NDCG@10 ↑",
                  _format_score(results.get("naija_ndcg10")),
                  f'vs {_format_score(results.get("claude_ndcg10"))}')
        c1, c2 = st.columns(2)
        c1.metric("BERTScore F1",
                  _format_score(results.get("naija_bert")),
                  f'vs {_format_score(results.get("claude_bert"))}')
        c2.metric("AS overall",
                  _format_score(results.get("naija_overall")),
                  f'vs {_format_score(results.get("claude_overall"))}')
        st.caption(
            f"From `paper/results.json`. Task A: n={results.get('n_task1')}, "
            f"Task B: n={results.get('n_task2')} scenarios."
        )
    else:
        st.caption("No `paper/results.json` yet — run `python scripts/eval_all.py`.")

    st.divider()

    # ─── API status ───
    st.subheader("API status")
    try:
        r = requests.get(f"{API_URL}/health", timeout=3)
        if r.status_code == 200:
            info = r.json()
            st.success(f"✅ Connected   `{API_URL}`")
            with st.expander("API config"):
                st.json(info.get("components", {}))
        else:
            st.error(f"❌ HTTP {r.status_code}: {r.text[:100]}")
    except Exception as e:
        st.error(f"❌ Unreachable: `{API_URL}`")
        st.caption(f"Start the API: `make serve` (port 8765). Then refresh.")

    st.divider()
    st.markdown(
        "**Resources**\n\n"
        "- [GitHub repo](https://github.com/Mystique1337/telcoproject)\n"
        "- [🤗 Model (GGUF)](https://huggingface.co/Shinzmann/naija-reviewer-8b-v2-Q4_K_M-GGUF)\n"
        "- AgentSociety drop-in: `submission/naija_agent.py`\n"
        "- Paper: `paper/paper.tex`"
    )


# ============================================================
# Tabs
# ============================================================
tab1, tab2, tab3 = st.tabs(
    ["📝 Simulate Review (Task A)",
     "🎯 Recommend (Task B)",
     "💬 Multi-turn Recommend"]
)


# =================================================================== #
# TAB 1 — Simulate Review
# =================================================================== #

with tab1:
    st.subheader("Generate a Nigerian product review")
    st.caption(
        "Pick a persona (24 archetypes spanning 6 geopolitical zones × 4 register tiers), "
        "a product (from 6.6k real Jumia catalog), then choose which LLM should write the review."
    )

    # ─── Persona picker with filtering ───
    pc1, pc2, pc3 = st.columns([1, 1, 2])
    with pc1:
        tier_filter = st.selectbox("Register tier", REGISTER_TIERS, index=0, key="t1_tier")
    with pc2:
        persona_search = st.text_input("Search persona", key="t1_pers_search",
                                       placeholder="e.g. lagos, trader, kano")
    filtered_p = _filter_personas(personas, tier_filter, persona_search)
    with pc3:
        if filtered_p:
            persona_key = st.selectbox(
                f"Persona ({len(filtered_p)} / {len(personas)} match)",
                list(filtered_p.keys()),
                format_func=lambda k: _persona_label(filtered_p[k], k),
                key="t1_persona",
            )
            persona = filtered_p[persona_key]
        else:
            st.warning("No personas match the filter.")
            persona = None

    if persona is not None:
        with st.expander("View full persona JSON"):
            st.json(persona)

    # ─── Product picker with search/filter ───
    st.markdown("##### Product")
    pp1, pp2, pp3 = st.columns([1, 1, 2])
    with pp1:
        cats = sorted({p.get("category", "?") for p in products.values()})
        cat_filter = st.selectbox("Category", ["all"] + cats, index=0, key="t1_cat")
    with pp2:
        prod_search = st.text_input("Search product", key="t1_prod_search",
                                    placeholder="e.g. tecno, blender")
    filtered_pr = _filter_products(products, cat_filter, prod_search)
    with pp3:
        if filtered_pr:
            product_key = st.selectbox(
                f"Product ({len(filtered_pr)} / {len(products)} match)",
                list(filtered_pr.keys()),
                format_func=lambda k: _product_label(filtered_pr[k], k),
                key="t1_product",
            )
            product = filtered_pr[product_key]
        else:
            st.warning("No products match the filter.")
            product = None

    if product is not None:
        with st.expander("View product JSON"):
            st.json(product)

    st.divider()

    # ─── Compare mode ───
    compare_mode = st.toggle(
        "**🆚 Compare side-by-side** (recommended — pits NaijaReviewer-8B against a frontier model on the SAME persona × product)",
        value=True, key="t1_compare",
    )

    if compare_mode:
        ca, cb = st.columns(2)
        with ca:
            model_a = st.selectbox("Model A (left)", list(MODEL_REGISTRY.keys()), index=0, key="t1_model_a")
        with cb:
            model_b = st.selectbox("Model B (right)", list(MODEL_REGISTRY.keys()), index=1, key="t1_model_b")
    else:
        model_a = st.selectbox("Model", list(MODEL_REGISTRY.keys()), index=0, key="t1_model_single")
        model_b = None

    if persona is not None and product is not None:
        if st.button("Generate Review", type="primary", use_container_width=True, key="t1_go"):

            def _call(label: str):
                payload = {
                    "persona": persona,
                    "product": product,
                    "include_reasoning": True,
                    "backbone_override": MODEL_REGISTRY[label],
                }
                try:
                    resp = requests.post(f"{API_URL}/simulate-review", json=payload, timeout=180)
                    resp.raise_for_status()
                    return resp.json(), None
                except Exception as exc:
                    return None, str(exc)

            def _render_review(data: dict, model_label: str) -> None:
                if not data:
                    return
                st.success(
                    f"⭐ {data.get('rating','?')}/5  ·  "
                    f"register={data.get('register_tier','?')}  ·  "
                    f"{data.get('latency_ms', 0)} ms"
                )
                st.markdown(f"**{model_label}**")
                st.markdown(f"> {data.get('review','(empty)')}")
                st.caption(f"💡 {data.get('rationale','')}")
                if data.get("reasoning_trace"):
                    with st.expander("🧠 Reasoning trace", expanded=False):
                        _render_reasoning_trace(data["reasoning_trace"])

            if compare_mode:
                col_a, col_b = st.columns(2)
                with col_a:
                    with st.spinner(f"Generating with {model_a}..."):
                        data_a, err_a = _call(model_a)
                    if err_a:
                        st.error(err_a)
                    else:
                        _render_review(data_a, model_a)
                with col_b:
                    with st.spinner(f"Generating with {model_b}..."):
                        data_b, err_b = _call(model_b)
                    if err_b:
                        st.error(err_b)
                    else:
                        _render_review(data_b, model_b)
            else:
                with st.spinner(f"Generating with {model_a}..."):
                    data, err = _call(model_a)
                if err:
                    st.error(err)
                else:
                    _render_review(data, model_a)


# =================================================================== #
# TAB 2 — Recommend (single-shot, supports cold-start + cross-domain)
# =================================================================== #

with tab2:
    st.subheader("Personalised product recommendations")
    st.caption(
        "Single-shot persona-aware recommendation. Supports **cold-start** "
        "(personas with no history → popularity-weighted) and **cross-domain** "
        "(`domain=all` → multi-catalogue retrieval with category-diverse top-K)."
    )

    # ─── Persona picker (reuse filter UI) ───
    pc1, pc2, pc3 = st.columns([1, 1, 2])
    with pc1:
        tier_filter2 = st.selectbox("Register tier", REGISTER_TIERS, index=0, key="t2_tier")
    with pc2:
        persona_search2 = st.text_input("Search persona", key="t2_pers_search",
                                        placeholder="e.g. tunde, fintech")
    filtered_p2 = _filter_personas(personas, tier_filter2, persona_search2)
    with pc3:
        if filtered_p2:
            persona_key_2 = st.selectbox(
                f"Persona ({len(filtered_p2)} / {len(personas)} match)",
                list(filtered_p2.keys()),
                format_func=lambda k: _persona_label(filtered_p2[k], k),
                key="t2_persona",
            )
            persona_2 = filtered_p2[persona_key_2]
        else:
            st.warning("No personas match.")
            persona_2 = None

    # ─── Cold-start toggle (forces history_count=0) ───
    cs1, cs2, cs3 = st.columns([1, 1, 1])
    with cs1:
        force_cold_start = st.checkbox(
            "🧊 Force cold-start (wipe history)",
            value=False,
            help="Simulates a brand-new user — wipes history_count + review_anchors. "
                 "The agent should branch into popularity-weighted prerank.",
            key="t2_cs",
        )
    with cs2:
        domain = st.selectbox(
            "Domain",
            ["jumia", "konga", "nollywood", "all"],
            index=0,
            help="`all` → cross-domain retrieval across multiple catalogues.",
            key="t2_domain",
        )
    with cs3:
        k = st.slider("Top-K", 1, 10, 5, key="t2_k")

    # ─── Re-ranker model ───
    reranker_choice = st.selectbox(
        "Re-ranker model", list(MODEL_REGISTRY.keys()), index=0,
        help="Model that scores + ranks the candidates.",
        key="t2_model",
    )

    if persona_2 is not None and st.button(
        "Generate Recommendations", type="primary", use_container_width=True, key="t2_go"
    ):
        active_persona = dict(persona_2)
        if force_cold_start:
            active_persona["history_count"] = 0
            active_persona["review_anchors"] = []

        payload = {
            "persona": active_persona,
            "domain": domain,
            "k": k,
            "include_reasoning": True,
            "reranker_override": MODEL_REGISTRY[reranker_choice],
        }
        with st.spinner(f"Ranking with {reranker_choice}..."):
            try:
                resp = requests.post(f"{API_URL}/recommend", json=payload, timeout=180)
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:
                st.error(str(exc))
                data = None

        if data and data.get("recommendations"):
            st.success(
                f"✅ {len(data['recommendations'])} recommendations  ·  "
                f"{data.get('latency_ms', 0)} ms"
            )
            _render_response_flags(data)
            st.markdown("")
            for item in data["recommendations"]:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**#{item['rank']} · {item.get('title') or item['product_id']}**")
                    st.caption(f"💡 {item.get('rationale','')}")
                with col2:
                    st.metric("Score", f"{item['score']:.2f}")
                st.divider()
            if data.get("reasoning_trace"):
                with st.expander("🧠 Reasoning trace", expanded=False):
                    _render_reasoning_trace(data["reasoning_trace"])
        elif data:
            st.warning(
                "No recommendations returned. The product index may be empty — run "
                "`python scripts/pull_jumia_products.py` to populate the catalog."
            )


# =================================================================== #
# TAB 3 — Multi-turn Recommend (the brief's third sub-scenario)
# =================================================================== #

with tab3:
    st.subheader("Multi-turn recommendation with conversation history")
    st.caption(
        "Carry constraints across turns. The agent extracts **budget**, "
        "**recipient**, **category** from the conversation and folds them into "
        "the re-ranker prompt as hard constraints. Try: "
        "*\"I want a phone\" → \"for my mum\" → \"under ₦100k\"*."
    )

    # ─── Persona ───
    pc1, pc2, pc3 = st.columns([1, 1, 2])
    with pc1:
        tier_filter3 = st.selectbox("Register tier", REGISTER_TIERS, index=0, key="t3_tier")
    with pc2:
        persona_search3 = st.text_input("Search persona", key="t3_pers_search")
    filtered_p3 = _filter_personas(personas, tier_filter3, persona_search3)
    with pc3:
        if filtered_p3:
            persona_key_3 = st.selectbox(
                f"Persona ({len(filtered_p3)} match)",
                list(filtered_p3.keys()),
                format_func=lambda k: _persona_label(filtered_p3[k], k),
                key="t3_persona",
            )
            persona_3 = filtered_p3[persona_key_3]
        else:
            persona_3 = None

    # ─── Conversation history (mutable list in session state) ───
    if "convo" not in st.session_state:
        st.session_state.convo = [
            {"role": "user", "content": "I want a phone for my mum"},
            {"role": "assistant", "content": "Got it — any budget or features she cares about?"},
            {"role": "user", "content": "Under ₦100k, durable, big buttons preferred"},
        ]

    st.markdown("##### Conversation history")
    new_convo = []
    for i, turn in enumerate(st.session_state.convo):
        c1, c2, c3 = st.columns([1, 5, 1])
        with c1:
            role = st.selectbox(
                "role", ["user", "assistant"],
                index=0 if turn["role"] == "user" else 1,
                key=f"t3_role_{i}", label_visibility="collapsed",
            )
        with c2:
            content = st.text_input(
                "content", value=turn["content"],
                key=f"t3_content_{i}", label_visibility="collapsed",
            )
        with c3:
            keep = st.button("✕", key=f"t3_del_{i}", help="Remove turn")
        if not keep:
            new_convo.append({"role": role, "content": content})
    st.session_state.convo = new_convo

    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        if st.button("➕ Add user turn", key="t3_add_user"):
            st.session_state.convo.append({"role": "user", "content": ""})
            st.rerun()
    with cc2:
        if st.button("➕ Add assistant turn", key="t3_add_asst"):
            st.session_state.convo.append({"role": "assistant", "content": ""})
            st.rerun()
    with cc3:
        if st.button("🔄 Reset to demo", key="t3_reset"):
            st.session_state.convo = [
                {"role": "user", "content": "I want a phone for my mum"},
                {"role": "assistant", "content": "Got it — any budget or features she cares about?"},
                {"role": "user", "content": "Under ₦100k, durable, big buttons preferred"},
            ]
            st.rerun()

    # ─── Settings ───
    st.markdown("##### Settings")
    sc1, sc2, sc3 = st.columns([1, 1, 1])
    with sc1:
        domain3 = st.selectbox("Domain", ["jumia", "konga", "all"], index=0, key="t3_domain")
    with sc2:
        k3 = st.slider("Top-K", 1, 10, 5, key="t3_k")
    with sc3:
        reranker_3 = st.selectbox("Re-ranker", list(MODEL_REGISTRY.keys()), index=0, key="t3_model")

    if persona_3 is not None and st.button(
        "Generate Recommendations", type="primary", use_container_width=True, key="t3_go"
    ):
        payload = {
            "persona": persona_3,
            "domain": domain3,
            "k": k3,
            "include_reasoning": True,
            "reranker_override": MODEL_REGISTRY[reranker_3],
            "conversation_history": [t for t in st.session_state.convo if t.get("content")],
        }
        with st.spinner(f"Running multi-turn rerank via {reranker_3}..."):
            try:
                resp = requests.post(f"{API_URL}/recommend", json=payload, timeout=180)
                resp.raise_for_status()
                data = resp.json()
            except Exception as exc:
                st.error(str(exc))
                data = None

        if data and data.get("recommendations"):
            _render_response_flags(data)
            constraints = data.get("extracted_constraints") or []
            if constraints:
                st.markdown(
                    "**Extracted constraints:** " +
                    " · ".join(f"`{c}`" for c in constraints)
                )
            st.success(
                f"✅ {len(data['recommendations'])} recommendations  ·  "
                f"{data.get('latency_ms', 0)} ms"
            )
            for item in data["recommendations"]:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**#{item['rank']} · {item.get('title') or item['product_id']}**")
                    st.caption(f"💡 {item.get('rationale','')}")
                with col2:
                    st.metric("Score", f"{item['score']:.2f}")
                st.divider()
            if data.get("reasoning_trace"):
                with st.expander("🧠 Reasoning trace", expanded=True):
                    _render_reasoning_trace(data["reasoning_trace"])
        elif data:
            st.warning("No recommendations returned. Check conversation has content turns.")


# ============================================================
# Footer
# ============================================================
st.divider()
fc1, fc2, fc3 = st.columns(3)
fc1.caption(f"🎓 Bluechip Tech Hackathon submission · {len(personas)} personas · {len(products):,}+ products")
fc2.caption("Team Ashinze · Franca · 3rd")
fc3.caption(f"API: `{API_URL}`")
