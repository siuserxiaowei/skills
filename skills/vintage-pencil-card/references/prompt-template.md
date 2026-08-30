# Prompt template

Use this scaffold to assemble an edit prompt. Keep only the blocks relevant to the request.

```text
Use Image 1 as the sole content authority. [If supplied: Use Image 2 only as a detail anchor for ... . Use Image 3 only for paper, pencil texture, palette, spacing, and mood; do not copy its subject, pose, objects, or composition.]

Asset type and use
Transform the source into a [horizontal 3:2 / vertical 4:5 / source-matched] vintage colored-pencil card for [use].

Preserve exactly
[List the visible identity, pose, geometry, object count, spatial relationships, crop anchors, lighting facts, and source-specific details that must not drift.]

Edit instructions
[Describe only what changes: background replacement, scene-wide redraw, crop adaptation, palette, paper, or optional crayon accents.]

Composition
[State subject position, scale, negative space, horizon height, foreground/middle/background layers, and crop behavior. If orientation changes, explain how the source is re-framed without reversing or inventing features.]

Style and material
Refined hand-drawn colored-pencil illustration on warm ivory fibrous handmade paper. Fine graphite underdrawing; layered dry pencil strokes; sparse broad wax-crayon accents only in peripheral areas; low-saturation Morandi palette; slight paper aging and faint Risograph grain. The focal subject is most detailed, supporting forms are moderately simplified, and peripheral marks are loosest. Quiet, healing, literary vintage stationery mood. Flat tactile illustration, restrained contrast, no heavy cast shadow and no photorealistic rendering.

Text
No text, logo, or watermark. [If exact text is required, quote it once and specify placement, hierarchy, and legibility; prefer adding it after image generation.]

Constraints
Do not change [critical source invariants]. Do not add [likely invented objects]. No generic cartoon face, anime, chibi, thick black outline, plastic skin, 3D render, oil-paint impasto, watercolor wash, or photographic background unless explicitly requested.
```

## Subject modules

Append one module after `Preserve exactly`.

### Person

```text
The person must remain immediately recognizable as the same individual. Preserve real facial proportions, face shape, hairline, eye shape and spacing, eyebrows, nose and mouth placement, ears, expression, age, skin tone, body proportions, pose, hand and foot placement, clothing silhouette, collar, folds, and key patterns. Do not enlarge eyes, slim the face, beautify features, change age or ethnicity, or substitute a generic illustration face. The face receives fine graphite and colored-pencil detail; broad wax crayon is background-only.
```

### Pet

```text
Preserve species and breed cues, skull and muzzle proportions, eye placement, ear shape and angle, coat length, exact color patches and markings, tail shape, pose, paw placement, collar, and expression. Do not humanize the face, enlarge the eyes, shorten the muzzle, or replace the coat pattern with a generic one.
```

### Landscape

```text
Preserve horizon height, major landform silhouettes, shoreline or river path, road direction, foreground anchors, depth layers, weather, reflection pattern, and light direction. Redraw the whole scene; do not treat the environment as removable background. Do not reverse the scene, flatten depth, relocate terrain, or add people, buildings, vehicles, boats, wildlife, or a visible sun unless present.
```

### Architecture

```text
Preserve camera viewpoint, vanishing lines, massing, roofline, facade rhythm, door and window count and placement, structural proportions, stairs, signage location, and relationship to adjacent space. Simplify texture, not geometry. Keep verticals and perspective coherent; do not invent floors, openings, ornaments, or landscaping.
```

### Still life or product

```text
Preserve object count, silhouette, proportions, overlap order, camera angle, color blocks, material cues, key hardware, and arrangement on the surface. Simplify micro-texture but do not merge objects, change packaging shape, invent accessories, or alter functional geometry. Add exact brand text only when the user explicitly requires it.
```

## Split-card module

For a strict photo/illustration card, append:

```text
Canvas is divided horizontally into two exact halves. The top 50% is an intelligently cropped but otherwise untouched source photograph. The bottom 50% is warm handmade paper with a narrow, irregular horizontal color field sampled from the photo. Draw a simplified dark matte wax-pencil outline of the source's main subject across that field. Leave ample blank paper above and below the drawing. No extra decoration. If exact preservation of the top photograph matters, generate the bottom panel separately and composite it with the source crop rather than regenerating the photograph.
```
