# Paper Summary - OpenClaw Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)

An OpenClaw skill for academic paper summarization and analysis. Extracts text from PDF papers and produces structured research summaries.

## Features

- **Multiple Input Sources**: Local PDF, arXiv ID/URL, DOI, Semantic Scholar, PubMed ID, remote PDF URL
- **High-Quality Extraction**: Uses pymupdf4llm for accurate PDF→Markdown conversion
- **Structured Output**: 7-section template (TL;DR, Background, Method, Results, Limitations, Commentary)
- **Batch Processing**: Process entire directories of PDFs in parallel
- **Advanced Analysis**: Citation network, paper comparison, figure extraction, recommendations
- **Bilingual**: Supports Chinese/English bilingual section headers
- **Cache Support**: Download caching to avoid re-fetching
- **Progress Tracking**: Real-time progress bars for batch operations

## Quick Start

### Prerequisites

```bash
pip3 install pymupdf4llm
```

### Usage via OpenClaw

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

# Extract from DOI
python3 scripts/extract_paper.py "10.1234/example.doi" --metadata

# Extract from Semantic Scholar
python3 scripts/extract_paper.py "https://www.semanticscholar.org/paper/..."

# Output as JSON
python3 scripts/extract_paper.py 2301.07041 --format json --output result.json

# Extract with tables
python3 scripts/extract_paper.py /path/to/paper.pdf --tables
```

## Advanced Features

### Citation Network Analysis

```bash
python3 scripts/advanced_analysis.py citations 1706.03762
```

### Multi-Paper Comparison

```bash
python3 scripts/advanced_analysis.py compare paper1.pdf paper2.pdf paper3.pdf --output comparison.md
```

### Figure/Table Extraction

```bash
python3 scripts/advanced_analysis.py ocr paper.pdf --output ./figures/
```

### Related Paper Recommendations

```bash
python3 scripts/advanced_analysis.py recommend 1706.03762
```

### Batch Processing

```bash
# Parallel extraction
python3 scripts/batch_extract.py /path/to/pdfs --output-dir ./output

# With auto-summarization
python3 scripts/batch_extract.py /path/to/pdfs --summarize --concurrency 4

# With custom template
python3 scripts/batch_extract.py /path/to/pdfs --summarize --template ./my-template.md
```

## Supported Input Sources

| Source | Example |
|--------|---------|
| Local PDF | `/path/to/paper.pdf` |
| arXiv ID | `2301.07041` |
| arXiv URL | `https://arxiv.org/abs/2301.07041` |
| DOI | `10.1234/example.doi` |
| Semantic Scholar | `https://www.semanticscholar.org/paper/...` |
| PubMed ID | `PMID:12345678` or `12345678` |
| Remote PDF URL | `https://example.com/paper.pdf` |

## Command-Line Options

### extract_paper.py

| Option | Description |
|--------|-------------|
| `--metadata` | Include metadata in output |
| `--format json` | JSON output format |
| `--tables` | Extract tables |
| `--timeout` | Download timeout (seconds) |
| `--cache-dir` | Cache directory for PDFs |
| `--verbose` | Verbose logging |

### batch_extract.py

| Option | Description |
|--------|-------------|
| `--output-dir` | Output directory |
| `--summarize` | Auto-generate summaries |
| `--concurrency` | Parallel extraction count |
| `--timeout` | Per-paper timeout |
| `--template` | Custom summary template |

### advanced_analysis.py

| Command | Description |
|---------|-------------|
| `compare <files>` | Compare multiple PDFs |
| `citations <id>` | Citation network analysis |
| `ocr <pdf>` | Extract figures/tables |
| `recommend <id>` | Find related papers |

## Skill Structure

```
paper-summary/
├── SKILL.md                    # Skill entry point + trigger config
├── README.md                   # This file
├── TODO.md                     # Development TODO list
├── scripts/
│   ├── extract_paper.py        # Single paper extraction (PDF/arXiv/DOI/URL)
│   ├── batch_extract.py        # Batch directory processing
│   └── advanced_analysis.py    # Advanced analysis tools
└── references/
    └── summary-template.md      # Structured summary template
```

## Output Guidelines

- Use the paper's language for the summary body; use bilingual section headers
- Include quantitative results — actual numbers, not vague claims
- For survey/review papers, emphasize the taxonomy and key reference landscape
- Keep TL;DR to 1-2 sentences maximum
- Rate the paper briefly at the end (novelty, rigor, clarity, impact)

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [pymupdf4llm](https://github.com/pymupdf/pymupdf4llm) for PDF extraction
- [Semantic Scholar API](https://www.semanticscholar.org/) for citation data
- [OpenClaw](https://github.com/openclaw/openclaw) for the agent framework
