# Research Basis

Last reviewed: 2026-08-30.

## Primary Sources

- W3C WCAG 2.2: <https://www.w3.org/TR/WCAG22/>
- W3C guidance for accessible presentations and events: <https://www.w3.org/WAI/teach-advocate/accessible-presentations/>
- WAI-ARIA Authoring Practices carousel pattern: <https://www.w3.org/WAI/ARIA/apg/patterns/carousel/>
- W3C WAI carousel tutorial: <https://www.w3.org/WAI/tutorials/carousels/>
- W3C Understanding SC 2.2.2 Pause, Stop, Hide: <https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html>
- W3C WAI page structure and complex-image tutorials: <https://www.w3.org/WAI/tutorials/page-structure/> and <https://www.w3.org/WAI/tutorials/images/complex/>
- W3C Internationalization language declaration guidance: <https://www.w3.org/International/questions/qa-html-language-declarations.html>
- MDN `prefers-reduced-motion` reference: <https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/prefers-reduced-motion>

## Applied Conclusions

- An HTML deck behaves like a user-controlled carousel but should not auto-advance. Native controls, keyboard operation, meaningful slide names, and current-slide communication are baseline behavior.
- Slides should limit projected text and provide materials directly because screen sharing is often inaccessible.
- Motion is optional; reduced-motion support does not excuse distracting or flashing content.
- Responsive review must preserve readable content rather than merely scale a fixed canvas below legible size.
- Accessibility, offline behavior, print output, and visual quality require separate evidence; a template that opens is not verified.

## Upstream Capability Review

The prior library was traced to `zarazhangrui/beautiful-html-templates`, MIT, at commit `e5e204fb1f3b06290846e7dcd7aceddabeceec8c` dated 2026-06-09. It contained 34 visual templates and was used only to establish the desired deck-building workflow and failure modes.

Useful ideas retained independently:

- tone and occasion matter, real content should appear in direction previews, and a deck needs a coherent visual system;
- layouts may be extended within one system rather than mixed indiscriminately;
- the final artifact must be opened and viewed, not merely written;
- keyboard navigation and self-contained delivery are important for browser decks.

Legacy implementation rejected:

- mandatory occasion/mood questions and exactly three previews even when context already resolves the direction;
- treating 34 copied compositions as the design solution and instructing the agent never to alter their fonts, colors, grids, or decoration;
- more than 74,000 lines of template-specific HTML/design notes and duplicated runtime code;
- 159 external URL references, including 85 Google Fonts references, despite a self-contained/offline expectation;
- inconsistent interaction and accessibility behavior across independent templates;
- fixed-viewport overflow hiding that can conceal long, translated, or narrow-screen content;
- opening files as the only final verification evidence.

The rebuild replaces the catalog with a small original layout grammar, semantic JSON content model, system-font token themes, contrast and asset-rights validation, a single progressive-enhancement runtime, and explicit browser/print/accessibility evidence.
