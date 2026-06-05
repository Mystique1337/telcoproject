# Naija Persona Agent

Source: http://localhost:8765/

To create a video from this capture, use the `website-to-hyperframes` skill.

## What's in This Capture

| File | Contents |
|------|----------|
| `screenshots/contact-sheet.jpg` | **View this first.** All scroll screenshots in labeled grid — see the entire page at a glance |
| `screenshots/scroll-*.png` | Individual viewport screenshots if you need detail on a specific section. |
| `extracted/tokens.json` | Design tokens: 20 colors, 5 fonts, 9 headings, 2 CTAs |
| `extracted/design-styles.json` | Computed styles from live DOM: typography hierarchy, button/card/nav styles, spacing scale, border-radius, box shadows. Primary data source for DESIGN.md. |
| `extracted/asset-descriptions.md` | One-line description of every downloaded asset. Read this for asset selection — only open individual files for safe-zone checking. |
| `extracted/visible-text.txt` | Page text in DOM order, prefixed with HTML tag (`[h1]`, `[p]`, `[a]`). Use as context — rephrase freely. |
| `assets/contact-sheet.jpg` | All downloaded images in one labeled grid. |
| `assets/svgs/contact-sheet.jpg` | SVGs rendered as thumbnails in labeled grid |
| `assets/` | Individual downloaded images, SVGs, and font files. |

## Brand Summary

- **Colors**: #060912 (bg-dark), #F7F8FA (bg-light), #0A0E18 (accent), #2F3A4D (neutral), #EDF0F5 (bg-light), #008751 (accent), #6E7C92 (neutral), #FAFAFA (bg-light), #A8B3C4 (neutral), #003820 (accent)
- **Fonts**: InterVariable (100-900 variable), Inter var (100-900 variable), Inter (100,200,300,400,500,600,700,800,900), InterDisplay (100,200,300,400,500,600,700,800,900), Space Grotesk (500,600,700)
