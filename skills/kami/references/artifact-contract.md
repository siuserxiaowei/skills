# Artifact Contract

Use a contract when the task produces multiple files, depends on external facts or licensed assets, promises a rendered format, or carries meaningful accessibility or publication risk. Keep it beside the deliverables as `delivery.json`.

## Minimal Shape

```json
{
  "version": 1,
  "status": "verified",
  "artifact": {
    "kind": "report",
    "title": "Quarterly operating review",
    "language": "en-US",
    "audience": "Operating leadership",
    "purpose": "Decide the next-quarter priorities"
  },
  "outputs": [
    {"path": "review.html", "format": "html", "editable": true},
    {"path": "review.pdf", "format": "pdf", "editable": false}
  ],
  "sources": [
    {"kind": "user-file", "locator": "notes.md", "as_of": "2026-08-30"}
  ],
  "assets": [
    {"path": "assets/logo.svg", "role": "logo", "rights": "user-provided", "alt": "Acme"}
  ],
  "verification": {
    "gaps": [],
    "content_reviewed": true,
    "renders": [
      {
        "output": "review.pdf",
        "tool": "browser print",
        "pages": 3,
        "reviewed_pages": [1, 2, 3],
        "evidence": ["review-evidence/page-1.png", "review-evidence/page-2.png", "review-evidence/page-3.png"]
      }
    ],
    "accessibility": {
      "html_keyboard": "not-applicable",
      "html_structure": "tested",
      "pdf": "unknown",
      "notes": "No PDF/UA claim; reading order needs a dedicated tagged-PDF check."
    }
  }
}
```

## Required Meanings

- `status`: `draft`, `verified`, or `blocked`. Only `verified` activates the strict evidence gates.
- `artifact.kind`: `one-pager`, `report`, `letter`, `resume`, `portfolio`, `slide-deck`, `landing-page`, or `other`.
- `artifact.language`: a BCP 47-style tag such as `zh-CN`, `en-US`, `ja`, or `ar`.
- `outputs`: local files in the bundle. `format` must agree with the suffix. Mark editability based on the real target application.
- `sources`: facts or material inputs. `kind` is `user-file`, `user-statement`, `primary-url`, or `derived`; `locator` identifies the input and `as_of` records temporal scope when relevant.
- `assets`: every logo, image, font, audio, video, or externally sourced illustration shipped with or referenced by the artifact. `rights` is `user-provided`, `original`, `open-license`, `licensed`, or `public-domain`.
- `verification.gaps`: unresolved content, source, asset, format, or visual issues. A verified bundle has none.
- `verification.renders`: one record per rendered output. Evidence must exist locally and cover every declared page or required viewport.
- `verification.accessibility`: precise test status, not a marketing claim. Allowed values are `tested`, `failed`, `unknown`, and `not-applicable`.

## Screen Render Record

For a landing page or other browser surface, replace `pages` with `viewports`:

```json
{
  "output": "index.html",
  "tool": "Chromium 140",
  "viewports": [
    {"width": 375, "height": 812, "screenshot": "evidence/375.png"},
    {"width": 1280, "height": 900, "screenshot": "evidence/1280.png"}
  ]
}
```

Add other widths, locales, states, print sizes, or slide variants that the contract promises. Two screenshots do not prove every responsive state; they are the minimum evidence for the default surface.

## Font Record

Bundled or remotely served fonts need an asset record plus:

```json
{
  "path": "assets/fonts/Example.woff2",
  "role": "font",
  "rights": "open-license",
  "license": "OFL-1.1",
  "source": "https://example.org/font-project",
  "offline_fallback": "ui-serif, Georgia, serif",
  "alt": "not-applicable"
}
```

Do not copy a font into the bundle when the license is unknown or forbids redistribution. A system font stack needs no asset record.

## Boundaries

The manifest records evidence; it does not replace the source document, citations, browser inspection, presentation opening, PDF tag inspection, or human editorial review. Do not loosen it to make a failing artifact appear complete.
