# Research Basis

Last reviewed: 2026-08-30.

## Primary Sources

- OpenAI image generation guide: <https://developers.openai.com/api/docs/guides/image-generation>
- OpenAI GPT Image prompting guide: <https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide>
- W3C Web Content Accessibility Guidelines (WCAG) 2.2: <https://www.w3.org/TR/WCAG22/>
- web.dev, responsive image delivery: <https://web.dev/articles/serve-responsive-images>
- web.dev, preventing image-driven cumulative layout shift: <https://web.dev/articles/optimize-cls>

## Current Findings

1. Current image tooling supports both generation and editing, including multi-turn refinement and input images. The prompt guide recommends explicit composition, change/preserve constraints, indexed multi-image roles, and small iterative changes.
2. Exact in-image text benefits from literal copy and typography constraints, but output still requires visual inspection. A web concept's raster text is not a substitute for semantic, resizable implementation text.
3. WCAG 2.2 requires 4.5:1 contrast for ordinary text and images of text, 3:1 for large text, and live text instead of images of text when the same presentation can be achieved with the implementation technology. It also requires ordinary content to reflow at a width equivalent to 320 CSS pixels without two-dimensional scrolling.
4. Responsive media is a delivery and art-direction problem, not merely a smaller canvas. `srcset`/`sizes` can reduce bytes and improve image LCP; `<picture>` or equivalent art direction can supply a materially different crop for narrow screens.
5. Intrinsic width/height or reserved aspect-ratio space prevents image loading from shifting surrounding content. An attractive generated hero that omits delivery metadata can create real CLS and LCP debt.

## Retained Capabilities

- image-led art direction for heroes, sections, complete page concepts, and coordinated sets;
- attention to hierarchy, typography, whitespace, brand consistency, crop, material, and visual rhythm;
- anti-template review that rejects decorative UI, invented data, and repeated generic compositions;
- implementation handoff rather than treating an image as the final website.

## Rejected Legacy Behaviors

- requiring one horizontal image for every section;
- defaulting ambiguous sites to six or eight generation calls;
- announcing an arbitrary image count before identifying unresolved design decisions;
- treating all websites as conversion funnels or all hero sections as image-led;
- fixed 1–10 style dials and large prescriptive pattern catalogs that override the actual brand and content;
- using pixels as proof of semantic controls, responsive behavior, accessible text, or production performance;
- calling a concept image implementation-ready without dimensions, crop rules, text strategy, provenance, and browser verification.

## Independent Design Decisions

The rebuilt Skill selects the minimum evidence set by decision coverage, separates concepts from production assets, records responsive and accessibility intent, validates a portable manifest without external dependencies, and makes real browser behavior the final source of truth when implementation is in scope.
