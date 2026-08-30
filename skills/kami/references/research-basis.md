# Research Basis

Last reviewed: 2026-08-30.

## Primary Sources

- W3C Web Content Accessibility Guidelines (WCAG) 2.2: <https://www.w3.org/TR/WCAG22/>
- W3C techniques for WCAG 2.2, including PDF techniques; these techniques are informative rather than required: <https://www.w3.org/WAI/WCAG22/Techniques/>
- W3C WAI Page Structure tutorial: <https://www.w3.org/WAI/tutorials/page-structure/>
- W3C WAI Complex Images tutorial: <https://www.w3.org/WAI/tutorials/images/complex/>
- W3C Internationalization guidance for HTML language declarations and UTF-8: <https://www.w3.org/International/questions/qa-html-language-declarations.html> and <https://www.w3.org/International/questions/qa-html-encoding-declarations.en>
- W3C CSS Paged Media Level 3 and CSS Fragmentation Level 3: <https://www.w3.org/TR/css-page-3/> and <https://www.w3.org/TR/css-break-3/>
- ISO 14289-2:2024, PDF/UA-2 for PDF 2.0: <https://www.iso.org/standard/82278.html>
- web.dev font-loading guidance: <https://web.dev/articles/font-best-practices>
- SIL Open Font License FAQ and usage guidance: <https://openfontlicense.org/ofl-faq/> and <https://openfontlicense.org/how-to-use-the-ofl/>

## Applied Conclusions

- Appearance, semantic HTML, and tagged-PDF quality are separate evidence surfaces.
- W3C PDF techniques can support WCAG evaluation but are not themselves the conformance requirements.
- PDF/UA-2 is an explicit standard, not a synonym for a readable or tagged PDF.
- CSS paged-media and fragmentation features need engine-specific verification; CSS Paged Media Level 3 remains a Working Draft, while CSS Fragmentation Level 3 is a Candidate Recommendation.
- Complex charts and diagrams need both short identification and an equivalent detailed explanation.
- Custom fonts affect performance, layout stability, portability, privacy, and licensing. System stacks are a valid default; redistribution needs the actual license and source record.

## Upstream Capability Review

The prior implementation was traced to `tw93/Kami`, target version 1.12.0, MIT, and an upstream snapshot at commit `fbdb54f59b7f224db55322357e5739b9ef9687f4` dated 2026-08-02. It was used only to establish feature coverage and failure modes.

Useful ideas retained independently:

- routing among one-pagers, reports, letters, resumes, portfolios, slide decks, and static landing pages;
- source and material passes before layout;
- content fidelity, missing-data disclosure, page/render checks, responsive screenshots, font verification, and separate editable/rendered outputs;
- concise editorial structure, charts chosen for the question, and visual feedback tied to rendered evidence.

Legacy implementation rejected:

- a fixed parchment/ink-blue/serif aesthetic presented as the default answer to unrelated brands and audiences;
- automatic reads from user-home brand profiles and implicit habit notes;
- 49 copied templates/diagrams and more than 33,000 lines of tightly coupled maintenance surface;
- a font downloader that writes to a user font directory, uses mutable branch CDN URLs, and checks only byte size rather than a pinned digest;
- runtime dependency-install suggestions using `--break-system-packages`;
- an MCP server and renderer whose trusted-HTML boundary still allows referenced local, HTTP, and HTTPS resources with the process's permissions;
- treating template lint, font presence, page density, or exported screenshots as sufficient accessibility or publication proof.

The rebuild uses a neutral structural starter, a source-first editorial protocol, a read-only delivery validator, explicit rights and evidence records, and no network, global state, background service, runtime install, or bundled third-party asset.
