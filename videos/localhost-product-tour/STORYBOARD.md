# STORYBOARD — Naija Persona Agent: 60-Second Product Tour

---

## Concept Block

**Message:** Nigerian consumer AI is finally here, and it's this fast — 24 culturally-grounded personas, structured results in under 2 minutes.
**Arc:** Problem → Solution → Demonstration (InsideNaija + ShopEasy) → Market Scale → CTA
**Audience:** Developers and product managers building products for the Nigerian market; watching on landing page or LinkedIn.
**Brand voice:** Quiet technical authority — confident, data-backed, no hype. Economy of words. Pauses are features.
**Why this matters now:** Zero culturally-native AI tools existed before Naija Persona. This video makes that argument and offers the exit: Get started free.

---

## Global Direction

**Format:** 1920×1080 landscape
**Pacing: Moderate** — 6 beats, CSS crossfades between most, domain-warp on opener, light-leak on CTA setup. Each beat 8–12s.
**Audio:** Kokoro TTS voiceover + underscore
**VO direction:** Calm, mid-range Nigerian-accented male voice, measured pace. Apple-keynote register — economy of words, deliberate pauses, each sentence gets its own breath. 2.2 words/sec.
**Narration start:** 1.2s (after opening visual flash settles)
**Style basis:** DESIGN.md — Near-Black Navy backgrounds, Nigerian Green CTAs, Bright Green stats, Space Grotesk display, Inter Variable body.
**Rhythm:** STRIKE → resolve → build → reveal → reveal → COUNT → LAND

**Shader transitions:**
- Beat 1 → Beat 2: `domain-warp` (4s) — dramatic problem-to-solution warp
- Beat 5 → Beat 6: `light-leak` (3.5s) — cinematic close before CTA

**CSS crossfades (everything else):** 0.8s ease-in-out between beats 2→3, 3→4, 4→5

**Underscore music direction:** Minimal electronic. Single sustained sub-bass pad already playing when the video starts. No melody — texture and weight only. It lives under everything and never competes with VO. A single bright harmonic layer swells faintly during beat 5 (the stats), then resolves to near-silence under beat 6. Tempo: atmospheric, no defined BPM.

---

## Required Capabilities Discovered

- Shader transitions available (installed): `domain-warp-dissolve`, `light-leak`
- Shader runtime names: `domain-warp`, `light-leak`
- VFX blocks: none installed (not needed — this video is composed entirely from CSS, SVG, kinetic type, and counter animations)
- Registry blocks available: `data-chart`, `logo-outro`, `flowchart` (none used — storyboard doesn't require them)

---

## Asset Audit

### SVG Contact Sheet (page 1 of 1 — only page)

```
Contact sheet: capture/assets/svgs/contact-sheet.jpg
5 most visually distinctive assets I see (filename + what's actually pictured):
1. lucide-users.svg: Two human silhouettes — the persona/people icon, represents the 24 personas panel
2. lucide-users-2.svg: Slightly different two-human silhouette variant — usable as a duplicate personas icon
3. lucide-cpu.svg: Microchip/CPU icon with pins — represents the AI model (NaijaReviewer-8B)
4. lucide-chart-column.svg: Bar chart icon — represents research-grade results, analytics
5. lucide-shopping-bag.svg: Shopping bag icon — represents ShopEasy product
Other assets: lucide-flask-conical.svg (Labz icon), lucide-github.svg (GitHub link), lucide-arrow-right.svg (×5 variants, navigation arrows), lucide-chevron-down.svg (dropdown), lucide-sun.svg (theme toggle)
```

### Raster contact sheet
- No raster images found in capture (`capture/assets/contact-sheet.jpg` did not exist). The brand uses no photography or illustration — only Lucide icons and typographic design.
- **Implication:** All beats are purely composed from CSS, typography, and the brand's Lucide SVGs. This is expected for this product — the visual identity IS the typography and color, not imagery.

### Asset USE/SKIP decisions

| Asset | Type | Where | Role |
|-------|------|--------|------|
| lucide-users.svg | SVG | Beat 3 | Primary icon badge — represents the 24 personas panel |
| lucide-shopping-bag.svg | SVG | Beat 4 | Primary icon badge — represents ShopEasy product |
| lucide-cpu.svg | SVG | Beat 2 | Accent — floats on the NaijaReviewer beat, represents the model |
| lucide-chart-column.svg | SVG | Beat 5 | Accent — data/analytics indicator on stats beat |
| lucide-arrow-right.svg | SVG | Beat 6 | Button arrow on CTA |
| lucide-flask-conical.svg | SVG | SKIP | Labz icon — not in this tour's scope (Labz is experimental/advanced) |
| lucide-github.svg | SVG | SKIP | Developer link — not relevant to this user-focused product tour |
| lucide-chevron-down.svg | SVG | SKIP | Navigation chrome — forbidden by storyboard rules |
| lucide-sun.svg | SVG | SKIP | Theme toggle — UI chrome, not video content |
| lucide-users-2.svg | SVG | SKIP | Duplicate of lucide-users, not needed |

**Brand defaults:**
- No branded logo SVG exists in the capture (wordmark is text-only). Beat 1 opens with a kinetic wordmark built from typography.
- Signature visual: the Nigerian green + near-black palette and Space Grotesk 700 ARE the brand. Every beat expresses this.

---

## Beat Structure

---

### BEAT 1 — THE GAP (0:00–0:09, 9s)

**Concept:** Cold open into the problem. No fade from black — a single word SLAMS on screen. The core tension is set up: Western AI doesn't know Nigeria. This beat exists to make the developer nod and feel seen before we offer the solution. It should feel like a statement, not an intro.

**Shot type:** Extreme close-up — one word at a time fills the frame, everything else absent.

**Camera move:** Dolly in — the entire composition scales 1.0 → 1.06 over the full 9s, with a subtle rightward x drift (+8px over 9s). Creates constant forward pressure on the viewer without any cuts.

**VO cue:** "Western AI doesn't know Nigeria. The language. The culture. The two-hundred and eighteen million consumers that every generic model gets wrong."

**Visual description:**
Deep Near-Black Navy canvas (#060912). The frame is empty except for building kinetic type. The word "WESTERN AI" slams in from below (y: 120 → 0, scale: 0.9 → 1.0, 0.28s, expo.out) in Space Grotesk 80px/700, Near-White (#F7F8FA). Then "DOESN'T KNOW NIGERIA." types word by word — each word punches in with scale 0.85→1.0 stagger. "NIGERIA." lands in Nigerian Green (#008751).

A secondary line fades in below (y: 20 → 0, opacity: 0→0.7, 0.6s, power2.out): "The language. The culture. The 218M consumers." in Inter Variable 20px/400, Muted Slate (#6E7C92).

Depth strategy: The primary text is the foreground. Behind it at 8% opacity: a grid of 24 tiny text labels (the four ethnic groups: Yoruba, Hausa, Igbo, Pidgin) arranged in a 6×4 ghost pattern — these barely-visible labels hint at what's coming. They slowly drift upward (y: 0 → -12px over 9s) using transform on the container.

**Composition (load-bearing):**
Composed from:
- `<div class="hero-text">` container with absolute positioning, centered
- Space Grotesk 80px/700 for "WESTERN AI" line
- Per-word split on "DOESN'T KNOW NIGERIA." — each word a `<span>` with stagger entrance
- Ghost grid: `<div class="ghost-grid">` — 24 `<span>` children, 4×6 arrangement, positioned with CSS grid, Inter Variable 11px/400, color #F7F8FA at 8% opacity, each containing a persona name + region
- Grain overlay: semi-transparent div with `background: url('data:image/svg+xml,...')` SVG noise, mix-blend-mode: overlay, opacity 0.06

**GSAP sequence:**
- 0.0s: Canvas is black, dolly-in begins (scale 1.0, will reach 1.06 at 9s)
- 0.2s: "WESTERN AI" SLAMS in (y: 120→0, scale: 0.85→1.0, 0.28s, expo.out)
- 0.6s: "DOESN'T" punches in (scale: 0.9→1.0, y: 20→0, 0.22s, back.out(1.4))
- 0.82s: "KNOW" punches in (same treatment, stagger 0.22s)
- 1.04s: "NIGERIA." punches in — but in Nigerian Green, with a subtle text-shadow `0 0 30px rgba(0,135,81,0.4)` bloom appearing simultaneously (0.3s)
- 1.5s: Secondary stats line fades up (opacity 0→0.7, y: 20→0, 0.6s, power2.out)
- 2.5s–9s: Ghost grid drifts (y: 0→-12px, 6.5s, none easing, linear) continuously; headline breathes with subtle letter-spacing pulse (0.02em variation, sine.inOut, 3s, yoyo)

**Text Animations:**
- "WESTERN AI" headline: `per-word-crossfade` → customized to have scale + y component (uses back.out overshoot)
- "DOESN'T KNOW NIGERIA." — each word: `spring-scale-in` — overshoot bounce entrance, stagger 0.22s
- Secondary stats line: `soft-blur-in` — blur 8px→0 with fade, 0.6s

**Accents:** None (beat carries itself with kinetic type)

**SFX:**
- `sfx/impact-bass-1.mp3` at 0.2s, volume 0.45 — on "WESTERN AI" slamming in (peak on impact, tail bleeds into next second)
- `sfx/click-soft.mp3` at 1.04s, volume 0.25 — on "NIGERIA." green landing

**Beat Timing:**
- Transition in at: 0s (first beat)
- GSAP timeline duration: 9s
- Transition OUT: domain-warp (into beat 2), starts at 8.2s

---

### BEAT 2 — THE SOLUTION (9:00–0:19, domain-warp transition included; effective beat duration ~11s)

**Concept:** The green line. After the domain-warp dissolves the problem beat, we emerge on the answer: a single horizontal Nigerian Green line has drawn itself across the frame. "Built for Nigeria." assembles from it. This is the philosophical turn — from adaptation to origin. The NaijaReviewer-8B model's identity lands as a badge.

**Shot type:** Medium — two-thirds of the frame occupied by the key message, the CPU icon as a smaller accent right.

**Camera move:** Push — at the moment "NIGERIA." lands in green, the composition pushes in fast (scale: 1.0 → 1.04, 0.35s, power3.out), then resumes slow dolly in to 1.07 over the rest of the beat.

**VO cue:** "Naija Persona is different. NaijaReviewer-8B was fine-tuned on Nigerian data — not a Western model with a Nigerian system prompt. A model that actually understands the culture."

**Visual description:**
Near-Black Navy canvas (#060912). A single horizontal line in Nigerian Green (#008751) DRAWS itself across the full 1920px width — scaleX: 0→1, 0.5s, expo.out, originating from center-left. This line is 2px high, positioned at 42% vertical.

Above the line: "Built for" appears first (Inter Variable 32px/400, Muted Slate #6E7C92), then "NIGERIA." ASSEMBLES letter by letter in Space Grotesk 72px/700, Near-White — each letter DROPS in with rotation from y: -60 and rotate: -8deg to 0, back.out(1.7) per letter, stagger 0.04s.

Below the line: "Not adapted." types on in Nigerian Green (#008751), Space Grotesk 24px/600, character by character.

Bottom left: A glowing badge/pill appears — "NaijaReviewer-8B" in Inter Variable 13px/500, #D8B4FE (Lavender), on a `#0A0E18` background with `1px solid #D8B4FE` border, `border-radius: 10px`, `padding: 6px 14px`. The lucide-cpu SVG precedes the label text in violet.

Right side (40% from right): `lucide-cpu.svg` rendered at 56×56, color #A855F7 (Violet), floats gently — y oscillates ±4px, sine.inOut, 2.2s, yoyo, starts at opacity 0 then fades in (0→0.65, 0.6s) when the badge appears.

**Composition (load-bearing):**
- Green divider line: `<div class="green-line">` — `width: 100%; height: 2px; background: #008751; transform: scaleX(0); transform-origin: left;`
- "Built for" label: `<span class="pre-headline">`
- "NIGERIA." title: per-letter spans inside `<div class="main-headline">`
- "Not adapted." subtitle: `<div class="sub-headline">` with character-level typing via GSAP `steps(N)` on a pseudo-element width/overflow clip approach
- Badge: `<div class="model-badge">` with SVG icon inline
- CPU icon: `<img src="../../capture/assets/svgs/lucide-cpu.svg">` positioned absolute, right side

**GSAP sequence:**
- 0.0s: Green line draws (scaleX: 0→1, 0.5s, expo.out)
- 0.5s: "Built for" fades up (opacity: 0→0.7, y: 10→0, 0.4s, power2.out)
- 0.8s: "NIGERIA." letters drop in — 7 letters, 0.04s stagger, 0.45s each, back.out(1.7)
- 1.4s: Camera push (scale 1.0→1.04, 0.35s, power3.out)
- 1.8s: "Not adapted." types on (45 chars at 0.035s/char = ~1.6s, steps easing)
- 2.8s: NaijaReviewer-8B badge slides up (y: 20→0, opacity: 0→1, 0.5s, back.out(1.4))
- 3.0s: CPU icon fades in (opacity: 0→0.65, 0.6s) and begins float oscillation
- 3.5s–11s: Hold with life — green line pulses brightness (opacity 0.85→1.0, sine.inOut, 1.8s, yoyo), "NIGERIA." headline has subtle letter-spacing drift (0→0.01em, sine.inOut, 2s, yoyo), CPU icon floats continuously

**Text Animations:**
- "NIGERIA." headline: `bottom-up-letters` — per-letter with back.out overshoot, stagger 0.04s
- "Built for" pre-label: `soft-blur-in`
- "Not adapted." typing: `typewriter` — steps(1,end) per character

**Accents:**
- `capture/assets/svgs/lucide-cpu.svg` — right side, 40% from right, 30% from top, 56×56, tinted Violet (#A855F7) via CSS filter or colored SVG, opacity 0.65, continuous float

**SFX:**
- `sfx/ping.mp3` at 0.0s, volume 0.35 — on green line drawing start (peak immediate)
- `sfx/sparkle.mp3` at 0.8s, volume 0.2 — as "NIGERIA." letters begin assembling (under VO, keep quiet)

**Beat Timing:**
- Transition in at: ~13s (domain-warp started at 8.2s in beat 1 + 4s transition = beats rendered at t=13s effectively; data-start for this beat should be set after the 4s domain-warp)
- GSAP timeline duration: 11s
- Transition OUT: CSS crossfade 0.8s → beat 3

---

### BEAT 3 — INSIDENAIJA: THE PANEL (0:24–0:37, ~13s)

**Concept:** The 24 personas materialize. They're not abstract icons — they're distinct people with names, regions, language registers. The research panel assembles itself from darkness like a grid coming online. Then one persona card expands to show a live feedback result, with the 48.5% win rate counter rising. This beat answers the question: "how does 'culturally grounded' actually work?"

**Shot type:** Close-up — the 24-persona grid fills 60% of frame. Pull-back mid-beat to reveal the grid in context with a result card alongside it.

**Camera move:** Dolly out — starts framed tightly (scale: 1.12) on the grid center, then slowly pulls back (1.12 → 1.0 over 8s) as the full grid assembles and the result appears. Creates the feeling of the system "opening up."

**VO cue:** "InsideNaija is a synthetic panel of 24 culturally-grounded Nigerian personas — Yoruba, Hausa, Igbo, Pidgin speakers. Structured feedback in under 2 minutes. 48.5% win rate versus Claude Sonnet."

**Visual description:**
Deep Navy canvas (#0A0E18) — the alternate section background.

Top: An eyebrow label "B2B · RESEARCH PANEL" in Inter Variable 12px/500, Muted Slate (#6E7C92), appears first with a green left-border pip (`3px solid #008751`). The lucide-users.svg renders at 16×16 in green before the label text.

Center-left: 24 persona mini-cards arranged in a 6×4 grid (each card ~110×56px). Each card shows:
  - A two-letter monogram circle (filled with one of 4 subtle colors — #008751 30% opacity, #A855F7 30%, #4CC079 30%, #2F3A4D — cycling across the 4 ethnic groups)
  - A persona name in Inter Variable 11px/600 Near-White
  - A region tag in Inter Variable 10px/400 Muted Slate

Cards appear with a stagger animation: rows reveal one by one, each card within a row staggers 0.06s, each row 0.2s apart. Entrance: y: 20→0, opacity: 0→1, scale: 0.9→1.0, 0.35s, power2.out.

At ~4.5s into the beat: one card (center row, second from left) "activates" — it expands (scale: 1.0 → 1.5, 0.4s, back.out(1.3)), border changes to `1px solid #008751`, and a mini feedback result appears to its right as a floating tooltip-style result card:
- Result card background: `#141925`, `border-radius: 10px`, `1px solid #2F3A4D`, padding 12px
- "Sentiment: Positive" in Bright Green (#4CC079), 12px/600
- 2 lines of truncated review text in Muted Slate, 11px
- A star row (5 filled circles in green)

Right column (detached, 30% width): "48.5%" counter — starts at 0.0%, counts up to 48.5 over 2.5s (GSAP tl.to on a text element, custom snap to 1 decimal). Below it: "Win rate vs. Claude Sonnet" in Inter Variable 13px/400 Muted Slate. This entire panel fades in at 5s into beat.

**Composition (load-bearing):**
- Grid wrapper: `<div class="persona-grid">` — CSS grid 6 columns × 4 rows, gap 8px
- Each card: `<div class="persona-card">` with monogram, name, tag
- Activated card: extra class `.activated` for expanded state transition
- Result card: `<div class="result-card">` positioned absolute relative to grid area
- Counter: `<span id="winrate-counter">` targeted by GSAP `tl.to({val: 0}, {val: 48.5, duration: 2.5, onUpdate: () => el.textContent = val.toFixed(1) + '%'})`
- Eyebrow: `<div class="beat-eyebrow">`
- lucide-users.svg: inline SVG in eyebrow

**GSAP sequence:**
- 0.0s: Eyebrow label appears (soft-blur-in, 0.4s)
- 0.3s: Row 1 (4 cards) fade in — y: 20→0, opacity: 0→1, stagger 0.06s, 0.35s each
- 0.5s: Row 2 appears (stagger continues)
- 0.7s: Row 3 appears
- 0.9s: Row 4 appears (all 24 cards now visible)
- 4.5s: Active card scales up (scale: 1→1.5, 0.4s, back.out(1.3)), border color transitions
- 4.7s: Result card slides in from right (x: 30→0, opacity: 0→1, 0.5s, power2.out)
- 5.0s: Counter starts (0→48.5, 2.5s, power2.out)
- 5.0s: Counter panel fades in (opacity: 0→1, y: 10→0, 0.5s)
- 7.5s: Counter settles; "48.5%" briefly pulses (scale: 1.0→1.08→1.0, 0.4s, elastic.out)
- 7.5–13s: Dolly-out continues; active card breathes (scale oscillates ±0.02, sine.inOut)

**Text Animations:**
- Eyebrow label: `soft-blur-in`
- Counter "48.5%": custom GSAP counter tween (not a text effect ID — procedural count-up)
- "Win rate vs. Claude Sonnet" sub-label: `micro-scale-fade`

**Accents:**
- `capture/assets/svgs/lucide-users.svg` — inline in eyebrow, 16×16, colored #008751

**SFX:**
- `sfx/click-soft.mp3` at 0.3s, volume 0.2 — on first row of cards appearing (under VO, quiet)
- `sfx/notification.mp3` at 4.7s, volume 0.3 — on result card appearing (after VO mentions "under 2 minutes")
- `sfx/chime.mp3` at 7.5s, volume 0.25 — on counter settling at 48.5%

**Beat Timing:**
- Transition in at: 24s (CSS crossfade from beat 2)
- GSAP timeline duration: 13s
- Transition OUT: CSS crossfade 0.8s → beat 4

---

### BEAT 4 — SHOPEASY: THE RECOMMENDER (0:37–0:50, ~13s)

**Concept:** The recommendation engine in motion. Three Nigerian product cards are shown ranked. Then a "Nigerian context signal" is applied and they re-rank — new order animates smoothly into place. The NDCG score appears as the ranking settles. This isn't showing a screenshot — it's showing the MODEL's judgment in action.

**Shot type:** Close-up — three product cards fill 65% of frame, vertically stacked, center-left.

**Camera move:** Parallax pan — the card column drifts from right-of-center (translateX: +40px) to center (translateX: 0) over 13s at constant speed, while a subtle depth layer in the background drifts opposite (translateX: -20px). Creates the feeling of camera moving through the scene.

**VO cue:** "ShopEasy powers persona-aware recommendations tuned to Nigerian shopping behaviour, cultural context, and language register. NDCG at ten: zero point five seven two — best of five models tested."

**Visual description:**
Near-Black Navy canvas (#060912).

Top: Eyebrow "B2C · RECOMMENDATION ENGINE" with lucide-shopping-bag.svg (16×16, #008751) and same green pip design as beat 3.

Center-left: Three product cards (each ~420×72px), stacked vertically with 10px gap. Each card has:
  - Rank number left (#1, #2, #3) in Space Grotesk 18px/700, Bright Green (#4CC079)
  - Product name in Inter Variable 15px/600, Near-White — real Nigerian Jumia product names: "#1 Tecno Spark 20C", "#2 Lekki Market Bag", "#3 Knorr Seasoning Cube Pack"
  - Right side: a small "Score" chip in Muted Slate

At 3.5s into the beat: "Nigerian Context Applied" label fades in above the cards, then the cards RE-ORDER — they animate to new y positions (power3.inOut, 0.6s), re-ranking. The new order: what was #3 becomes #1, with new product names showing different ranked preferences:
  "#1 Ankara Print Fabric", "#2 Indomie Noodles Pack", "#3 MTN Airtime Bundle"

The Rank numbers recount (#3→#1, etc.) with a number flip animation.

Right side (35% from right): "NDCG@10" label in Inter Variable 12px/500, Muted Slate. Below it: "0.572" counter counts from 0.000 to 0.572 over 2.0s (decimal counter tween). Then: "Best of 5 models" in Bright Green, 13px/500.

Background depth layer: extremely subtle — a pattern of 120 tiny shopping cart unicode characters (🛒) at 3% opacity, arranged randomly, drifting upward slowly. Does not compete visually but adds depth texture.

**Composition (load-bearing):**
- Cards: `<div class="product-cards">` with 3 `<div class="product-card">` children
- Rank reordering: GSAP timeline that animates `top` or `y` of each card to new positions
- NDCG counter: `<span id="ndcg-counter">` with GSAP decimal counter
- Background: `<div class="bg-texture">` with CSS-generated grid of tiny characters

**GSAP sequence:**
- 0.0s: Eyebrow label appears (0.4s, soft-blur-in)
- 0.4s: Cards 1, 2, 3 stagger in from right (x: 60→0, opacity: 0→1, stagger 0.15s, 0.5s each, power2.out)
- 3.5s: "Nigerian Context Applied" label appears (scale: 0.9→1.0, opacity: 0→1, 0.35s, back.out)
- 3.8s: Card rank numbers flip (previous number fades down, new number rises up)
- 3.9s: Cards rearrange — y positions transition (0.6s, power3.inOut) — card that was bottom flies to top
- 5.0s: NDCG counter panel fades in (0.5s); counter starts
- 5.0s: Counter counts 0.000 → 0.572 over 2.0s (power2.out)
- 7.0s: "Best of 5 models" lines up below (micro-scale-fade, 0.4s)
- 7.0–13s: Parallax pan continues; settled cards have a very subtle scale-breathe (1.0→1.005, sine.inOut, 1.8s, yoyo, staggered per card)

**Text Animations:**
- Eyebrow: `soft-blur-in`
- Product names (initial): `short-slide-right` — per-card stagger 0.15s
- "Nigerian Context Applied" label: `spring-scale-in`
- NDCG counter: custom decimal counter tween
- "Best of 5 models": `micro-scale-fade`

**Accents:**
- `capture/assets/svgs/lucide-shopping-bag.svg` — inline in eyebrow, 16×16, colored #008751

**SFX:**
- `sfx/whoosh-short.mp3` at 0.4s, volume 0.15 — cards sliding in (very quiet, under VO)
- `sfx/click.mp3` at 3.8s, volume 0.3 — on rank reorder triggering
- `sfx/pop.mp3` at 5.0s, volume 0.25 — on NDCG counter appearing

**Beat Timing:**
- Transition in at: 37s (CSS crossfade from beat 3)
- GSAP timeline duration: 13s
- Transition OUT: CSS crossfade 0.8s → beat 5

---

### BEAT 5 — THE OPPORTUNITY (0:50–1:00, ~10s)

**Concept:** The market scale, delivered as three facts that build in sequence. Not a slide — a revelation. "218M+" rises from zero and the number itself fills the frame. Then 15%. Then the devastating third: before Naija Persona, zero culturally-native AI tools existed. Each number is its own moment. The last number transforms.

**Shot type:** Wide — three stat columns arranged symmetrically, each takes ~28% of frame width, separated by vertical hairlines. Numbers are enormous (Space Grotesk 64px/700).

**Camera move:** Slow dolly in (scale: 1.0 → 1.05 over 10s) + slight rightward drift (+6px over 10s). Steady, inevitable forward motion.

**VO cue:** "Two-hundred-and-eighteen million Nigerians. Fifteen percent e-commerce growth every year. And until now? Zero culturally-native A I tools for the market."

**Visual description:**
Near-Black Navy canvas (#060912).

Three stat columns, centered as a group:

**Column 1 (Nigerians):**
- Eyebrow: "NIGERIANS" in Inter Variable 11px/500, Muted Slate, with Bright Green pip
- Stat: counter from 0 to 218, then "M+" suffix appends — rendered as "218M+" in Space Grotesk 64px/700, Bright Green (#4CC079)
- Sub-label: "Africa's largest consumer market" in Inter Variable 12px/400, Muted Slate

**Column 2 (E-Commerce):**
- Eyebrow: "E-COMMERCE GROWTH YOY"
- Stat: counter from 0 to 15, "%" suffix — "15%+" in same treatment
- Sub-label: "Fastest growing digital market on the continent"

**Column 3 (Gap):**
- Eyebrow: "CULTURALLY-NATIVE AI TOOLS"
- Stat: "0" appears (NOT a counter, just appears) in Space Grotesk 64px/700, Near-White — representing the void
- Sub-label: "Before Naija Persona" in Muted Slate
- At 7s into beat: The "0" SHATTERS via opacity+scale (scale: 1.0→0.3, opacity: 1→0, 0.35s, power3.in) — and is replaced by "NAIJA PERSONA" rising up (y: 30→0, opacity: 0→1, 0.5s, back.out(1.4)) in Space Grotesk 18px/700, Nigerian Green. The background of column 3 very subtly pulses with a green glow radial gradient (rgba(0,135,81,0.08) expanding from center).

Vertical hairlines: `1px solid #2F3A4D` between columns.
The lucide-chart-column.svg (20×20, #4CC079) appears as an accent in the top-right of column 1, fading in when that stat finishes counting.

Columns appear sequentially — column 1 at 0s, column 2 at 1.2s, column 3 at 2.4s (each fades up: y: 30→0, opacity: 0→1, 0.5s, power2.out).

**Composition (load-bearing):**
- Three-column flex layout: `display: flex; justify-content: center; gap: 0; align-items: flex-start;`
- Each column: `<div class="stat-col">` with eyebrow, stat, sub-label divs
- Hairlines: CSS `border-right: 1px solid #2F3A4D` on first two columns
- Counters: GSAP text counter tweens on stat spans
- Column 3 "0" shatter: scale + opacity tween, then GSAP.set on replacement text + entrance tween
- Column 3 glow: `<div class="col-glow">` absolute positioned radial-gradient div with GSAP opacity pulse

**GSAP sequence:**
- 0.0s: Column 1 appears (y: 30→0, opacity: 0→1, 0.5s, power2.out); counter 0→218M begins (2.0s)
- 1.2s: Column 2 appears; counter 0→15 begins (1.5s)
- 2.4s: Column 3 appears — the "0" just fades in (opacity: 0→1, 0.4s) — no counter (it's not growing, it's a void)
- 2.5s: chart-column icon fades in near column 1 (opacity: 0→0.6, 0.4s)
- 6.8s: VO approaches "zero culturally-native" — the "0" shatters (scale: 1→0.3, opacity: 1→0, 0.35s, power3.in)
- 7.0s: "NAIJA PERSONA" rises up in Nigerian Green (y: 30→0, opacity: 0→1, 0.5s, back.out(1.4))
- 7.1s: Column 3 glow begins pulsing (opacity: 0→0.12→0, 1.5s, sine.inOut)
- 7.5–10s: All three columns drift subtly in place; dolly continues

**Text Animations:**
- Column eyebrows: `soft-blur-in`, staggered 1.2s between columns
- Stat numbers: custom GSAP counter tweens
- Sub-labels: `mask-reveal-up`, triggered after counter finishes
- "NAIJA PERSONA" replacement: `per-word-crossfade` with y entrance component

**Accents:**
- `capture/assets/svgs/lucide-chart-column.svg` — column 1 top-right, 20×20, #4CC079, opacity 0.6

**SFX:**
- `sfx/impact-bass-2.mp3` at 0.0s, volume 0.4 — sets the weight as the first number begins rising
- `sfx/ping.mp3` at 2.4s, volume 0.3 — on "0" appearing (sharp, emphasizes the void)
- `sfx/impact-bass-1.mp3` at 7.0s, volume 0.45 — on "NAIJA PERSONA" landing (strongest SFX moment of the video)

**Beat Timing:**
- Transition in at: 50s (CSS crossfade from beat 4)
- GSAP timeline duration: 10s
- Transition OUT: `light-leak` shader, 3.5s, starts at 9.2s → transitions to beat 6

---

### BEAT 6 — START BUILDING (1:00 end; effective start after light-leak ~1:03, CTA beat ~8s)

**Concept:** The CTA isn't a slide — it's a moment. After the light-leak transition, we emerge in near-total darkness with a single green orb of light at center. It blooms outward into the CTA button. The wordmark is the last thing that appears. The viewer leaves with the action, the product name, and the exit.

**Shot type:** Extreme close-up — the CTA button and surrounding text fill 50% of frame at peak.

**Camera move:** No dolly — static composition. Instead, the button itself pulses with a slow breathing scale (scale: 1.0 → 1.02 → 1.0, sine.inOut, 2.4s, yoyo, repeat 1 after entering). Creates presence without movement.

**VO cue:** "Get started free. No credit card. First results in under 2 minutes."

**Visual description:**
Near-Black Navy canvas (#060912), deep grain overlay (0.08 opacity).

0.0s: Nothing visible. A green orb appears at center — `<div class="cta-orb">` — radial gradient (Nigerian Green `rgba(0,135,81,0.6)` → transparent), 300px diameter, blur(80px), scale 0 → 1.0 (0.5s, expo.out).

0.4s: "Start building for Nigeria today" resolves above from blur — Space Grotesk 36px/700, Near-White (#F7F8FA), with letter-spacing -0.5px. Text emerges from blur (blur: 20px→0, opacity: 0→1, 0.6s, power2.out). The orb's green glow provides the under-lighting.

1.0s: The CTA button SLAMS into place from below — `<button class="cta-btn">` with Nigerian Green background (#008751), white text "Get started free", Inter Variable 16px/500, border-radius 10px, height 48px, padding 0px 32px — enters with y: 60→0, scale: 0.85→1.0, 0.4s, back.out(2.0) (strong overshoot).

1.0s: lucide-arrow-right.svg (14×14, white) appears inline within the button text, sliding in from x: -8 to 0, 0.3s.

1.4s: "Free to try · No credit card · Under 2 minutes" sub-copy appears below the button — Inter Variable 14px/400, Muted Slate (#6E7C92), three parts separated by `·`, each part appearing 0.15s apart.

1.8s: "NAIJA PERSONA" wordmark appears above everything — Space Grotesk 14px/600, Near-White, letter-spacing 0.12em, uppercase, centered. It fades in (opacity: 0→0.5, 0.5s, power2.out) — intentionally understated, the brand name as a soft sign-off.

2.5s–8s: Button breathes (scale: 1.0→1.02→1.0, sine.inOut, 2.4s, yoyo repeat 1). Green orb breathes (opacity: 0.6→0.9→0.6, sine.inOut, 3s, yoyo). Headline drifts gently (y: 0→-3px, sine.inOut, 2s, yoyo). All held for last VO line + 2.5s.

**Composition (load-bearing):**
- Central orb: `<div class="cta-orb">` absolute centered, purely CSS radial-gradient + blur
- Headline: Space Grotesk display text
- Button: Standard HTML `<button>` styled from DESIGN.md Primary CTA spec
- Arrow: inline `<img src="../../capture/assets/svgs/lucide-arrow-right.svg">` within button
- Sub-copy: three `<span>` with separators inside a `<p>`
- Wordmark: `<div class="wordmark">` at very top center

**GSAP sequence:**
- 0.0s: Green orb blooms (scale: 0→1.0, opacity: 0→0.6, 0.5s, expo.out)
- 0.4s: Headline resolves from blur (blur: 20px→0, opacity: 0→1, 0.6s, power2.out)
- 1.0s: Button SLAMS in (y: 60→0, scale: 0.85→1.0, 0.4s, back.out(2.0)) — most kinetic moment of the beat
- 1.0s: Arrow slides in within button (x: -8→0, 0.3s, power2.out)
- 1.4s: Sub-copy appears — three spans, stagger 0.15s, each soft-blur-in
- 1.8s: Wordmark fades in (opacity: 0→0.5, 0.5s)
- 2.5s: Button breathe begins (scale: 1.0→1.02, sine.inOut, 2.4s, yoyo, repeat 1)
- 2.5s: Orb breathe begins (opacity: 0.6→0.9, sine.inOut, 3s, yoyo, repeat 1)

**Text Animations:**
- "Start building for Nigeria today" headline: `focus-blur-resolve` — blur→clarity emergence
- Sub-copy spans: `soft-blur-in` staggered per span
- Wordmark: `fade-through` — opacity only, gentle

**Accents:**
- `capture/assets/svgs/lucide-arrow-right.svg` — within CTA button, 14×14, white

**SFX:**
- `sfx/sparkle.mp3` at 1.0s, volume 0.5 — on button SLAMMING in (peak on impact — this is the emotional resolution of the video)
- `sfx/chime.mp3` at 1.8s, volume 0.2 — soft finish tone when wordmark appears

**Beat Timing:**
- Transition in at: ~62.7s (light-leak started at 59.2s, 3.5s duration)
- GSAP timeline duration: 8s
- Transition OUT: none (final beat — video ends)

---

## Brand Accents Summary

| Asset | Type | Beat | Role |
|-------|------|------|------|
| lucide-users.svg | SVG | Beat 3 eyebrow | Personas section badge — Nigerian Green |
| lucide-shopping-bag.svg | SVG | Beat 4 eyebrow | ShopEasy section badge — Nigerian Green |
| lucide-cpu.svg | SVG | Beat 2 right | NaijaReviewer model accent — Violet #A855F7 |
| lucide-chart-column.svg | SVG | Beat 5 col 1 | Stats accent — Bright Green #4CC079 |
| lucide-arrow-right.svg | SVG | Beat 6 CTA button | Button arrow — White |

---

## Real Timing (from transcript.json — ground truth)

**Narration start:** 1.2s into video (audio `data-start="1.2"`)
**Total audio duration:** 61.4s → last word ends at video 62.6s
**Total video duration:** ~69.4s (61.4s audio + 1.2s visual intro + CTA hold)

| Element | data-start | data-duration | Notes |
|---------|------------|--------------|-------|
| Beat 1 | 0 | 9.5 | VO: "Western AI..." ends at v9.64s |
| domain-warp transition | 9.5 | 4.0 | VO bridges: "Naija Persona is different..." |
| Beat 2 | 13.5 | 7.5 | VO: "NaijaReviewer-8B..." ends at v19.92s |
| CSS crossfade 2→3 | 21.0 | 0.8 | |
| Beat 3 | 21.3 | 14.0 | VO: "InsideNaija..." ends at v34.52s |
| CSS crossfade 3→4 | 35.3 | 0.8 | |
| Beat 4 | 36.1 | 12.0 | VO: "ShopEasy..." ends at v47.5s |
| CSS crossfade 4→5 | 48.1 | 0.8 | |
| Beat 5 | 48.9 | 9.5 | VO: "218M..." ends at v57.76s; light-leak at 57.9s |
| light-leak transition | 57.9 | 3.5 | VO bridges: "Get started free..." |
| Beat 6 | 61.4 | 8.0 | VO ends v62.56s; CTA hold 2.5s |

## Transitions Map

| Transition | Type | From→To | Duration | data-start (video time) |
|------------|------|---------|----------|------------|
| Beat 1 → 2 | `domain-warp` shader | Beat 1 → Beat 2 | 4.0s | 9.5s |
| Beat 2 → 3 | CSS crossfade | Beat 2 → Beat 3 | 0.8s | 21.0s |
| Beat 3 → 4 | CSS crossfade | Beat 3 → Beat 4 | 0.8s | 35.3s |
| Beat 4 → 5 | CSS crossfade | Beat 4 → Beat 5 | 0.8s | 48.1s |
| Beat 5 → 6 | `light-leak` shader | Beat 5 → Beat 6 | 3.5s | 57.9s |

---

## Production Architecture

```
videos/localhost-product-tour/
├── index.html                      root — VO + underscore + beat orchestration
├── DESIGN.md                       brand reference (Step 1)
├── SCRIPT.md                       narration text (Step 3)
├── STORYBOARD.md                   THIS FILE
├── transcript.json                 word-level timestamps (Step 4)
├── narration.wav                   TTS audio (Step 4)
├── capture/                        captured website data (Step 0)
│   ├── screenshots/
│   ├── assets/
│   │   ├── svgs/
│   │   │   ├── lucide-users.svg
│   │   │   ├── lucide-shopping-bag.svg
│   │   │   ├── lucide-cpu.svg
│   │   │   ├── lucide-chart-column.svg
│   │   │   └── lucide-arrow-right.svg
│   │   └── fonts/
│   │       ├── InterVariable.woff2
│   │       ├── InterVariable-Italic.woff2
│   │       └── V8mQoQDjQSkFtoMM3T6r8E7mF71Q-gOoraIAEj4PVksj.ttf (Space Grotesk 700)
│   └── extracted/
│       └── visible-text.txt
└── compositions/
    ├── beat-1-gap.html
    ├── beat-2-solution.html
    ├── beat-3-insidenaija.html
    ├── beat-4-shopeasy.html
    ├── beat-5-opportunity.html
    └── beat-6-cta.html
```
