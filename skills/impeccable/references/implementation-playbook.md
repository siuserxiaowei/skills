# Implementation Playbook

Use this reference immediately before changing a frontend.

## Plan the Smallest Coherent Change

Identify:

- target routes/components and shared dependencies;
- preserve/extend/replace decision;
- design tokens and primitives to reuse or add;
- required content and states;
- data, analytics, accessibility, and performance contracts;
- tests and rendered viewports that will prove completion.

Prefer one coherent system change over scattered pixel overrides. Avoid broad refactors that do not improve the requested path.

## Structure

- Keep meaningful DOM order aligned with reading and focus order.
- Use headings and landmarks to expose page structure.
- Use button, link, input, select, textarea, details, dialog, table, and list semantics when they match the behavior.
- Give custom widgets explicit state, accessible names, keyboard behavior, focus management, and tests based on the applicable platform pattern.
- Keep destructive and irreversible actions distinct and confirm them in proportion to impact.

## Content and State

- Preserve factual and legal copy unless the user authorizes changes.
- Make labels describe the action or information, not the visual location.
- Put validation near the field and provide a recoverable summary when needed.
- Preserve user input across recoverable errors.
- Distinguish no data, no results, no permission, unavailable service, and loading.
- Define focus destination after dialogs, deletion, navigation, insertion, and asynchronous updates.

## Visual System

- Use semantic tokens or established variables for repeated roles.
- Maintain readable line length, hierarchy, contrast, and text spacing across real content.
- Keep interactive states consistent: default, hover when relevant, focus, active, selected, disabled, loading, error, and success.
- Avoid color as the only state signal.
- Apply a deliberate spacing/grid rule instead of local nudges.
- Preserve recognizable brand assets and licensed media; do not redraw them casually.

## Responsive and International

- Test content growth rather than only placeholder strings.
- Allow wrapping and intrinsic sizing before adding truncation.
- Use logical properties where they improve direction independence.
- Declare language and direction correctly; test mixed-direction content when applicable.
- Keep primary actions reachable with keyboard, pointer, and touch.
- For dense tables or tools, choose a documented narrow-screen behavior instead of hiding columns arbitrarily.

## Motion and Performance

- Animate transforms/opacity when they achieve the effect; measure expensive layout/paint work rather than relying on a blanket rule.
- Make animation interruptible and avoid delaying input or content access.
- Provide a meaningful reduced-motion alternative.
- Reserve space for media and late content.
- Deliver responsive image candidates and intentional art direction.
- Avoid lazy-loading critical above-the-fold media; verify the actual LCP candidate.
- Diagnose INP as input delay, handler work, and presentation delay; optimize the measured bottleneck.

## Finish

Render the whole affected path, not only the component in isolation. Fix root causes first, then re-run the smallest complete verification set. Stop when the acceptance checks pass and remaining differences are explicit; do not keep polishing without a new evaluator or user decision.
