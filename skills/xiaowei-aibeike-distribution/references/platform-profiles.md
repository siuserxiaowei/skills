# Platform profile guidance

These are planning defaults for the package generator. They are deliberately not hard-coded claims about a platform's current limits. Before a draft is saved, inspect the current editor or the platform's official documentation and record any deviation in `review_notes`.

## Douyin / 抖音

- Use a concise first-line hook and keep hashtags separate from the main sentence when the editor exposes tag chips.
- Check the selected cover in the actual preview; confirm the account's original-content and AI-content declarations.
- Verify duration, visibility, location, comment permissions, and scheduled time in the current editor.

## Xiaohongshu / 小红书

- Treat the title, body, and tags as separate fields. Keep the body readable if the editor removes line breaks.
- Prefer a vertical cover with a readable title area and no critical text near crop edges.
- Verify whether the current flow creates a draft, schedules it, or opens a public publish confirmation.

## Bilibili / 哔哩哔哩

- Keep a clear title, description, tags, and category. Preserve technical terms and product names from the approved content anchor.
- Confirm cover ratio, collection/series selection, original declaration, and visibility in the current uploader.
- Do not infer a successful upload from a completed progress bar; verify the resulting draft or video page.

## WeChat Channels / 视频号

- Keep the caption short enough for the current composer and place hashtags only where the current editor supports them.
- Verify account, visibility, location, cover, and scheduled time separately; these settings often live in different panels.
- Treat any “submitted for review” state as a platform receipt, not as public availability.

## YouTube / TikTok and other API-capable targets

- Prefer official APIs when they are authorized and documented for the account. Store the API version and endpoint source in campaign notes, never in credentials.
- Respect each API's draft/private/public semantics and rate limits. A successful upload response is not proof that metadata, visibility, or processing completed.

## Profile update rule

When an editor changes, update this reference only after checking a current official page or a real logged-in task. Keep the profile as a cautious default and let fresh UI evidence win.
