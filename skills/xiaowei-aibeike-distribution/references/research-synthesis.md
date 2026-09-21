# Research synthesis

This skill is an original implementation informed by public projects and documentation. It does not copy their files or call their private services.

## Patterns retained

1. **Draft-first and fresh verification.** `oil-oil/video-publisher-skill` separates preparation, upload, metadata repair, and independent verification. Its useful lesson is that a visible preview or a completed action is not enough; the resulting page state must be checked.
2. **Explicit workflow gates.** `officialwhitebird/video-automation-skill` keeps preview, overwrite, paid/API, download, and long-job gates visible and asks for subtitle review before irreversible rendering. This skill applies the same idea to media copying, account access, and final publication.
3. **Content-aware subtitle and platform adaptation.** `DianeHoo/subtitle-maker` uses semantic segmentation, internal review, and target-specific output. This skill carries that principle into captions, titles, tags, covers, and disclosures without forcing one caption onto every platform.
4. **Idempotent retries.** `Upload-Post/n8n-nodes-upload-post` documents stable keys to prevent duplicate posts after retry. This skill uses `campaign_id:platform` job IDs and requires inspection before retry.
5. **Per-platform isolation.** Queue-based multi-platform publishers such as `Pr4w/Laravel-Social-Poster` show why at-least-once delivery must be paired with duplicate protection and per-platform result tracking. This skill stores independent status and receipts.
6. **Human approval at consequential steps.** `tradewithmeai/socials-studio` makes the transition to public visibility explicit. This skill keeps final public publication behind a separate current user instruction.

## Sources consulted

- [oil-oil/video-publisher-skill](https://github.com/oil-oil/video-publisher-skill)
- [officialwhitebird/video-automation-skill](https://github.com/officialwhitebird/video-automation-skill)
- [DianeHoo/subtitle-maker](https://github.com/DianeHoo/subtitle-maker)
- [Upload-Post/n8n-nodes-upload-post](https://github.com/Upload-Post/n8n-nodes-upload-post)
- [Pr4w/Laravel-Social-Poster](https://github.com/Pr4w/Laravel-Social-Poster)
- [tradewithmeai/socials-studio](https://github.com/tradewithmeai/socials-studio)
- [爱贝壳 Chrome Web Store listing](https://chromewebstore.google.com/detail/%E7%88%B1%E8%B4%9D%E5%A3%B3%E5%86%85%E5%AE%B9%E5%90%8C%E6%AD%A5%E5%8A%A9%E6%89%8B/jejejajkcbhejfiocemmddgbkdlhhngm)

## Decisions made here

- Use a local package boundary instead of coupling to undocumented extension internals.
- Make source fingerprints, platform rows, and receipts first-class data.
- Prefer a stable handoff plus optional UI adapter over an all-or-nothing automation promise.
- Keep exact platform limits configurable because creator editors and extension support change.
- Treat public publication as a separate capability from preparation and draft creation.
