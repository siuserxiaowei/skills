# Design Decisions

Use this reference for a new surface, broad redesign, or unresolved visual direction.

## Product Truth Before Style

Record:

- who uses the surface, in what situation, and with what prior knowledge;
- the single most important outcome and the cost of failure;
- real content, data density, permissions, compliance, and trust constraints;
- device, input, language, browser, network, and environment assumptions;
- existing brand/system elements that are mandatory, optional, or obsolete;
- what evidence would make the chosen direction successful.

If the content or product behavior is unknown, use clearly labeled placeholders and keep the uncertainty visible. Do not create persuasive-looking fiction.

## Decide Preserve, Extend, or Replace

- **Preserve:** the incumbent identity and structure are valid; change only the named defects.
- **Extend:** the system is valid but lacks patterns, states, tokens, or responsive rules needed by the new surface.
- **Replace:** the user requested a redesign or the existing world cannot satisfy the new contract. Preserve product truth and behavior while replacing the visual system deliberately.

Replacing a visual direction is a material decision. Explain what becomes obsolete and where shared components or tokens will change before applying a broad migration.

## Design-System Map

Describe roles rather than isolated values:

- **Color:** canvas, surface, text, muted text, border, focus, action, success, warning, danger, and data-series roles.
- **Typography:** display, page title, section title, body, label, caption, code, and numeric roles.
- **Space and grid:** container, columns, gaps, density, vertical rhythm, and breakpoint behavior.
- **Shape and depth:** radius, border, shadow, overlay, and selected/focused/disabled treatment.
- **Media and icons:** source, style, crop, focal point, alternative-text intent, and responsive delivery.
- **Motion:** entrance, transition, feedback, duration/easing families, interruption, and reduced-motion alternative.

When durable tokens are useful, use a documented token hierarchy and aliases rather than duplicating raw values. The current Design Tokens Community Group stable format is a useful interchange reference, but do not migrate an established project's token format without a concrete benefit.

## Responsive Contract

For each material layout change, state:

- what remains visible, moves, collapses, wraps, scrolls, or becomes progressive disclosure;
- whether DOM order stays meaningful;
- minimum viable control and text sizes;
- media crop/art direction and reserved aspect ratio;
- table, chart, navigation, dialog, and dense-tool behavior;
- expected behavior at zoom and text expansion.

Do not derive mobile solely by shrinking desktop. Do not hide essential functionality merely because space is scarce.

## Distinctiveness Without Fiction

Derive character from real inputs: product mechanism, audience culture, content, materials, imagery, motion behavior, brand history, or domain vocabulary. A distinctive choice must still support the surface's job.

Useful questions:

- What relationship should be recognizable even without the logo?
- Which one or two moments deserve visual emphasis?
- What may remain conventional because familiarity helps task completion?
- Which repeated rule creates coherence across the whole path?
- What would look wrong for this specific product, not merely unfashionable in general?
