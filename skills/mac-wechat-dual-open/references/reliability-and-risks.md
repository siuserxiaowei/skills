# Reliability and risk model

## What the workaround changes

The workflow copies an existing application bundle, edits the copy's top-level identifier and icon metadata, gives the copy an ad-hoc signature, and launches the copied executable. It does not make the duplicate an official second-install feature.

## Expected failure boundaries

| Boundary | Observable symptom | Response |
|---|---|---|
| Application update | source and duplicate versions differ | create and verify a fresh duplicate; retain the old one until migration is confirmed |
| Signature policy | macOS rejects the copied bundle | inspect signature and Gatekeeper output; do not disable platform protections globally |
| Single-instance logic | duplicate exits or focuses the original | record the exact versions; the workaround may be incompatible |
| Notification identity | one instance misses pushes | treat notifications as unreliable and verify messages in-app |
| Icon cache | old icon remains visible | quit the duplicate, refresh registration, and compare the generated preview |
| Account/container behavior | sessions are not isolated as expected | stop before entering sensitive credentials and inspect actual container paths |

## Security posture

Ad-hoc signing replaces the vendor signature on the duplicate, so vendor signature assurances no longer apply to that copy. This is acceptable only when the copy was produced locally from the user's verified installation and no unreviewed code or resources were inserted.

Avoid tutorials that require disabling system protections, downloading a patched executable, injecting a dynamic library, or running an opaque installer. Those techniques cross a different trust boundary from a local copy-and-identify workflow.

## Reversibility

The duplicate should live outside `/Applications/WeChat.app`. Reversal consists of quitting it, moving the exact duplicate bundle to Trash after user approval, and removing preferences for its custom identifier if requested. Never delete the source app or the user's chat data as part of cleanup.

## Evidence for a support answer

When explaining whether the method works, report the tested macOS and WeChat versions, source/target identifiers, signature verification result, whether two windows were observed, and any notification or update limitation. Do not give a timeless reliability score; compatibility changes over time.
