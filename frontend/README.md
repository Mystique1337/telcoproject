# Frontend — Franca's Workstream

> Streamlit (recommended) or Next.js judge demo for Naija Persona Agent.

## Recommended: Streamlit (1-day ship)

The fastest path to a judge-ready compare panel.

```bash
poetry install --with demo
poetry run streamlit run demo/streamlit_app.py
```

Then open `http://localhost:8501`. The stub in `demo/streamlit_app.py` is your starting point — three persona archetypes, a product picker, a "Generate" button, and a side-by-side compare panel against vanilla Claude.

## Deployment

| Platform | Pros | Cons |
|---|---|---|
| **Streamlit Cloud** (Recommended) | Free; auto-deploys from GitHub; subdomain `<app>.streamlit.app` | Sleeps after 7d idle |
| **HuggingFace Spaces** | Free; lots of MLO traffic; Gradio or Streamlit | Slightly slower cold start |
| Vercel (Next.js) | Best perf if you go Next | More setup |

## Layout to build

```
┌───────────────────────────────────────────────┐
│  Naija Persona Agent — Live Demo               │
│                                                │
│  [Pick a persona ▾]   [Pick a product ▾]      │
│                                                │
│  ┌──────────────┐    ┌──────────────────────┐ │
│  │ NaijaReviewer│    │  Vanilla Claude       │ │
│  │ 8B (Ours)    │    │  (Baseline)           │ │
│  │              │    │                       │ │
│  │ ⭐⭐⭐⭐ 4    │    │  ⭐⭐⭐⭐ 4         │ │
│  │              │    │                       │ │
│  │ "Nna ehn..." │    │  "This phone is..."   │ │
│  └──────────────┘    └──────────────────────┘ │
│                                                │
│  Why this output? [▾ show persona dimensions]  │
│                                                │
│  > Switch to Recommendation tab                │
└───────────────────────────────────────────────┘
```

## Two tabs

1. **Simulate Review** — persona + product → side-by-side review compare.
2. **Recommend** — persona → top-5 product recommendations with per-item rationale.

## How to call the API

The backend exposes `POST /simulate-review` and `POST /recommend` (see `data/sample/requests/` for example payloads). From Streamlit:

```python
import requests, json

with open("data/sample/personas/chinwe_owerri.json") as f:
    persona = json.load(f)

with open("data/sample/products/tecno_spark_10.json") as f:
    product = json.load(f)

resp = requests.post(
    "http://localhost:8000/simulate-review",
    json={"persona": persona, "product": product, "include_reasoning": True},
)
print(resp.json())
```

## If you go Next.js instead

- Stack: Next.js 15 (App Router) + Tailwind CSS + shadcn/ui + Vercel AI SDK.
- Bundle frontend into `/frontend` (this dir); main Dockerfile already excludes it from the API container.
- Deploy to Vercel; CORS is already open on the FastAPI backend.

## Sample personas to wire up

| ID | Vibe |
|---|---|
| `chinwe_owerri` | Owerri Gen-Z, code-mixed Igbo+English, communal, hedonic, Afrobeats fan |
| `tunde_lagos` | Lagos market trader, Pidgin-heavy, utilitarian, high-intensity |
| `aisha_kano` | Kano teacher, measured Nigerian English, Muslim framing, mid-intensity |
| `femi_abuja` | Abuja banker, standard English, low-intensity, individualist |
| `ifeoma_ph` | PH Nollywood superfan, Nigerian English with film vocab |

Files in `data/sample/personas/*.json`.

## Wow-factor stretch features (if you have time on Day 4)

1. **Interactive persona builder** — slider for hedonic/communal, dropdown for register tier, custom aspect input. Lets judges *feel* the architecture.
2. **Reasoning trace viewer** — when `include_reasoning=true` the API returns per-node trace; render as an expandable timeline.
3. **Streaming** — server-sent events; render token-by-token.

## Submission checklist

- [ ] Demo deployed at a public URL
- [ ] All 5 personas selectable
- [ ] At least 6 sample products across 3 categories
- [ ] Side-by-side compare panel works
- [ ] URL added to `JUDGES.md` and main `README.md`
