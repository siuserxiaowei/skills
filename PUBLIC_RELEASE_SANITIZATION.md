# Public release sanitization

This public snapshot preserves the research summaries, candidate IDs, evidence ledgers, and reproducible status records. It intentionally omits or redacts:

- login-bound URL parameters and browser login checkpoints;
- private Feishu wiki/document locators;
- author email addresses, third-party API profile payloads, and local absolute paths;
- full Stack Exchange API response bodies (status, byte count, result count, and SHA-256 remain);
- generated Python caches and other machine-local artifacts.

These changes do not alter the accepted-item counts or platform coverage conclusions. The private Feishu destination is not published by this repository.
