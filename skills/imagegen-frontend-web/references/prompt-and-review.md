# Prompt and Review Playbook

Use this reference while constructing prompts, editing a selected image, or reviewing an output.

## Six Visible Dimensions

Describe what can be observed rather than relying on labels such as “premium,” “cinematic,” or “anti-slop.”

1. **Subject:** people, products, UI objects, action, quantity, identity, geometry, and relationships.
2. **Environment:** location, time, depth, background, surface, material, and contextual objects.
3. **Visual language:** palette roles, texture, shape, edge treatment, image grade, typography temperament, and density.
4. **Light:** direction, softness, temperature, contrast, reflection, shadow, and atmosphere.
5. **Camera/composition:** framing, viewpoint, lens feel, perspective, subject position, safe area, and negative space.
6. **Layout:** canvas, grid, hierarchy, exact short copy, alignment, live-text region, and responsive crop intent.

Add constraints in three groups:

- **Preserve:** identity, geometry, brand colors, camera, layout, transparent background, or other invariants.
- **Change:** the smallest observable change requested in this iteration.
- **Do not introduce:** extra text, logos, watermarks, objects, controls, people, color shifts, or background changes.

## Web-Specific Prompt Record

For a page or section concept, capture:

```text
Deliverable: responsive homepage concept, desktop frame first
Audience and job: ...
Primary action: ...
Content hierarchy: ...
Design-system anchors: ...
Viewport/canvas: ...
Subject/environment/style/light/composition/layout: ...
Live-text safe regions: ...
Preserve: ...
Change: ...
Do not introduce: ...
Acceptance checks: ...
```

Name real content as real and placeholders as placeholders. Do not invent testimonials, customer logos, security claims, prices, performance figures, or product screens that could be mistaken for evidence.

## Text Strategy

Choose one strategy per frame or asset:

- `live-overlay`: the image reserves safe areas; the implementation supplies semantic text and controls.
- `placeholder-only`: generated copy communicates hierarchy only and must not ship.
- `essential-raster`: the wording and appearance are inseparable from the image; provide a reason and an accessible equivalent.
- `no-text`: the image contains no meaningful text.

For exact text inside a concept image:

- quote the literal text;
- specify placement, hierarchy, case, weight, contrast, and number of occurrences;
- keep wording short;
- review character by character at full size;
- regenerate or replace with live text when accuracy is insufficient.

Do not approve functional UI based solely on pixels. Buttons, inputs, focus, validation, hover, expanded states, and responsive order need a structured implementation specification.

## Iteration Protocol

1. Generate one diagnostic frame.
2. Compare it with the acceptance checks.
3. Name the largest observable miss.
4. Edit that miss while repeating the preserve list.
5. Reinspect the whole frame for drift.
6. Only after direction approval, produce the remaining required viewports, states, or assets.

If two revisions fail for the same reason, change the representation or split the task. Examples: generate the hero art without text, render typography in code, use separate mobile art direction, or provide a wireframe plus an asset instead of a monolithic screenshot.

## Visual Inspection Checklist

At full size:

- exact spelling, labels, prices, units, dates, and product geometry;
- hands, faces, repeated objects, cutout edges, transparency, unwanted shadows, and watermarks;
- alignment, baseline, crop, safe area, visual hierarchy, and component consistency;
- sufficient contrast for intended text and controls;
- identity and brand invariants across edits.

At target size:

- primary message and action remain obvious;
- text is not merely technically present but unreadable;
- the focal subject survives the crop;
- small controls are not depicted below practical target sizes;
- the image does not require horizontal scrolling to understand ordinary page content.

For a coordinated set:

- tokens, type roles, radius/shape language, illustration or photo grade, and CTA hierarchy stay coherent;
- variation follows page jobs and viewport needs rather than random novelty;
- every extra frame resolves a different implementation question.
