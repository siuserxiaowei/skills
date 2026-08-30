---
name: vintage-pencil-card
description: "Transform one or more reference photos into composition-faithful vintage colored-pencil cards. Use for portrait, pet, landscape, architecture, still-life, or mixed-scene photo-to-illustration requests that need subject-specific preservation, handmade-paper texture, muted Morandi color, and optional photo/illustration split layouts."
---

# Vintage Pencil Card

## 案例入口

先读 [references/examples.md](references/examples.md)：其中给出正向案例、边界案例、失败恢复和可观察的验收证据；再按下文流程执行。

Turn a supplied photo into a quiet, tactile colored-pencil card without losing the identity or scene structure that makes the source recognizable.

## Start with the input contract

Assign every attached image one role before writing the prompt:

- **Image 1 — content authority:** controls subject, identity, pose, object count, scene geometry, and composition.
- **Image 2 — detail anchor, optional:** controls only close facial features, coat pattern, product detail, or another explicitly named feature.
- **Image 3 — style reference, optional:** controls only paper, pencil texture, palette, spacing, and mood. Never copy its subject, pose, objects, or composition.

If the user did not label the images, infer roles from context and state the assumption briefly. One clear content image is enough. Do not request a style image when a textual style specification will work.

Inspect each local image before editing it. Use the platform's image-editing path and pass the actual content image as a reference; do not rely on a text-only description when the source is available.

## Route by subject type

Classify the content image as `person`, `pet`, `landscape`, `architecture`, `still-life`, or `mixed`. Then load the matching preservation rules from [references/preservation-rules.md](references/preservation-rules.md).

Apply this priority order:

1. Recognizability and source truth.
2. Pose, geometry, and spatial relationships.
3. Requested crop and card layout.
4. Colored-pencil material and palette.
5. Decorative looseness.

Do not let style words override the first three priorities.

## Choose the layout

Use one of these modes:

- **Full illustration — default:** convert the subject and required scene into one colored-pencil illustration on warm handmade paper.
- **Paper portrait:** keep a person or pet detailed, remove the distracting photographic background, and add restrained loose crayon accents around generous negative space.
- **Whole-scene card:** preserve and redraw the complete landscape, architecture, or still life. Do not remove a landscape's “background”; it is part of the subject.
- **50/50 split card:** top half is the original photo crop and bottom half is the paper illustration, each exactly 50% of canvas height. When pixel-faithful photography is mandatory, generate only the lower illustration panel and composite the untouched source crop deterministically; generative editing alone cannot guarantee unchanged pixels.

Match the source orientation unless the user asks for a new one. When changing orientation, name the invariants that must survive the crop.

## Build the prompt

Read [references/prompt-template.md](references/prompt-template.md) and fill it with visible facts from the source. A strong prompt contains:

- asset type and intended aspect ratio;
- reference roles;
- an explicit **Preserve exactly** block;
- the requested changes only;
- subject, environment, material, light, framing, and text treatment;
- a short exclusion list tied to likely failure modes.

Prefer concrete source facts over vague instructions such as “keep it similar.” For a portrait, name face shape, hair silhouette, expression, pose, clothing, and age. For a landscape, name horizon height, landforms, water or road paths, foreground anchors, weather, depth layers, and light direction.

## Render the card look

Unless the user supplies a different art direction, use this default system:

- warm ivory handmade paper with visible natural fibers;
- fine graphite underdrawing and layered colored pencil;
- very light peach and rose pencil for skin;
- low-saturation dusty rose, cream ochre, sage, gray blue, muted teal, umber, and charcoal;
- focal subject most detailed, supporting forms moderately simplified, peripheral wax-crayon marks loosest;
- slight paper aging and faint Risograph grain;
- large quiet negative space, restrained contrast, and no heavy cast shadow;
- no text by default because generated lettering is unstable; add exact text later when typography matters.

## Generate and verify

Generate one considered composition first. Compare it against the source on four axes:

1. **Identity:** same person, pet, object, or place?
2. **Structure:** same pose, anatomy, horizon, perspective, shoreline, road, opening count, or object arrangement?
3. **Material:** clearly colored pencil on fibrous paper rather than watercolor, oil paint, 3D, or a photo filter?
4. **Restraint:** no generic cartoon face, invented objects, thick outlines, heavy shadows, unwanted text, logo, or watermark?

If one axis fails, iterate with one targeted correction. Start with: `Keep everything else unchanged. Correct only ...` Re-state the exact source invariant and the visible target. Do not rewrite the entire art direction unless the style itself failed.

Use [references/examples.md](references/examples.md) when explaining the Skill to a user or adapting the workflow to a new subject class.
