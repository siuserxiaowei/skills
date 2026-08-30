# Research Basis

Last reviewed: 2026-08-30.

## Primary Sources

- W3C Web Content Accessibility Guidelines (WCAG) 2.2: <https://www.w3.org/TR/WCAG22/>
- W3C WAI-ARIA Authoring Practices Guide: <https://www.w3.org/WAI/ARIA/apg/>
- W3C Internationalization Quick Tips: <https://www.w3.org/International/quicktips/>
- Design Tokens Community Group technical reports; 2025.10 is the current stable report: <https://www.designtokens.org/technical-reports/>
- web.dev Web Vitals: <https://web.dev/articles/vitals>
- web.dev responsive images: <https://web.dev/articles/serve-responsive-images>
- web.dev cumulative layout shift guidance: <https://web.dev/articles/optimize-cls>

## Current Standards Baseline

- WCAG 2.2 remains the normative accessibility baseline used here. Automated checks can find only a subset of failures; conformance is a property of the delivered experience, not a scanner score.
- WAI-ARIA APG supplies informative patterns for semantics, state, accessible names, keyboard behavior, and focus management. Native HTML remains preferable when it provides the required behavior.
- The Design Tokens Community Group lists 2025.10 as stable. It is an interchange reference, not a reason to replace a working project-specific token system.
- Current Core Web Vitals are LCP, INP, and CLS. The “good” thresholds are LCP at or below 2.5 seconds, INP at or below 200 ms, and CLS at or below 0.1 at the 75th percentile, segmented by mobile and desktop. Lab tools do not replace field evidence; Lighthouse cannot directly measure INP without real interaction.
- International interfaces need declared UTF-8/language, local formats, translatable content, and correct base direction. Responsive review must include content growth and direction, not only viewport width.

## Upstream Capability Review

The prior implementation was traced to `pbakaus/impeccable`, local Skill version 4.0.4, Apache-2.0, with an upstream snapshot at commit `620ba1fe7d87a39039a8528bfaa319ecfa893cb2` (2026-08-04). It was used only to establish the feature baseline and failure modes.

Useful capabilities retained independently:

- critique, technical audit, shaping, building, refinement, design-system extraction, responsive adaptation, states, internationalization, accessibility, performance, motion, typography, layout, color, and browser verification;
- project evidence and design context before visual changes;
- bounded verification rather than endless subjective polishing;
- static anti-pattern detection as one input to human/agent review.

Legacy behavior rejected:

- 23 command aliases and a large routing vocabulary that increase trigger ambiguity without changing the underlying work;
- universal aesthetic prohibitions presented as design truth;
- hidden or persistent project hooks, user-home caches, background servers, and generated shortcut Skills;
- live-edit infrastructure that rewrites source through a browser session;
- forwarding the full environment to child processes and suggesting credential exports;
- launching Codex with `--dangerously-bypass-approvals-and-sandbox` or Claude with `bypassPermissions`;
- bundled minified browser code and more than three megabytes of copied implementation whose maintenance and supply-chain surface exceed this repository's need;
- treating deterministic detector counts as proof of design quality.

## Independent Design Conclusions

The rebuilt Skill routes by user-authorized action, separates critique from mutation, uses project truth rather than style bans, supplies a transparent read-only scanner, and requires rendered/interaction/accessibility/performance evidence appropriate to each claim. It does not install hooks, run services, invoke external Agents, or handle credentials.
