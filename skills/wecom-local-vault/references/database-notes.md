# Storage and compatibility notes

## Account recognition

A candidate account directory is accepted only when `message.db`, `session.db`, and `user.db` coexist. Discovery currently searches the WeCom sandbox, private-library, and team-container locations used by recent macOS clients. A short SHA-256 label identifies a path without printing it by default.

## Page codec

The supported encrypted form uses 4096-byte pages and a 16-byte raw secret. Each page has an AES key derived from the secret, little-endian page number, and the four-byte format tag; its IV comes from the compatible page-number PRNG sequence. Page one exposes enough database-header bytes to recognize the format and reject a wrong secret. Plain SQLite input is also accepted so fixture and migrated stores can be snapshotted.

This is not the SQLCipher layout used by personal WeChat. Do not exchange keys or decryption tools between the products.

## WAL boundary

The decoder checks WAL magic, page size, and header salt. It ignores stale-salt frames and frames after the final observed commit. Accepted pages replace the corresponding base pages in memory, and the final commit size controls truncation. No WAL checksum is rewritten because output is one merged SQLite database, not a reconstructed WAL pair.

Reading a live file can race with the client. The implementation compares size and modification time around each read and retries a bounded number of times; repeated movement fails instead of emitting an unmarked partial result.

## Query schema

The query layer probes tables and columns before selecting them. It recognizes contact data in `user_table` and `external_user_relation_v3`, conversations in `conversation_table`, member aliases in `conversation_user_table`, and message rows in `message_table`, `message_small_table`, or `kf_message_tableV1`. A client release may rename any of these. Missing structures produce empty or partial results rather than invented mappings.

## Protection evidence

- key records, database copies, manifests, diagnostics, and exports use owner-only file mode;
- key records are rejected when group or other permission bits are present;
- writes use exclusive creation and do not replace a prior artifact;
- source databases are opened only for byte reads, while snapshot SQL connections use read-only URI mode plus `PRAGMA query_only`.
