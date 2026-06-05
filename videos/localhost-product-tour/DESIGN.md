# DESIGN.md — Naija Persona Agent Brand Cheat Sheet

---

## 1. Visual Theme

Naija Persona Agent is deep-dark and purposeful — all five page sections sit on `#060912` (Near-Black Navy) or the marginally lighter `#0A0E18`, with zero light-mode UI anywhere. The accent palette is bifurcated: Nigerian Green (`#008751`) carries all primary action signals (a deliberate nod to the Nigerian flag), while Violet (`#A855F7` / `#D8B4FE`) marks the experimental "Labz" track. Display text is set in Space Grotesk, lending the brand a technical-yet-confident tone — not clinical, not playful, but precise. Hierarchy is achieved through size extremes: the hero headline drops to 72px/700 while body metadata lives at 14px/400, with very little in between. The overall mood is quiet authority — a developer tool that doesn't need to shout.

---

## 2. Quick Reference

### Colors

- **Near-Black Navy** (`#060912`): Primary page background, nav background
  - As surface: use `#F7F8FA` text → 19.4:1 ✅ / use `#EDF0F5` text → 18.2:1 ✅
- **Deep Navy** (`#0A0E18`): Alternate section background (features/why section)
  - As surface: use `#F7F8FA` text → ~18:1 ✅
- **Nigerian Green** (`#008751`): Primary CTA button, success indicators
  - On Near-Black Navy: 4.5:1 ✅ AA — On Near-White (`#F7F8FA`): 4.3:1 ⚠ AA-Large only; add `#006B40` for small text on light bg
- **Bright Green** (`#4CC079`): Stats emphasis, data highlights
  - On Near-Black Navy: 9.1:1 ✅ / On Deep Navy: 8.8:1 ✅ — safe for all sizes
- **Violet** (`#A855F7`): Labz experimental accent, purple UI markers
  - On Near-Black Navy: 5.2:1 ✅ / On Deep Navy: 5.0:1 ✅ AA
- **Lavender** (`#D8B4FE`): Labz nav tab border/text, soft purple highlights
  - On Near-Black Navy: 11.7:1 ✅ / On Deep Navy: 11.2:1 ✅
- **Near-White** (`#F7F8FA`): Primary heading text, hero headline
  - On Near-Black Navy: 19.4:1 ✅
- **Soft White** (`#EDF0F5`): Feature card headings (h3 level)
  - On Near-Black Navy: 18.2:1 ✅ / On Deep Navy: 17.8:1 ✅
- **Muted Slate** (`#6E7C92`): Body copy, secondary descriptions
  - On Near-Black Navy: 4.9:1 ✅ AA / On Deep Navy: 4.7:1 ✅ AA — ⚠ borderline, do not make smaller than 14px
- **Steel Blue** (`#A8B3C4`): Caption text, metadata labels
  - On Near-Black Navy: 8.4:1 ✅ / On Deep Navy: 8.1:1 ✅
- **Border Subtle** (`#2F3A4D`): Card borders, dividers on dark bg
- **Border Light** (`#D6DCE6`): Used on white bg / Sign-in button border — **do not use on dark**
  - `#D6DCE6` on `#060912`: 12.8:1 ✅ — OK if intentionally used as text on dark surfaces

### Fonts

- **Display / Heading:** `"Space Grotesk"` — hero headline, section headings, product names
  - 700: `capture/assets/fonts/V8mQoQDjQSkFtoMM3T6r8E7mF71Q-gOoraIAEj4PVksj.ttf`
  - 600: `capture/assets/fonts/V8mQoQDjQSkFtoMM3T6r8E7mF71Q-gOoraIAEj42Vksj.ttf`
  - 500: `capture/assets/fonts/V8mQoQDjQSkFtoMM3T6r8E7mF71Q-gOoraIAEj7aUUsj.ttf`
- **Body / UI:** `"Inter Variable"` (variable 100–900 via `font-variation-settings: 'wght' <value>`) — body text, labels, nav, captions
  - Variable regular: `capture/assets/fonts/InterVariable.woff2`
  - Variable italic: `capture/assets/fonts/InterVariable-Italic.woff2`
- **Fallback stack:** `-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`

**`@font-face` block — copy verbatim into every composition:**

```css
@font-face {
  font-family: "Space Grotesk";
  src: url("../../capture/assets/fonts/V8mQoQDjQSkFtoMM3T6r8E7mF71Q-gOoraIAEj4PVksj.ttf") format("truetype");
  font-weight: 700;
  font-display: block;
}
@font-face {
  font-family: "Space Grotesk";
  src: url("../../capture/assets/fonts/V8mQoQDjQSkFtoMM3T6r8E7mF71Q-gOoraIAEj42Vksj.ttf") format("truetype");
  font-weight: 600;
  font-display: block;
}
@font-face {
  font-family: "Space Grotesk";
  src: url("../../capture/assets/fonts/V8mQoQDjQSkFtoMM3T6r8E7mF71Q-gOoraIAEj7aUUsj.ttf") format("truetype");
  font-weight: 500;
  font-display: block;
}
@font-face {
  font-family: "Inter Variable";
  src: url("../../capture/assets/fonts/InterVariable.woff2") format("woff2");
  font-weight: 100 900;
  font-style: normal;
  font-display: block;
}
@font-face {
  font-family: "Inter Variable";
  src: url("../../capture/assets/fonts/InterVariable-Italic.woff2") format("woff2");
  font-weight: 100 900;
  font-style: italic;
  font-display: block;
}
```

**Type scale:**

| Role       | Family        | Size  | Weight | Line-height | Letter-spacing |
|------------|---------------|-------|--------|-------------|----------------|
| Display    | Space Grotesk | 72px  | 700    | 72px (1)    | -1.8px         |
| H2         | Space Grotesk | 30px  | 700    | 36px        | -0.6px         |
| H3 Large   | Space Grotesk | 20px  | 700    | 28px        | -0.4px         |
| H3 Small   | Space Grotesk | 16px  | 600    | 24px        | -0.32px        |
| Stats      | Inter Variable | 36px | 700    | 40px        | normal         |
| Body       | Inter Variable | 16px | 400    | 24px        | normal         |
| Caption    | Inter Variable | 14px | 400    | 20px        | normal         |
| Nav        | Inter Variable | 16px | 400    | —           | normal         |

---

## 3. Component Stylings

#### Primary CTA Button (Nigerian Green)

- **Background:** `#008751`
- **Text color:** `#FFFFFF`
- **Font:** Inter Variable 16px / 500
- **Padding:** `0px 32px`
- **Border radius:** `10px`
- **Border:** none (transparent)
- **Height:** `48px`
- **Box shadow:** none
- **Hover:** background `#006B40`, slight scale `1.01`

#### Secondary Button (Sign In / Ghost Outline)

- **Background:** `#000000` (opaque black, sits on near-black bg)
- **Text color:** `#D6DCE6`
- **Font:** Inter Variable 16px / 500
- **Padding:** `0px 10px`
- **Border radius:** `10px`
- **Border:** `1px solid #D6DCE6`
- **Height:** `48px`
- **Box shadow:** none

#### Labz Accent Button (Violet outline)

- **Background:** `#000000`
- **Text color:** `#D8B4FE`
- **Font:** Inter Variable 16px / 500
- **Padding:** `0px 10px`
- **Border radius:** `10px`
- **Border:** `1px solid #D8B4FE`
- **Height:** `48px`

#### Navigation Bar

- **Background:** `#060912`
- **Text color:** `#F7F8FA`
- **Font:** Inter Variable 16px / 400
- **Padding:** `12px 24px`
- **Height:** `61px`
- **Border radius:** `0px`
- **Border / shadow:** none (flat, no separator)

#### Stat Card / Counter Block

- **Background:** transparent (lives directly on section bg)
- **Stat value:** Inter Variable 36px / 700, color `#4CC079`
- **Stat label:** Inter Variable 14px / 400, color `#6E7C92`
- No border, no shadow, no card background — raw numbers on dark bg

#### Feature Card (Why Naija section)

- **Background:** transparent or very subtle `rgba(255,255,255,0.03)`
- **Icon container:** `#0A0E18` with accent-colored icon (green for data, violet for AI)
- **Heading:** Space Grotesk 16px / 600, color `#EDF0F5`
- **Body:** Inter Variable 14px / 400, color `#6E7C92`
- **Border radius:** `10px`
- **Border:** `1px solid #2F3A4D` (very subtle on dark)
- **Padding:** `24px`

#### Section Divider / Opportunity Rail

- Full-bleed section with `#060912` background
- Green data number (`#4CC079`) as the visual anchor
- Stats presented in a horizontal row with `40px` gap between items

---

## 4. Spacing & Layout

#### Spacing scale

**Base unit:** `8px`

| Token | Value  | Used for                                                   |
|-------|--------|------------------------------------------------------------|
| xs    | `4px`  | Icon-to-text gaps, tight badge padding                     |
| sm    | `8px`  | Button group gaps, compact component padding               |
| md    | `12px` | Inline element gaps                                        |
| base  | `16px` | Card internal padding, form field spacing                  |
| lg    | `24px` | Nav padding, card padding                                  |
| xl    | `32px` | CTA button horizontal padding, section sub-element gaps    |
| 2xl   | `40px` | Between stat items, major component separation             |
| 3xl   | `48px` | Button height, section rhythm                              |
| 4xl   | `64px` | Large section separation                                   |

#### Border-radius scale

- `0px`: Nav bar
- `10px` (`0.625rem`): All interactive elements — buttons, cards, badges ← **the only radius in the system**
- Full pill (`9999px`): Not used on this site

#### Whitespace philosophy

Dark, editorial, breathing room. Section vertical padding is implicitly generous — sections are 340–550px tall with limited content, creating strong whitespace. Horizontal content is constrained to a centered max-width (~1200px) with `24px` minimum edge padding. The brand does not crowd content — it trusts the dark background as a visual element in itself.

---

## 5. Iteration Guide

1. **Background is always `#060912` or `#0A0E18`** — never go lighter than `#0A0E18` for any composition surface. This is a dark-only brand; no white or gray panels.

2. **All primary actions use Nigerian Green (`#008751`)** — CTA buttons, success states, call-to-action copy highlights. For small text on dark bg, `#22B35D` is the lighter-safe variant (passes AA at 14px). **No other CTA color exists.**

3. **Violet (`#A855F7` / `#D8B4FE`) is reserved for the Labz / experimental track only** — use it to mark anything experimental, AI-model-specific, or "coming soon." Do not use violet as a generic accent.

4. **Space Grotesk at 700 for all display and section headings; Inter Variable for everything else.** There is no italic body text in the brand. Never use Space Grotesk below 16px.

5. **Stats get `#4CC079` (Bright Green), NOT `#008751` (CTA Green)** — the brand uses two greens with distinct roles. Nigerian Green = action. Bright Green = data/achievement. Never swap them.

6. **Border radius is `10px` everywhere** — no sharp corners, no pill shapes. One radius, all components, no exceptions.

7. **Muted Slate (`#6E7C92`) is the floor for body text on dark** — never go darker than this for readable text. At 14px, verify WCAG AA (4.9:1 on `#060912` ✅ — borderline; use `#A8B3C4` for anything below 14px or where readability is critical).

8. **No shadows anywhere** — the brand uses no box-shadow or drop-shadow. Depth is expressed through color layering (`#060912` vs `#0A0E18`) and border-color contrast (`#2F3A4D` borders on dark surfaces), never elevation shadows.
