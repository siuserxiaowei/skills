# Google Search native discovery and canonical readback

Checked: 2026-08-26 (Asia/Shanghai)

Two queries were executed in the native Google Search web UI:

- `google-native-exact-pi-coding-agent`: `"Pi Coding Agent"`
- `google-native-earendil-works-pi-extensions`: `"earendil-works/pi" extensions`

Both SERPs rendered normally without login, CAPTCHA, or an unusual-traffic
interstitial. Google snippets were used only to discover URLs. Each retained
candidate was then opened and its canonical body, documentation, README,
product detail, or advisory index was independently read in the ordinary
in-app browser.

The ten retained URLs are globally distinct from current accepted items and
all existing worker candidate shards. Tenable and Kodem pages about the same
security issue were excluded as near-duplicate advisory content; the GitLab
package advisory index is retained once as a broader, auditable risk object.
An SEO-style directory review was read but replaced by Thomas Wiegold's
independent SDK deep dive because the latter provides concrete code, failure
modes, and a distinct implementation contribution rather than another generic
feature summary.
Existing Pi migration, YouTube, npm, Zenn, DEV.to, HN and repository objects
that appeared in Google were also excluded where their canonical URLs were
already occupied elsewhere.

No account actions, search-result interactions beyond read-only navigation,
downloads, installs, or product actions were performed.
