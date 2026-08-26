# Engine replay notes

- The canonical router probed Python, Go, and Rust from their real executables.
- Python was selected for the `rank` stage. Go and Rust were ready but ineligible for ranking, so they were not falsely reported as rank executors.
- First replay stopped with `output directory must not already exist`; this was the ranker's fail-closed overwrite guard, not a ranking mismatch.
- The existing `ranking-output` directory was moved to a system temporary directory, the unchanged plan generated a fresh output directory, and `diff -qr` returned no differences.
- `engine_execution.json` is the successful canonical replay result. The earlier nonzero attempt remains in the task execution log; this note preserves its cause in the repository.
