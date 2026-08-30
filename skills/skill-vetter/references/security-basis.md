# Security basis

Use these principles to interpret evidence; do not turn them into a mechanical checklist.

## Untrusted instructions and excessive agency

External files, web pages, images, tool results, and package documentation can contain direct or indirect prompt injection. Separate external content from trusted instructions, constrain privileges, validate consequential arguments in deterministic code, and require human approval for high-impact actions.

Primary references:

- [OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- [OWASP Top 10 for Agentic Applications](https://genai.owasp.org/)

## Software and AI supply chain

Provenance and dependency review answer different questions. Provenance helps bind an artifact to a source and process; dependency review reveals components, versions, licenses, and known vulnerabilities. Neither proves benign behavior. Inspect direct and transitive dependencies, installation hooks, mutable references, downloaded executables, model or data assets, and generated artifacts.

Prefer immutable revisions and verified hashes where the ecosystem supports them. A lockfile improves reproducibility but does not make a compromised version trustworthy. Pair pinning with monitored updates.

Primary references:

- [NIST Secure Software Development Framework 1.1](https://csrc.nist.gov/projects/ssdf)
- [NIST Software Security in Supply Chains](https://www.nist.gov/itl/executive-order-14028-improving-nations-cybersecurity/software-security-supply-chains-software)
- [GitHub supply-chain security](https://docs.github.com/en/code-security/concepts/supply-chain-security/supply-chain-security)
- [OpenSSF Scorecard checks](https://github.com/ossf/scorecard#scorecard-checks)

## Repository and automation security

Review workflows and release automation as executable code. Look for untrusted values interpolated into shells, broad workflow-token permissions, mutable action references, artifact substitution, unsigned or unverifiable releases, and jobs where a pull request can reach secrets or write-capable tokens.

Primary references:

- [GitHub secure use reference](https://docs.github.com/en/actions/reference/security/secure-use)
- [OpenSSF Scorecard: Pinned-Dependencies and Dangerous-Workflow](https://github.com/ossf/scorecard/blob/main/docs/checks/internal/checks.yaml)

## Evidence standard

Static pattern matches are leads, not verdicts. Validate whether the matched code is reachable, what controls the input, which identity executes it, and what data or systems it can affect. Absence of a match is not absence of risk. Record coverage and uncertainty so a later reviewer can reproduce the decision.
