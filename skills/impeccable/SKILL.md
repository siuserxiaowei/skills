---
name: impeccable
description: Design, critique, audit, implement, or refine browser-based user interfaces using the project's real content, design system, interaction requirements, accessibility needs, responsive behavior, and performance evidence. Use for websites, landing pages, dashboards, app shells, forms, onboarding, empty states, component systems, UX copy, visual hierarchy, motion, and frontend quality reviews; do not use for backend-only work or silently modify code when the user asked only for diagnosis.
---

# Impeccable

Produce frontend work whose visual character, usability, accessibility, resilience, and delivery quality can all be explained and verified.

Read [references/examples.md](references/examples.md) only when distinguishing audit from implementation authority, explaining evidence levels, or forward-testing this Skill. Route ordinary work to the action-specific references below.

## Resolve the Requested Action

Choose one action before touching files:

- **Critique:** explain UX, hierarchy, content, interaction, and visual-system issues. Read-only unless the user also asks for fixes.
- **Technical audit:** inspect semantics, keyboard behavior, accessibility, responsive behavior, states, and performance. Read-only unless fixes are requested.
- **Shape:** turn a product need into a frontend brief, information architecture, states, and acceptance checks. Stop before implementation unless asked to build.
- **Build or redesign:** create a new surface or replace an existing visual direction while preserving product truth and required behavior.
- **Refine:** improve a bounded existing surface without changing its identity, copy, information architecture, or behavior outside scope.
- **Extract:** identify reusable tokens and components, then migrate only when the user authorizes code changes.

A request to review, critique, or diagnose is not authorization to edit. A request to improve, fix, redesign, or build normally includes implementation and proportionate verification.

## Establish the Evidence

Inspect the smallest complete set of sources that defines the surface:

1. Project instructions, target route or component, framework, build and test commands.
2. Real copy, data shape, user roles, permissions, primary tasks, and required states.
3. Existing tokens, theme, shared components, layout primitives, fonts, icons, and media, including provenance and usage rights for assets that may ship.
4. Current browser rendering at representative wide and narrow viewports when it can be run.
5. Product or brand documentation and earlier decisions, while checking them against the current implementation.
6. Accessibility, browser, device, localization, and performance targets.

Do not infer that a project is greenfield because a design document is missing. Existing code and rendered behavior are evidence. Preserve user changes and distinguish source files from generated output before editing.

For a new direction or broad redesign, read [references/design-decisions.md](references/design-decisions.md). For critique and audit, read [references/review-playbook.md](references/review-playbook.md). For implementation and refinement, read [references/implementation-playbook.md](references/implementation-playbook.md).

## Define the Surface Contract

Write a compact working brief containing:

- the user's job and the surface's primary outcome;
- real content hierarchy and primary/secondary actions;
- entry, success, failure, empty, loading, disabled, permission, offline, and recovery states that are relevant;
- what must remain invariant and what may change;
- design-system anchors and intentional exceptions;
- fonts, icons, photos, illustrations, and other assets that may ship, with their provenance, permitted use, and fallback;
- target viewports, input methods, languages, themes, and reduced-motion behavior;
- accessibility and performance acceptance checks;
- unknowns that must remain placeholders or be resolved with the user.

The surface may help someone choose, complete a task, understand information, or explore work. Optimize for that actual job. Do not force every marketing surface into a loud campaign, every product surface into a dense dashboard, or every redesign into the current visual trend.

## Make Design Decisions

Work from content and interaction outward:

1. **Structure:** reading order, landmarks, headings, grouping, disclosure, navigation, and task sequence.
2. **Hierarchy:** what must be noticed first, what supports it, and what can remain quiet.
3. **System:** color roles, typography roles, spacing, grid, shape, elevation, icon and media treatment, and state vocabulary.
4. **Behavior:** keyboard/pointer/touch interaction, focus movement, validation, async feedback, interruption, undo, and recovery.
5. **Adaptation:** narrow/wide layouts, content growth, zoom, localization, right-to-left direction, coarse pointers, and reduced motion.
6. **Character:** distinctive choices grounded in the product, audience, content, and brand evidence.

Avoid universal aesthetic bans. A font, gradient, card, border, animation, or asymmetric layout is good or bad only in context. Reject a choice when it harms hierarchy, comprehension, interaction, consistency, accessibility, performance, or the stated direction—not because it appears on a fashionable anti-pattern list.

Prefer native HTML behavior before custom ARIA widgets. When a custom composite is necessary, follow the applicable WAI-ARIA Authoring Practices keyboard and state pattern, then test the actual component.

## Use the Static Audit as a Lead Generator

The bundled auditor is read-only, uses only the Python standard library, never executes project code, and does not follow symlinks:

```bash
python3 scripts/audit_frontend.py path/to/project
python3 scripts/audit_frontend.py path/to/project --format json --fail-on high
```

It scans source HTML, JSX/TSX, Vue, Svelte, Astro, and CSS-family files for bounded signals such as missing document metadata, image alternatives/dimensions, unnamed controls, unlabeled literal form controls, positive `tabindex`, clickable non-controls, duplicate IDs, removed focus outlines, unbounded motion, `transition: all`, suspicious fixed widths, and token drift.

Every finding includes evidence, line, severity, confidence, and a verification step. Treat it as a triage list, not proof of accessibility, usability, visual quality, or performance. Review false positives and inspect runtime behavior before changing code.

## Implement Within the Existing System

- Reuse existing primitives and dependencies when they meet the contract.
- Preserve framework conventions, data flow, routes, analytics hooks, form names, legal copy, and external behavior unless the requested change requires otherwise.
- Use semantic elements and real controls. Keep DOM order meaningful; do not rely on CSS reordering to repair reading order.
- Keep content real. Do not invent customer logos, testimonials, metrics, prices, certifications, product states, or claims.
- Reuse or add fonts, icons, photographs, and illustrations only when their source and intended product use are allowed. Do not download a convenient asset, strip attribution, or bundle a third-party reference merely to complete the visual direction.
- Make state differences perceivable without relying on color alone.
- Define visible focus and predictable keyboard behavior.
- Reserve media dimensions, load critical media intentionally, and avoid shipping desktop-sized assets to narrow screens.
- Make motion explain change or provide feedback; give users a reduced-motion path and avoid blocking interaction on animation.
- Handle text expansion, long names, error messages, empty collections, slow responses, and unavailable permissions.
- Scope visual novelty to places where it improves the surface's job. Productive UI may need quiet precision; an expressive surface still needs a clear path and robust controls.

Do not install persistent hooks, start background services, forward credentials, spawn another Agent with bypassed permissions, or write global state as part of this Skill. Use the tools already available in the user's environment and keep every mutation inside the authorized project scope.

## Verify in Layers

Match evidence to the claim:

1. **Static:** lint, typecheck, unit/component tests, bundled audit, and changed-file review.
2. **Rendered:** wide and narrow screenshots, overflow, hierarchy, wrapping, media crop, theme, and state visibility.
3. **Interaction:** keyboard path, focus visibility/order/restoration, pointer/touch behavior, validation, async and recovery states.
4. **Accessibility:** semantic and accessible-name inspection plus the project's automated accessibility checks; manual screen-reader testing when the risk or target requires it.
5. **Performance:** real build output and lab evidence; field data for claims about Core Web Vitals. Lighthouse cannot directly measure field INP.
6. **Regression:** compare the target path and any shared components or tokens affected by the change.

Use at least one wide and one narrow viewport for responsive surfaces, plus any explicitly targeted breakpoint. A screenshot alone does not prove keyboard behavior, accessibility-tree correctness, localization resilience, or performance.

## Completion Evidence

Lead with the outcome and report:

- action performed and exact scope;
- preserved constraints and material design decisions;
- files or components changed, if any;
- static, rendered, interaction, accessibility, performance, and regression checks actually run;
- findings fixed, intentionally retained, or unverified;
- screenshots or artifact paths when created;
- remaining risks and the smallest next verification step.

Read [references/research-basis.md](references/research-basis.md) before changing accessibility, design-token, internationalization, or performance assumptions.
