---
name: kami
description: Create, restructure, typeset, or quality-check professional documents and static publication surfaces such as one-pagers, reports, letters, resumes, portfolios, slide decks, and landing pages. Use when the user needs content distilled into a polished editable or rendered artifact with source fidelity, print or responsive layout, font and asset rights, accessibility, and delivery evidence; do not use for dynamic application UI, backend work, or diagnosis-only requests that do not authorize edits.
---

# Kami

## 案例入口

先读 [references/examples.md](references/examples.md)：其中给出正向案例、边界案例、失败恢复和可观察的验收证据；再按下文流程执行。

Turn source material into a publication-ready artifact without inventing facts, imposing a house style, or confusing a successful export with a verified deliverable.

## Route the Request

Choose the narrowest artifact that serves the user's decision or action:

- **One-pager:** one claim, essential evidence, and one next action.
- **Report or white paper:** a sustained argument with traceable sources, sections, figures, and references.
- **Letter or memo:** a named sender, recipient, purpose, requested action, and appropriate tone.
- **Resume or portfolio:** selective evidence for a target role or audience; never fabricate scope, metrics, clients, or outcomes.
- **Slide deck:** an assertion-led sequence built for presenting. Editable slides require a real presentation format, not renamed HTML or screenshots.
- **Static landing page:** a responsive browser surface with a defined conversion or information goal. Route dynamic application UI to a frontend implementation workflow instead.

For a text correction or translation in an existing artifact, preserve its structure and visual identity unless the new content creates a demonstrated fit or accessibility defect. For critique-only requests, inspect and report; do not edit.

## Lock the Delivery Contract

Resolve these before production, inferring from the request and supplied material when safe:

1. audience and the job the artifact must accomplish;
2. language, locale, reading direction, and tone;
3. source material, facts requiring verification, and `as_of` dates;
4. artifact kind, editable source format, rendered formats, and length or page range;
5. brand elements and assets that must be used, preserved, or excluded;
6. accessibility claim, target devices or page size, and acceptance evidence;
7. privacy, licensing, deadline, and publication constraints.

Ask one compact question only when a missing choice would materially change the artifact. Never read a user-home profile or unrelated project by default. Use external files or sibling projects only when the user identifies them as inputs.

For multi-file or high-stakes delivery, record the contract in `delivery.json` using [the artifact contract](references/artifact-contract.md). For a small local draft, an equivalent concise note is enough.

## Establish Source Truth

- Inventory every supplied fact, quote, number, date, name, link, and required asset before editing.
- Verify current claims against primary sources. Record the source URL or file and date; distinguish verified fact, user-provided claim, inference, and open question.
- Preserve atomic facts through condensation. If a fact does not fit, list it as intentionally omitted rather than silently losing it.
- Mark missing evidence as a gap. Do not create placeholder metrics, approximate logos, synthetic testimonials, or decorative stock imagery that implies a real product or customer.
- Treat resumes, letters, financial material, customer data, and unpublished plans as sensitive. Keep them inside the user-authorized workspace and expose only what the deliverable requires.

## Choose the Production Path

Prefer, in order:

1. the user's existing editable artifact and its native toolchain;
2. an installed document, presentation, spreadsheet, PDF, or browser artifact capability that can produce the requested real format;
3. semantic HTML with screen and print CSS for documents or static pages;
4. a transparent source-only handoff when the required renderer is unavailable.

Do not install dependencies, download fonts, register background services, start an MCP server, or write global configuration merely to finish a document. If a renderer or conversion tool is missing, report the missing capability and the smallest reproducible next step. Never label a screenshot deck as editable PPTX or an untagged PDF as accessible.

The optional [neutral HTML starter](assets/editorial-starter.html) is a structural baseline, not a visual identity. Copy it into the working directory and replace its marked content; adapt the project tokens instead when a real design system exists.

## Shape Content Before Styling

Build an outline that maps source evidence to the artifact's job:

- lead with the decision, promise, thesis, or role fit;
- group supporting evidence into a small number of meaningful sections;
- make headings informative rather than decorative;
- let every chart, diagram, quote, table, and image answer a named question;
- place the next action, risk, qualification, or reference where the reader needs it;
- remove repetition before shrinking typography or crowding the page.

Artifact-specific structures and quality bars are in [editorial-system.md](references/editorial-system.md).

## Design From Context

- Preserve established brand and document conventions unless the user asks for a new direction.
- Define semantic tokens for background, text, muted text, accent, border, spacing, measure, radii, and type roles. Do not hard-code a universal palette or serif preference.
- Use hierarchy, alignment, grouping, measure, and whitespace before decoration.
- Test real copy, long names, large numbers, translations, and empty or missing sections. A template filled with idealized text is not evidence.
- Use system fonts by default. A custom font requires a documented source, redistribution or use rights appropriate to the deliverable, an integrity record for bundled files, and an offline fallback. Never fetch a font at render time without explicit approval.
- Give complex figures a short identification plus an adjacent long description, data table, or equivalent explanation. Color alone must not carry meaning.

## Implement for the Medium

For HTML, use a declared language, UTF-8, a meaningful title, logical headings, landmarks, real lists/tables, alt text, and responsive behavior. Keep content in the DOM; do not turn paragraphs or charts into inaccessible screenshots.

For print or PDF output, set page size and margins intentionally, control fragmentation, preserve selectable text, inspect every page, and verify document metadata. CSS paged-media behavior varies by renderer, so test the actual export engine.

For slide decks, keep one primary assertion per slide, use speaker-visible evidence, and verify both the editable source and a rendered view. For landing pages, verify keyboard use, focus, reflow, loading/error states when present, and narrow/wide viewports.

## Verify in Layers

Run only checks that match the claims being made:

1. **Content:** source coverage, factual support, gaps, names, numbers, links, and citations.
2. **Structure:** semantic hierarchy, reading order, tables, lists, labels, alt/long descriptions, and language.
3. **Render:** every page or target viewport, clipping, overflow, page breaks, crop, font substitution, density, and contrast.
4. **Interaction:** keyboard path, focus, links, forms, motion preference, and responsive states for screen surfaces.
5. **Format:** the promised files open in the intended application and retain promised editability, metadata, links, and text selection.
6. **Accessibility:** report the exact tests and tools used. Automated or visual review alone cannot prove WCAG or PDF/UA conformance.

Use `python3 scripts/validate_delivery.py delivery.json` to validate a recorded bundle before handoff. The validator is read-only: it checks manifest consistency, safe local paths, evidence coverage, basic HTML structure, asset rights records, and SHA-256 inventory; it does not render, execute project code, or certify accessibility. See [verification.md](references/verification.md).

## Deliver Honestly

Lead with the artifact paths and outcome. Then state:

- editable and rendered formats produced;
- checks run and the evidence inspected;
- every unresolved content or material gap;
- any unverified visual, accessibility, font, or conversion claim;
- the smallest next step when a requested format could not be produced.

Use `draft`, `verified`, or `blocked` precisely. A file that merely exists is still a draft until its promised render and format evidence have been inspected.

## References

- [Artifact contract](references/artifact-contract.md)
- [Editorial system](references/editorial-system.md)
- [Verification and failure handling](references/verification.md)
- [Research basis and upstream review](references/research-basis.md)
