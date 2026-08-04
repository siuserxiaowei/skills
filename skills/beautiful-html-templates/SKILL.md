---
name: beautiful-html-templates
description: A library of 34 reusable, beautifully designed HTML slide-deck templates. Use when the user wants a polished HTML presentation/slide deck — read AGENTS.md for the full workflow (match the user's occasion and mood against index.json, preview three candidates, then clone and adapt the chosen template).
---

# beautiful-html-templates

A library of reusable HTML slide templates designed so that any coding agent can pick the right one and produce a beautiful deck on the user's behalf, automatically.

## How to use

Read [`AGENTS.md`](./AGENTS.md) first — it is the operating manual for every deck-building task. In short:

1. Ask the user about the **occasion** and the **mood** they want.
2. Read [`index.json`](./index.json) and pick three candidate templates whose `mood` / `tone` / `best_for` / `formality` fit.
3. Build a title-slide preview of each candidate with the user's real content, open all three in the browser, and let the user pick.
4. Clone the chosen template's folder from [`templates/`](./templates/) into the user's workspace and adapt every slide: preserve the design system (fonts, palette, layout, decorations, navigation runtime), replace all placeholder content.
5. Open the final deck in the browser and send the user the absolute file path.

## What's inside

- `index.json` — the library-wide template index the matcher reads.
- `AGENTS.md` — the full operating manual (workflow, adaptation rules, pitfalls).
- `templates/<slug>/` — one self-contained folder per template: `template.html`, `template.json` (metadata), `design.md` (design-system notes), and `deck-stage.js` where needed.
- `runtime/deck-stage.js` — the shared slide-stage scaler copied into templates that use it.
- `scripts/` — maintenance utilities (`build-index.mjs` rebuilds `index.json`; `new-template.mjs` scaffolds a new template).

## License

[MIT](./LICENSE).
