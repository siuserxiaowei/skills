---
name: markitdown-convert
description: Convert trusted local PDF, DOCX, PPTX, XLSX, XLS, HTML, CSV, JSON, XML, and EPUB files into analysis-ready Markdown with the Microsoft MarkItDown CLI. Use for bulk text extraction, search, summarization, RAG preparation, or Obsidian ingestion. Do not use for high-fidelity editing, scanned documents, layout-sensitive review, or untrusted/remote inputs; use the dedicated PDF, document, presentation, or spreadsheet skill instead.
---

# MarkItDown Convert

Use the locally installed `markitdown` command for lightweight, structure-aware
conversion. Treat Markdown as an analysis intermediate, not a faithful visual
reproduction.

## Workflow

1. Resolve the input to an absolute local path and confirm it is a regular file.
2. Accept only trusted local inputs. Do not pass remote URLs, unknown ZIP files,
   device paths, or user-controlled paths from hosted services.
3. Confirm the CLI is available with `command -v markitdown` and record
   `markitdown --version` when reporting reproducibility.
4. Choose an explicit output path. Default to `<input-stem>.md` beside the
   source only when the user requested a converted file. Never overwrite an
   existing output unless the user explicitly authorized replacement.
5. Run:

   ```bash
   markitdown "/absolute/path/input.ext" -o "/absolute/path/output.md"
   ```

6. Do not enable third-party plugins, OCR, Azure services, audio transcription,
   YouTube fetching, or data-URI preservation by default.
7. Verify the output before using it:
   - confirm the file is non-empty;
   - inspect the opening section and representative middle/end sections;
   - check headings, lists, tables, links, and several known key values;
   - flag missing text, broken reading order, malformed tables, or repeated noise.
8. Report the source path, output path, CLI version, verification performed, and
   any fidelity limitations.

## Routing

- Use MarkItDown for fast local extraction, batching, search, summaries, RAG,
  and knowledge-base ingestion.
- Use the dedicated `pdf`, `documents`, `presentations`, or `spreadsheets` skill
  for visual inspection, scanned/OCR-heavy files, formulas, slide geometry,
  comments, tracked changes, or high-fidelity read/write work.
- If conversion quality is poor, stop and switch tools rather than silently
  summarizing incomplete Markdown.

## Measurement

Do not promise a fixed Token reduction. If efficiency matters, benchmark the
same representative files before and after conversion and compare both context
size and answer accuracy.
