---
name: paper-summary
description: >
  Academic paper summarization and analysis agent. Extracts text from PDF papers
  (local files, arXiv IDs/URLs, DOIs, or remote PDF URLs) using pymupdf4llm,
  then produces structured research summaries. Supports single and batch processing.
  Use when user asks to: summarize a paper, analyze a research paper, read a PDF paper,
  extract key findings from a paper, review literature, do a literature survey,
  总结论文, 分析文献, 论文解读, 文献综述.
---

# Paper Summary

Summarize academic papers into structured research reports.

## Prerequisites

- Python 3.8+ with `pymupdf4llm` installed
- Install: `pip3 install pymupdf4llm`

## Workflow

### Single Paper

1. **Extract text** — run the extraction script:

```bash
python3 {skill_dir}/scripts/extract_paper.py "<input>" --metadata
```

`<input>` accepts: local PDF path, arXiv ID (`2301.07041`), arXiv URL, DOI (`10.xxxx/...`), or any PDF URL.

2. **Read the extracted markdown** (pipe output or use `--output <path>` to write to file first for large papers).

3. **Generate summary** — follow the template in `references/summary-template.md`. Read it before writing.

4. **Save report** — write the summary to `{workspace}/paper-summaries/{sanitized-title}.md`. Create the directory if needed.

### Batch Processing

For a directory of PDFs:

```bash
python3 {skill_dir}/scripts/batch_extract.py <pdf_directory> --output-dir <output_dir>
```

Then read each extracted `.md` from `<output_dir>`, summarize individually, and produce a combined report.

### For URLs (non-PDF)

If the user provides a URL to an HTML paper page (not a direct PDF link), try:
1. Check if it's an arXiv URL → the script handles this automatically
2. Otherwise use `summarize "<url>" --length long` as fallback for HTML content

## Output Guidelines

- Use the paper's language for the summary body; use bilingual section headers
- Include quantitative results — actual numbers, not vague claims
- For survey/review papers, emphasize the taxonomy and key reference landscape
- Keep TL;DR to 1-2 sentences maximum
- Rate the paper briefly at the end (novelty, rigor, clarity, impact)

## Paths

- Extraction script: `scripts/extract_paper.py`
- Batch script: `scripts/batch_extract.py`
- Summary template: `references/summary-template.md`
- Default output: `{workspace}/paper-summaries/`
