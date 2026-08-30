# Decision model

## Severity

Rate the credible worst-case effect of the observed behavior:

- **Critical:** plausible credential theft, secret or private-data exfiltration, arbitrary code execution across the trust boundary, destructive broad-system action, or unauthorized high-impact external action.
- **High:** privileged or persistent modification, access to sensitive stores, unreviewed executable download, high-impact action without an adequate approval gate, or a dangerous path requiring limited additional conditions.
- **Medium:** excessive but bounded permissions, mutable or weakly verified dependencies, unsafe defaults, ambiguous data flow, missing license or provenance, or incomplete controls with meaningful impact.
- **Low:** hardening or clarity gap with limited direct impact.
- **Info:** inventory or context that helps reproduce the review.

Severity is not a count of suspicious strings. Explain the source, sink, attacker influence, required conditions, and affected boundary.

## Confidence

- **High:** directly observed in the resolved artifact or an isolated behavior trace.
- **Medium:** strongly implied but one relevant path or runtime condition remains unverified.
- **Low:** heuristic or metadata-only signal requiring confirmation.

## Verdict

- **approve:** complete relevant coverage, no unresolved material finding, and requested permissions are proportionate.
- **approve-with-controls:** useful behavior is acceptable only with stated sandbox, permission, domain, credential, or approval restrictions.
- **quarantine:** potentially acceptable, but missing provenance, unreviewed files, opaque binaries, unreachable dependencies, or uncertain behavior prevents installation or execution.
- **reject:** malicious behavior, an unacceptable capability, a license or integrity failure that blocks the intended use, or a material finding without a viable control.

Popularity and authorship claims may adjust confidence in provenance; they never override observed behavior.

## Stop conditions

Stop and quarantine rather than improvise when:

- the resolved artifact changes during review;
- an archive, binary, submodule, generated file, or remote include cannot be inspected;
- testing requires personal credentials or live external side effects not authorized by the user;
- the package attempts to disable controls, conceal behavior, or expand scope while being reviewed.
