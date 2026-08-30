---
name: pua-ding
description: Run a concise delivery-reality review when the user explicitly asks for 钉味、钉内/钉外式提醒, or wants to separate stakeholder reporting from user-visible outcomes and evidence. Do not activate for ordinary coding or status requests.
license: MIT
---

# Delivery reality reminder

The name is retained for compatibility. This is an original evidence-review mode; it does not reproduce or quote third-party essays, slogans, or character voices.

## Inputs and Preconditions

Capture the promised outcome, the artifact that is said to exist, the audience for the report, the evidence currently available, and the next external action if any. Use this mode only after the user asks for the named style or explicitly wants a delivery-versus-reporting review. A meeting note, approval message, or green dashboard is an input to inspect, not proof by itself.

Read [references/examples.md](references/examples.md) only when explaining the four-layer distinction, resolving an authorization boundary, or testing this Skill against a realistic scenario.

## Review four layers

1. **Outcome:** what is supposed to become true for the user or system?
2. **Artifact:** what concrete file, deployment, message, decision, or dataset exists?
3. **Evidence:** what direct observation demonstrates the outcome?
4. **Report:** how is that evidence summarized for stakeholders?

Treat meetings, approvals, dashboards, activity counts, and positive feedback as signals. They prove delivery only when their definition and connection to the requested outcome are established.

## Respond in the requested density

For a quick reminder, use one compact blockquote containing the observed gap and next evidence-producing action.

For a disputed or complex delivery, report:

- outcome;
- artifact;
- evidence and its scope;
- status: `candidate`, `verified`, `partially-verified`, or `blocked`;
- uncovered risk;
- next decision or check.

Be wry if the user asked for “钉味,” but keep the humor original and directed at process absurdity, not a person's worth. Do not invent executive opinions, quote private feedback, change metric definitions to improve appearances, or encourage performative overtime.

## Risk Gate, Recovery, and Acceptance

Do not publish a status, message a stakeholder, alter a dashboard, or change a metric without authorization. If an evidence source is unavailable or contradictory, downgrade the status and name the missing check instead of smoothing the report. If the promised artifact exists but its user path fails, return to the artifact and original outcome rather than polishing the report.

Accept the review only when every material claim maps to a named artifact and observation, the evidence scope is explicit, uncovered risk is visible, and the next action has a real owner or decision boundary. The output itself is a review; it does not make the underlying delivery verified.

Example:

> 汇报已经绿了，用户路径还没投票。当前是 candidate：先重跑真实入口并保存输出，通过后再改成 verified。
