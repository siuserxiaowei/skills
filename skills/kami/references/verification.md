# Verification and Failure Handling

## Evidence Matrix

| Promise | Minimum evidence | What it does not prove |
|---|---|---|
| Content-complete | source inventory mapped to final sections; names/numbers/links checked | factual truth of unverified user claims |
| Responsive HTML | rendered screenshots at contracted widths/locales; keyboard and focus pass | every device, browser, or assistive technology |
| Print-ready | actual export; every page inspected; size, margins, breaks, crop, links, and selectable text checked | PDF/UA or print-shop preflight unless tested separately |
| Editable deck | source opens in the intended presentation app; elements remain editable; rendered deck inspected | cross-suite fidelity without opening those suites |
| Accessible HTML | semantic and accessibility-tree inspection plus keyboard, reflow, contrast, and applicable interaction tests | formal WCAG conformance from an automated score alone |
| Accessible PDF | tag tree, reading order, language, title, alt text, tables/lists/links, keyboard behavior, and appropriate PDF/UA-capable validation | conformance when the generator cannot preserve tags |
| Licensed assets | source, rights, license, attribution, and redistribution boundary recorded | legal advice or rights beyond the recorded license |

## HTML Review

- declared UTF-8 and document language;
- unique descriptive title, one clear main region, logical headings;
- lists and tables represented structurally;
- images have appropriate short alternatives; complex figures have equivalent detail;
- no unresolved markers, broken local references, hidden overflow, or clipped focus;
- print and screen styles both preserve content order;
- narrow and wide viewports, real content growth, zoom, keyboard, and reduced motion where applicable.

## PDF Review

- correct page size, count, orientation, margins, crop, and bleed requirement;
- no blank, duplicated, clipped, sparse-by-accident, or overfull pages;
- text remains searchable/selectable when promised;
- links, title, author when appropriate, language, and bookmarks when appropriate;
- fonts render consistently and are embedded or substituted within the contract;
- reading order and tags tested separately from appearance;
- every rendered page viewed at normal size and zoomed for small text/graphics.

W3C PDF techniques are informative examples, not a substitute for the WCAG success criteria. ISO 14289-2:2024 defines PDF/UA-2 for PDF 2.0; do not claim it merely because a PDF opens or contains tags.

## Slides and Landing Pages

For slides, inspect the editable file and rendered frames. Check overflow, notes, video/font portability, chart legibility, image rights, and the presenting environment. For static landing pages, check the primary action, navigation, links, forms if present, default/focus/error/loading states, 375px and 1280px minimum default views, and every shipped locale.

## Font Failure Policy

Default to system stacks when a custom font is not essential. If a custom font is required:

1. obtain it from the official project or user;
2. record license and redistribution rights;
3. store a SHA-256 hash for bundled bytes;
4. self-host or bundle only when allowed;
5. provide a metrically reasonable offline fallback;
6. inspect layout before and after font load;
7. never silently download to the user profile during rendering.

If the font is unavailable, ship the verified fallback or stop with a precise missing dependency. Do not treat a readable fallback as evidence that the intended typography rendered.

## Validator

```bash
python3 scripts/validate_delivery.py delivery.json
python3 scripts/validate_delivery.py delivery.json --format json
python3 scripts/validate_delivery.py delivery.json --fail-on warning
```

The validator reads only the manifest and files inside its directory. It rejects absolute paths, traversal, symlinks, missing files, duplicate outputs, mismatched suffixes, missing rights records, unresolved HTML markers, and incomplete render evidence for `verified` bundles. It reports SHA-256 for recorded outputs and assets.

It deliberately does not:

- fetch URLs, install software, execute project code, or render HTML;
- parse PDF structure or certify PDF/UA;
- determine copyright ownership;
- validate factual truth, typography, contrast, reading order, or visual quality.

## Failure States

- **Draft:** useful source exists, but one or more promised checks remain.
- **Blocked:** required source, rights, renderer, target application, or user decision is unavailable and a fallback would materially change the deliverable.
- **Verified:** every promised output exists and the contract's content, render, format, and accessibility evidence has been inspected; no unresolved gap remains.

When blocked, preserve the editable source, evidence already gathered, exact failing command or tool, and the smallest next step. Do not erase a last known good artifact during a failed conversion.
