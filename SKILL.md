---
name: paper-summary
description: >
  Academic paper summarization and analysis agent. Extracts text from PDF papers
  (local files, arXiv IDs/URLs, DOIs, Semantic Scholar URLs, PubMed IDs, or remote PDF URLs) 
  using pymupdf4llm, then produces structured research summaries.
  
  **Basic**: summarize a paper, analyze a research paper, read a PDF paper, extract key findings,
  总结论文, 分析文献, 论文解读, 文献综述.
  
  **Advanced (trigger these keywords)**:
  - Compare/M对比: "compare papers", "对比论文", "多论文分析"
  - Citations/引用: "citation network", "引用分析", "谁引用了这篇论文"
  - Figures/图表: "extract figures", "提取图表", "图片提取"
  - Related/推荐: "related papers", "类似论文", "推荐论文"
  
  Use when user asks to: summarize papers, compare papers, analyze citations, extract figures,
  find related papers, do literature survey, 总结论文, 分析文献, 论文对比, 引用网络, 图表提取.
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

## Natural Language Triggers

The skill automatically routes to the appropriate function based on your request:

### 📊 Compare Papers (多论文对比)

**Trigger keywords**: "compare", "对比", "对比分析", "比较论文"
**Examples**:
- "对比这几篇论文的特点"
- "Compare paper A and paper B"
- "分析这三个论文的差异"

**Command**: `python3 {skill_dir}/scripts/advanced_analysis.py compare <pdf1> <pdf2> ...`

### 🔗 Citation Network (引用网络分析)

**Trigger keywords**: "citation", "引用", "谁引用了", "参考文献"
**Examples**:
- "这篇论文被谁引用了？"
- "分析论文的引用网络"
- "show citations of this paper"

**Command**: `python3 {skill_dir}/scripts/advanced_analysis.py citations <paper_id>`

### 🖼️ Extract Figures (图表提取)

**Trigger keywords**: "extract figure", "提取图表", "图片", "figures", "图表"
**Examples**:
- "提取论文中的图表"
- "extract all figures from this PDF"
- "保存论文里的图片"

**Command**: `python3 {skill_dir}/scripts/advanced_analysis.py ocr <pdf>`

### 🎯 Related Papers (相关论文推荐)

**Trigger keywords**: "related", "类似", "推荐论文", "similar"
**Examples**:
- "推荐类似的论文"
- "find related papers"
- "有哪些论文和这个相关？"

**Command**: `python3 {skill_dir}/scripts/advanced_analysis.py recommend <paper_id>`

## Basic Workflow

### Single Paper Extraction

```bash
python3 {skill_dir}/scripts/extract_paper.py "<input>" --metadata
```

### Batch Processing

```bash
python3 {skill_dir}/scripts/batch_extract.py <pdf_directory> --summarize --concurrency 4
```

## Advanced Features (Manual)

### Citation Network Analysis

```bash
python3 {skill_dir}/scripts/advanced_analysis.py citations 1706.03762
```

### Multi-Paper Comparison

```bash
python3 {skill_dir}/scripts/advanced_analysis.py compare paper1.pdf paper2.pdf paper3.pdf --output comparison.md
```

### Figure/Table Extraction

```bash
python3 {skill_dir}/scripts/advanced_analysis.py ocr paper.pdf --output ./figures/
```

### Related Paper Recommendation

```bash
python3 {skill_dir}/scripts/advanced_analysis.py recommend 1706.03762
```

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
