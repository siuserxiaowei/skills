# Research Basis

Last reviewed: 2026-08-30.

## Primary Sources

- OpenAI release notes describe Goal mode as a way to define an outcome and success criteria and let Codex keep working toward it: <https://help.openai.com/en/articles/6825453>
- OpenAI's *Codex-maxxing for long-running work* says a stronger goal supplies expected behavior, review criteria, constraints, or a clear definition of done that Codex can test against: <https://cdn.openai.com/pdf/8a9f00cf-d379-4e20-b06f-dd7ba5196a11/OAI_WhitePaper_Codex-maxxing26.pdf>
- The current local Codex goal interface accepts a concrete objective and an optional positive token budget. Its interface requires the budget to be omitted unless the user explicitly requested one, and reserves terminal status changes for actually complete or genuinely blocked goals.

## Design Conclusions

1. Outcome and verifiable success criteria are the stable public concepts. A fixed collection of labels is a writing aid, not verified product syntax.
2. The goal must preserve the requested end state across turns. A plan, progress update, token count, or partial test suite is not completion evidence.
3. Persistence should be bounded by authority and external reality. Long-running work does not grant permission for unrelated publication, deletion, payment, credential use, or production mutation.
4. A token budget changes stopping behavior and therefore must be explicit rather than inferred.
5. Product behavior can change. Recheck official OpenAI documentation and the current local goal interface before updating product-specific claims.

## Rejected Legacy Assumptions

- Mandatory bilingual output for Chinese users.
- A universal seven-field `/goal` schema.
- A default of three improvement rounds for every task.
- Treating all vague requests as local MVPs.
- Requiring multiple-choice interviews when a safe default is evident.

Those conventions can occasionally be useful, but making them universal narrows user intent and falsely presents a writing template as platform behavior.
