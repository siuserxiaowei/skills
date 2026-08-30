# Review Playbook

Use this reference for critique or technical audit. Keep observed facts, likely impact, and recommendations separate.

## Evidence Model

For every material finding record:

- location and state;
- observed behavior or code evidence;
- affected user/task;
- severity and confidence;
- applicable project requirement or external standard;
- recommended change and how to verify it.

Do not assign numerical scores unless the rubric, weights, and evidence are explicit. Do not label subjective taste as an accessibility or usability defect.

## Critique Pass

Review the surface in the user's likely order:

1. **Orientation:** purpose, current location, next action, and trust are understandable.
2. **Information architecture:** content groups and navigation match user concepts.
3. **Hierarchy:** reading order, emphasis, density, and progressive disclosure support the task.
4. **Content:** labels, help, errors, empty states, and calls to action are specific and truthful.
5. **Interaction:** affordances, feedback, selection, interruption, undo, and recovery are predictable.
6. **System:** typography, color roles, spacing, shape, icons, and repeated components are coherent.
7. **Character:** expression is intentional and appropriate rather than generic or distracting.

Critique should identify the smallest set of root causes. Ten symptoms caused by one missing hierarchy rule are one systemic finding, not ten unrelated complaints.

## Technical Audit Pass

Cover applicable evidence across:

- semantic structure, headings, landmarks, labels, accessible names and descriptions;
- keyboard operation, visible focus, focus order/restoration, and custom-widget conventions;
- contrast, color-independent states, zoom/reflow, target size, text spacing, and reduced motion;
- wide/narrow layout, orientation, overflow, touch/coarse pointer, and content expansion;
- loading, empty, error, success, disabled, permission, offline, destructive, and recovery states;
- language declaration, UTF-8, local names/dates/numbers, bidirectional text, and right-to-left layout;
- media alternatives, intrinsic dimensions, responsive candidates, crop, lazy loading, and provenance;
- bundle/runtime behavior, LCP candidates, long interactions, layout shift, and field versus lab evidence;
- component and token drift, duplicated patterns, and undocumented exceptions.

Use native HTML controls where possible. WAI-ARIA APG examples are informative patterns, not automatic proof that a custom component conforms.

## Severity

- **High:** blocks a primary task, creates data/safety risk, or has strong evidence of a serious accessibility failure.
- **Medium:** materially impairs comprehension, efficiency, resilience, consistency, or a secondary path.
- **Low:** bounded polish, maintainability, or weak-signal issue with limited immediate impact.

Confidence is independent of severity:

- **High confidence:** directly observed in runtime or deterministically established in source.
- **Medium confidence:** strong static signal that needs one runtime check.
- **Low confidence:** heuristic or incomplete-context signal; investigate before changing.

## Verification Matrix

| Claim | Minimum useful evidence |
|---|---|
| Visual hierarchy improved | before/after rendering at target viewports |
| Keyboard path works | manual keyboard traversal with focus observations |
| Accessible name is correct | accessibility tree or tested semantic query |
| Responsive defect fixed | render at affected and adjacent widths with real content |
| State is resilient | component/integration test plus rendered state |
| Performance improved | comparable build/lab trace; field data for field claims |
| Core Web Vitals pass | 75th-percentile field data segmented appropriately |
| Design system is consistent | token/component inventory and affected-path review |
