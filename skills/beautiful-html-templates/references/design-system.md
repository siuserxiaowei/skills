# Original Design System

## Start With Visible Axes

Choose a position on each axis from the brief:

| Axis | Quiet end | Energetic end |
|---|---|---|
| Contrast | close tonal values, restrained accent | strong light/dark split, assertive accent |
| Density | one idea with generous space | several tightly grouped evidence items |
| Geometry | soft rhythm, few rules | explicit grid, borders, modules |
| Type | text-led, conventional roles | scale-led, compressed labels, expressive display role |
| Imagery | sparse, documentary, captioned | image-led, cropped, sequenced |
| Motion | direct state change | brief transition that explains sequence |

Translate the choices into semantic tokens rather than a named style imitation.

## Token Contract

The builder accepts:

- `background`: outer and slide canvas;
- `panel`: cards, notes, and control background;
- `text`: primary text;
- `muted`: secondary text and source lines;
- `accent`: focus, progress, marks, and deliberate emphasis;
- `line`: borders and dividers;
- `font_pair`: `modern`, `editorial`, `technical`, `humanist`, or `system`.

All colors are six-digit sRGB hex values. Primary and muted text must meet at least 4.5:1 against their used background; accent use in the baseline UI also needs 4.5:1 because it carries text and focus cues. The builder rejects failed pairs, but rendered contrast still needs review where opacity, images, or browser styling changes the result.

The font pairs use only system stacks. They are roles, not brand claims:

- `modern`: platform sans for display and body;
- `editorial`: platform serif display with platform sans body;
- `technical`: platform sans display/body with a mono data role;
- `humanist`: readable UI-oriented sans stacks with softer proportions;
- `system`: the browser/platform defaults with minimal opinion.

## Cohesion Without a Catalog

Repeat a small number of decisions:

- one margin system;
- one display scale and one body scale;
- one corner or border treatment;
- one source/caption pattern;
- one progress/navigation treatment;
- one image crop rule;
- one transition behavior.

Variation should follow slide job: a cover, dense evidence slide, and close can differ in composition while sharing tokens and rhythm. Do not duplicate the same card grid on every slide merely for consistency.

## Extending the Baseline

When adding a new layout:

1. state the content job it enables;
2. reuse semantic tokens and type roles;
3. keep DOM reading order aligned with the visual order;
4. define narrow, short-viewport, print, reduced-motion, and no-JavaScript behavior;
5. add a representative test spec;
6. render it between existing slides and check whether hierarchy, not ornament, creates cohesion.

New layout code is justified by a recurring communication need, not by a desire for another template count.

## Reference Use

From a reference, record only general observations such as “high-contrast single accent,” “asymmetric two-column grid,” “small source footer,” or “documentary image crop.” Combine and transform them for the current subject. Do not lift distinctive arrangements, decorative assets, illustrations, slogans, or a complete token set.
