# Recovery loop

Use this reference after a repeated failure or when the current approach no longer produces information.

## Establish the failure signature

Record:

- the exact command, request, or reasoning step;
- the relevant input and environment;
- the observable output, including exit status;
- what changed since the previous attempt;
- whether the result is actually the same failure.

Do not increase a retry count for an observation timeout, pending process, user interruption, or a different failure. Re-poll confirmed live work rather than restarting it.

## Choose the next experiment

Prefer an action that separates competing explanations. Examples:

- inspect the resolved path before changing path logic;
- reproduce with the smallest input before replacing a dependency;
- compare current official documentation with the installed version before declaring an API unsupported;
- trace source-to-sink data flow before adding validation at a convenient but ineffective layer;
- run the original failure path before and after a fix, not only a broad test suite.

A new command is not a new approach when it exercises the same assumption. State which hypothesis the action tests and what different outcomes would mean.

## Escalate by information, not pressure

- **First material failure:** read the complete output and nearby authoritative context.
- **Repeated signature:** stop parameter tweaking; list distinct hypotheses and run a discriminating check.
- **No information gain:** revisit the completion criterion, boundary conditions, and whether the problem is being framed at the wrong layer.
- **External boundary:** ask only for the missing decision, authority, credential, or state change after exhausting safe discovery.

## Stop conditions

End the loop when one of these is true:

- the completion evidence passes;
- the user pauses or cancels;
- the agreed iteration, time, cost, or risk budget is exhausted;
- further action requires new authority or a material user choice;
- the same blocking condition remains after all safe discriminating checks;
- evidence shows the requested outcome is impossible under the stated constraints.

When stopping without success, provide verified facts, attempts and results, eliminated hypotheses, remaining uncertainty, current artifact state, and the smallest useful next step. This is an evidence handoff, not a failure of attitude.
