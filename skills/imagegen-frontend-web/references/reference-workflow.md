# Reference-Pack Workflow

## Select the Smallest Useful Set

Use unresolved decisions to choose frames:

| Unresolved decision | Useful evidence |
|---|---|
| Overall visual direction | One representative concept frame |
| Long-page rhythm and section order | One annotated full-page reference or structured blueprint |
| A section with unusual composition | One focused section frame |
| Mobile order, crop, or controls differ | A narrow-screen companion frame |
| Hover, open, error, empty, or loading behavior matters | One state frame per material behavior |
| Imagery will ship independently of layout | Separate production assets with crop/focal metadata |
| Stakeholders must choose a direction | Two or three distinct concepts using the same content constraints |

Do not generate a frame for a routine section that can be specified unambiguously with the shared grid, tokens, and content hierarchy.

## Blueprint

Accompany images with a compact implementation blueprint:

- page and section jobs;
- information hierarchy and real/placeholder content boundary;
- color roles, type roles, spacing, grid, shape, and image treatment;
- container behavior and responsive order;
- component states and interaction intent;
- each asset's role, crop mode, focal point, safe area, and alternative-text intent;
- unsupported or unresolved behavior;
- provenance and rights assumptions.

For responsive art direction, do not simply shrink the desktop composition. Decide whether the narrow viewport needs a different crop, subject position, text overlay, content order, or separate source image.

## Manifest Schema

The validator accepts UTF-8 JSON. Paths are relative to the manifest directory and may not escape it or traverse symlinks.

```json
{
  "version": 1,
  "deliverable": "responsive-set",
  "brief": {
    "page_kind": "product landing page",
    "audience": "operations teams evaluating the product",
    "goal": "explain the workflow and establish trust",
    "primary_action": "request a demo"
  },
  "design_system": {
    "colors": "ink, warm paper, one safety-orange action accent",
    "typography": "humanist sans for live UI; compact grotesk display role",
    "grid": "12 columns desktop; 4 columns mobile",
    "shape": "8px controls, square media, 1px neutral rules"
  },
  "viewports": [
    {"id": "desktop", "width": 1440, "height": 900},
    {"id": "mobile", "width": 390, "height": 844}
  ],
  "frames": [
    {
      "id": "home-desktop",
      "file": "frames/home-desktop.png",
      "viewport": "desktop",
      "scope": "page",
      "job": "show hierarchy, hero crop, proof order, and closing action",
      "purpose": "reference",
      "text_strategy": "live-overlay",
      "alt_mode": "descriptive",
      "alt_text": "Desktop homepage reference with an equipment photograph behind the hero and a single orange demo action.",
      "focal_point": [0.72, 0.36],
      "implementation_notes": [
        "Keep the headline and controls as live HTML.",
        "Use a separate narrow crop rather than centering this desktop source."
      ],
      "provenance": "generated from the approved brief; no third-party reference image"
    },
    {
      "id": "home-mobile",
      "file": "frames/home-mobile.webp",
      "viewport": "mobile",
      "scope": "page",
      "job": "resolve mobile content order and crop",
      "purpose": "reference",
      "text_strategy": "live-overlay",
      "alt_mode": "descriptive",
      "alt_text": "Narrow homepage reference with the equipment cropped above the live headline and demo action.",
      "focal_point": [0.53, 0.28],
      "implementation_notes": [
        "Move proof below the first product explanation on narrow screens."
      ],
      "provenance": "edited from the approved desktop direction"
    }
  ],
  "open_questions": [
    "Final customer proof and legal copy are still pending."
  ]
}
```

Accepted `deliverable` values are `single-concept`, `responsive-set`, `reference-pack`, and `production-assets`. Accepted frame `scope` values are `page`, `section`, `state`, and `asset`.

For a production asset, set `purpose` to `production-asset` and include a non-empty `rights` statement. For `essential-raster`, include `raster_text_reason`; the validator still emits a warning because an accessible equivalent must be verified in the implementation.

## Verification Levels

- **Concept reviewed:** the image itself was visually inspected.
- **Pack validated:** files, manifest, dimensions, paths, metadata, and hashes passed the validator.
- **Implemented:** the real page was rendered at declared viewports and compared with the blueprint.
- **Production verified:** accessibility and performance behavior were checked in the real stack, and production-media rights were resolved.

Do not collapse these levels into a single “done” claim.
