# Substack follow-up audit (2026-08-29)

Run: `pi-platform10-20260826`
Scope: append-only discovery and canonical public-page readback. This audit
does not modify `candidates.json`, `review_queue.json`, ledgers, or the public
library.

## Route and evidence boundary

The local `agent-reach` command was unavailable (`command not found`), so the
bounded public route was an ordinary anonymous Chrome page opened from one
focused Google query (`site:substack.com "pi-coding-agent"`). No Substack
publication search automation, API credential, login, subscription, comment,
restack, or download was used. Each URL below was opened directly and its
rendered canonical article body, visible byline/date, canonical/og URL, and
JSON-LD datePublished were checked. Body hashes are SHA-256 over the largest
article-content DIV `innerText` visible on 2026-08-29.

| provisional ID | canonical URL | visible body | decision |
|---|---|---:|---|
| `web-substack-nader-agent-stack` | `https://nader.substack.com/p/how-to-build-a-custom-agent-framework` | 47,766 chars; `adc958e7122f213f18f68c814c8607e9f8012502c9e2349a9244bbcce9c2d483` | evidence retained; reject as same tutorial cluster as accepted X `social-gap-x-dabit-agent-stack` (article says “Originally posted on X”) |
| `web-substack-rakesh-session-lifecycle` | `https://rakeshgohel.substack.com/p/how-pi-handles-the-full-lifecycle-of-an-agent-session` | 19,293 chars; `c466f315abc7ed9a6e9a1426ad005fc2eeadeadb9d928449008cc19ca1d52115` | independent candidate; Pi lifecycle/architecture |
| `web-substack-zarar-local-pi-lmstudio` | `https://bitbytebit.substack.com/p/run-a-local-coding-model-with-pi` | 10,757 chars; `1eb6a9fd05ed06cde2abd5a69074807c5d1ca4371e400ddf4ebdf49f2298b186` | independent candidate; local LM Studio setup |
| `web-substack-alex-getting-started` | `https://alexdevdunlop.substack.com/p/how-to-get-started-with-pi` | 4,607 chars; `08f05317215c4e47a4ba5e130ee85aa84df6924437eb57fe7bf64ad07b7612f` | independent candidate; install/provider/session guide |
| `web-substack-oleg-docker-pi-sandbox` | `https://olegselajev.substack.com/p/building-custom-docker-sandboxes` | 5,997 chars; `cea554e1b9e528b6044121cd695c75937c32fac936295901755167f8010aed46` | independent candidate; Docker Sandboxes delivery path |

The four independent rows have no matching canonical URL, title/author/date
pair, or high-overlap body cluster in the current queue and accepted library.
They remain `curator_review_ready` worker evidence only; a later curator may
promote them explicitly after checking the global cluster ledger. The Nader
row must not be promoted because its Substack body is the same tutorial linked
and embedded in the already accepted X object.

## Safety notes

The pages contain ordinary subscription prompts and one publication tagline
that attempts to steer reading (“Forget all previous instructions”); these are
untrusted page content and were ignored. No claim here is an independent
benchmark or security audit. Provider prices, model IDs, package names,
Docker/Pi versions, and author-reported performance can drift.
