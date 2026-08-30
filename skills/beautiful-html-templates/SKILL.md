---
name: beautiful-html-templates
description: Design, generate, adapt, or review a self-contained HTML slide deck when the user wants a browser-based presentation rather than PPTX, Keynote, or a document. Use for talks, pitches, lessons, research briefings, demos, and event decks that need an original visual direction, semantic slide structure, keyboard navigation, responsive and print behavior, source fidelity, asset rights, and browser evidence; do not use when the user requires a natively editable presentation file or asks only for critique without edits.
---

# Beautiful HTML Templates

## 案例入口

先读 [references/examples.md](references/examples.md)：其中给出正向案例、边界案例、失败恢复和可观察的验收证据；再按下文流程执行。

Create an original deck system from the user's content and context. Do not select from or imitate a catalog of fixed third-party visual expressions.

## Confirm the Medium

Use this Skill only when HTML is an acceptable primary format. If the user needs editable PowerPoint, Keynote, Google Slides, or another native deck, use the appropriate presentation workflow. Do not rename HTML, screenshots, or a PDF as an editable deck.

For critique-only requests, inspect the existing deck and report findings without rewriting it. For an existing deck the user wants changed, preserve accepted content, behavior, and identity unless the requested change requires otherwise.

## Lock the Deck Brief

Infer from the request and supplied material whenever possible:

- audience, occasion, venue or viewing context, and presentation duration;
- the decision, learning outcome, or action the deck should produce;
- language, locale, reading direction, and speaker needs;
- source facts, `as_of` dates, citations, and material gaps;
- slide-count range and expected density;
- brand constraints, required assets, and prohibited motifs;
- output path, offline requirement, print/PDF need, and browser evidence.

Ask one compact question only when a missing choice would materially change the story or visual direction. Do not force every user through an occasion/mood questionnaire. When the brief is truly visually open, show two or three low-cost direction specimens using the user's real title—not three complete copied templates—and let the user choose.

## Build the Story Before the Theme

1. Inventory the user's claims, names, numbers, quotations, dates, links, and assets.
2. Verify current claims from primary sources and separate verified fact, user statement, inference, and unresolved gap.
3. Define one assertion or question per slide. Put detail that competes with listening into notes or a handout.
4. Arrange the sequence: context → tension/question → evidence → synthesis → decision or close. Change the sequence when the communication job calls for it.
5. Map each slide to a layout only after its job is clear.

Never invent metrics, customer logos, testimonials, citations, product screenshots, or image rights to satisfy a layout. See [deck-workflow.md](references/deck-workflow.md).

## Derive an Original Direction

Choose visible decisions from the brief:

- contrast and atmosphere;
- type roles using offline system stacks;
- grid, margins, density, and negative space;
- geometry and border language;
- image crop and caption behavior;
- one restrained motion rule, if motion serves comprehension;
- repeated chrome such as section label, progress, or source footer.

Record the semantic theme tokens and a short rationale. Do not preserve a font, palette, decoration, or layout merely because it came from a template. Do not copy a recognizable composition from a reference deck. Translate references into general properties, then design for the current subject. Direction recipes and extension rules are in [design-system.md](references/design-system.md).

## Generate a Safe Starting Deck

Use the standard-library builder when its layouts fit:

```bash
python3 scripts/build_deck.py assets/deck.example.json --check
python3 scripts/build_deck.py path/to/deck.json --out path/to/deck.html
```

The JSON spec supports `cover`, `section`, `bullets`, `two-column`, `metrics`, `quote`, `image`, and `closing` layouts. It validates language, content density, colors, contrast, image rights and paths, then creates one self-contained HTML file with no external font, script, stylesheet, or network dependency. It escapes audience content rather than accepting raw HTML.

The builder is a baseline, not a ceiling. Extend the generated CSS and semantic markup in the user's workspace when the communication need exceeds the supplied layouts. Preserve source JSON as the editable content model. Never overwrite an existing output without explicit `--force` or an equivalent user-authorized change.

## Accessibility and Interaction Contract

- Use native buttons for previous/next controls and leave `Tab` navigation to the browser.
- Give the deck an accessible name and each slide a group role, slide role description, and unique label.
- Do not auto-advance. If future work adds rotation, it needs an explicit start/stop control and must stop on focus.
- Support Arrow, Page Up/Down, Home, and End without stealing keys from links, buttons, or editable controls.
- Announce the current slide, maintain deep-linkable hashes, and keep every slide available when JavaScript is disabled.
- Respect `prefers-reduced-motion`; avoid flashing, continuous motion, and decorative animation that competes with reading.
- Keep projected text and essential visuals legible at distance. Provide accessible material outside screen sharing when required.
- Give complex figures an identifying alt plus a visible detailed description or equivalent data.

## Responsive, Offline, and Print Behavior

The default deck keeps a 16:9 stage on presentation screens, becomes a scrollable content surface on narrow/short viewports, and prints one slide per landscape page. Test the actual content: long titles, translated text, URLs, data labels, footnotes, and notes.

System fonts are the default. Custom fonts or external assets require explicit user need, documented rights, integrity/provenance, an offline fallback, and rendered re-verification. Never depend on mutable Google Fonts URLs or remote runtime assets for a deck promised to work offline.

## Verify Before Handoff

1. Run the builder's `--check` mode and resolve every error; review warnings rather than suppressing them.
2. Run a static HTML audit as a lead, not as proof.
3. Open the actual file in the target browser and inspect every slide at the presentation viewport.
4. Test keyboard controls, focus, hashes, notes, reduced motion, and no-JavaScript reading order.
5. Inspect at least one narrow phone viewport and the required wide viewport; verify every shipped locale.
6. Print or export when promised and inspect every page for clipping, hidden content, broken links, and font substitution.
7. Reconcile every source fact and asset; disclose remaining gaps.

Report exact evidence. A generated HTML file is a draft until rendered, interacted with, and checked in the promised environments. Detailed checks and failure handling are in [deck-workflow.md](references/deck-workflow.md).

## Deliver

Provide the absolute source JSON and HTML paths, the visual direction in one sentence, the checks and browsers/viewports actually used, and any unverified format, asset, or accessibility boundary. Say `draft`, `verified`, or `blocked` accurately.

## References

- [Deck workflow and verification](references/deck-workflow.md)
- [Original design system](references/design-system.md)
- [Research basis and upstream review](references/research-basis.md)
