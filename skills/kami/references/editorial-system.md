# Editorial System

## Choose Structure by Reader Job

| Artifact | Productive structure | Common failure |
|---|---|---|
| One-pager | decision or promise → 3–5 evidence blocks → risks/next action | nine equal cards with no reading order |
| Report | executive finding → method/scope → evidence sections → limitations → recommendations/references | decorative cover followed by undifferentiated prose |
| Letter or memo | context → purpose → requested action → supporting detail → close | inflated tone that hides the request |
| Resume | target role → selected scope/outcomes → experience/evidence → skills/education as relevant | duties without scale, action, or result |
| Portfolio | positioning → selected cases → problem/action/evidence/outcome → contact or next step | screenshots without authorship or outcome |
| Slide deck | opening question → assertion-led sequence → evidence → decision/close | topic labels, paragraphs, and speaker notes placed on slides |
| Landing page | category/value → proof → how it works → objections/FAQ → action | invented testimonials, duplicated CTAs, or visual effects before product truth |

These are starting structures, not slot counts. Remove unsupported sections instead of fabricating content to fill them.

## Content Compression

1. Extract atomic facts and required quotations.
2. Group facts by the reader question they answer.
3. Write the smallest accurate claim supported by each group.
4. Put detail in captions, notes, appendix, or references only when the reader can still find it.
5. Compare the result against the inventory; record intentional omissions.

Avoid deleting caveats that change a claim, rounding numbers without noting it, converting correlation into causation, or converting a user's aspiration into an achieved result.

## Type and Measure

- Use type roles—display, heading, body, caption, code or data—not a collection of arbitrary sizes.
- Start from the platform's readable system stack. Add a brand font only when it contributes more than it costs in rights, loading, and fallback risk.
- Test the actual language. CJK, Arabic, Devanagari, Latin, and mixed-script text have different line breaking and font coverage needs.
- Keep body measure intentionally readable; do not use narrow columns for dense tables or excessively wide lines for prose.
- Use tabular numerals only when numerical comparison needs them. Keep decimals, signs, units, and date formats consistent.

## Layout and Page Flow

- Build one dominant reading path. Sidebars and callouts are secondary, not parallel articles.
- Align elements to a small grid and spacing scale. Optical corrections are allowed when documented by the render.
- In print CSS, set `@page` size/margins, use `break-before`, `break-after`, and `break-inside` intentionally, and set sensible `widows` and `orphans` where supported.
- Never assume a CSS paged-media feature is interoperable because it appears in a draft specification. Verify with the actual renderer and target version.
- Fix overflow by editing structure or content before shrinking below the established body-size floor.

## Figures, Tables, and Images

- Name the question a figure answers before choosing its form.
- Preserve the underlying values and units. Include a source and `as_of` date for external data.
- Use a table when exact lookup matters; use a chart when pattern or comparison matters; use prose when there are too few values to justify either.
- Give complex images a short identification and a nearby long description, data table, or equivalent explanation.
- Do not use color as the only distinction. Check labels, patterns, order, and contrast at the final size.
- Reserve intrinsic image dimensions on screen and inspect crops at every promised viewport.

## Language and Locale

- Set the document language and use BCP 47 tags; mark passages in another language when useful.
- Use the correct base direction and test mixed-direction strings, numbers, punctuation, and icons.
- Localize dates, numbers, currency, quotation marks, names, addresses, and line-break behavior—not just sentences.
- Re-run fit and reading-order review for every locale. Translation is a new content shape.

## Visual Direction

Derive direction from the subject, audience, brand, and medium. Record:

- three concrete qualities the artifact should express;
- semantic color roles and contrast constraints;
- type roles and fallback stacks;
- layout rhythm and image treatment;
- what existing identity must remain recognizable;
- visual conventions explicitly rejected by the user.

Do not default every artifact to parchment, ink blue, serif type, rounded cards, or any other fixed house style. Consistency should come from the current contract, not from the Skill's personality.
