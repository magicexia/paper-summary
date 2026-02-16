---
name: paper-summary
description: >
  Academic paper summarization and analysis agent. Extracts text from PDF papers
  (local files, arXiv IDs/URLs, DOIs, Semantic Scholar URLs, PubMed IDs, or remote PDF URLs) 
  using pymupdf4llm, then produces structured research summaries. Supports single and batch processing.
  Use when user asks to: summarize a paper, analyze a research paper, read a PDF paper,
  extract key findings from a paper, review literature, do a literature survey,
  总结论文, 分析文献, 论文解读, 文献综述.
---

# Paper Summary

Summarize academic papers into structured research reports.

## Prerequisites

- Python 3.8+ with `pymupdf4llm` installed
- Install: `pip3 install pymupdf4llm`

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

## Basic Workflow

### Single Paper

```bash
python3 {skill_dir}/scripts/extract_paper.py "<input>" --metadata
```

### Batch Processing

```bash
python3 {skill_dir}/scripts/batch_extract.py <pdf_directory> --summarize --concurrency 4
```

---

## Advanced Features

### 1. 📊 Multi-Paper Comparison (多论文对比)

Compare multiple papers and generate comparison tables.

```bash
python3 {skill_dir}/scripts/advanced_analysis.py compare paper1.pdf paper2.pdf paper3.pdf --output comparison.md
```

**Output**: Markdown with comparison tables for:
- Basic info (title, authors, pages)
- Methods
- Experimental results
- Pros/Cons summary

---

### 2. 🔗 Citation Network Analysis (引用网络分析)

Analyze citations and references of a paper.

```bash
# Basic citation analysis
python3 {skill_dir}/scripts/advanced_analysis.py citations 2301.07054

# With output file
python3 {skill_dir}/scripts/advanced_analysis.py citations 10.48550/arXiv.2301.07054 --output citations.md
```

**Output**: Markdown with:
- Citation count, reference count
- Reference list
- Citing papers
- Simple network visualization

---

### 3. 🖼️ Figure/Table Extraction (图表提取)

Extract images and tables from PDF.

```bash
# Extract to default directory
python3 {skill_dir}/scripts/advanced_analysis.py ocr paper.pdf

# Extract to custom directory
python3 {skill_dir}/scripts/advanced_analysis.py ocr paper.pdf --output ./figures/
```

**Output**:
- Images saved as PNG/JPEG
- Tables saved as Markdown
- Index page with list

---

### 4. 🎯 Related Paper Recommendation (相关论文推荐)

Find related papers based on content.

```bash
# Find related papers
python3 {skill_dir}/scripts/advanced_analysis.py recommend 2301.07054

# With output
python3 {skill_dir}/scripts/advanced_analysis.py recommend 10.48550/arXiv.2301.07054 --output recommendations.md
```

**Output**: Markdown with:
- Paper recommendations
- Quick search links
- Related keywords

---

## All Options

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

## Output Guidelines

- Use the paper's language for the summary body; use bilingual section headers
- Include quantitative results — actual numbers, not vague claims
- For survey/review papers, emphasize the taxonomy and key reference landscape
- Keep TL;DR to 1-2 sentences maximum
- Rate the paper briefly at the end (novelty, rigor, clarity, impact)

## Paths

- Extraction script: `scripts/extract_paper.py`
- Batch script: `scripts/batch_extract.py`
- Advanced analysis: `scripts/advanced_analysis.py`
- Summary template: `references/summary-template.md`
- Default output: `{workspace}/paper-summaries/`
