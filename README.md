# 📄 Paper Summary — OpenClaw Skill

An [OpenClaw](https://github.com/openclaw/openclaw) skill that extracts and summarizes academic papers into structured research reports.

## Features

- **Multiple input sources**: Local PDF, arXiv ID/URL, DOI, remote PDF URL
- **High-quality extraction**: Uses [pymupdf4llm](https://github.com/pymupdf/pymupdf4llm) for accurate PDF→Markdown conversion
- **Structured output**: 7-section template (TL;DR, Background, Method, Results, Limitations, Commentary)
- **Batch processing**: Process an entire directory of PDFs at once
- **Bilingual**: Supports Chinese/English bilingual section headers

## Quick Start

### Prerequisites

```bash
pip3 install pymupdf4llm
```

### Usage (via OpenClaw)

Just tell your agent:

- "帮我总结这篇论文 2401.02954"
- "Summarize this paper /path/to/paper.pdf"
- "分析 https://arxiv.org/abs/2301.07041"
- "批量总结这个目录下的论文 /path/to/papers/"

### Standalone Usage

```bash
# Extract from arXiv
python3 scripts/extract_paper.py 2401.02954 --metadata

# Extract from local PDF
python3 scripts/extract_paper.py /path/to/paper.pdf --output extracted.md

# Batch extract
python3 scripts/batch_extract.py /path/to/pdf_dir --output-dir ./output
```

## Skill Structure

```
paper-summary/
├── SKILL.md                    # Skill entry point + trigger config
├── README.md                   # This file
├── scripts/
│   ├── extract_paper.py        # Single paper extraction (PDF/arXiv/DOI/URL)
│   └── batch_extract.py        # Batch directory processing
├── references/
│   └── summary-template.md     # Structured summary template
└── assets/                     # (optional) Place PDFs here for processing
```

## License

MIT
