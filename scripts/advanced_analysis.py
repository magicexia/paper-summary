#!/usr/bin/env python3
"""
Advanced paper analysis: comparison, citation network, OCR, recommendations.

Usage:
  python3 advanced_analysis.py <command> [options]

Commands:
  compare     - Compare multiple papers
  citations   - Analyze citation network
  ocr         - Extract figures and tables from PDF
  recommend   - Find related papers

Examples:
  # Compare papers
  python3 advanced_analysis.py compare paper1.pdf paper2.pdf paper3.pdf --output comparison.md
  
  # Citation network
  python3 advanced_analysis.py citations 2301.07054 --depth 2
  
  # OCR extraction
  python3 advanced_analysis.py ocr paper.pdf --output ./figures/
  
  # Related papers
  python3 advanced_analysis.py recommend 10.48550/arXiv.2301.07054
"""

import sys
import os
import re
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# =============================================================================
# Logging
# =============================================================================

def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    format_str = '%(asctime)s [%(levelname)s] %(message)s'
    logging.basicConfig(level=level, format=format_str, datefmt='%H:%M:%S')
    return logging.getLogger(__name__)

logger = logging.getLogger(__name__)

# =============================================================================
# Base: Paper Metadata Fetcher
# =============================================================================

def fetch_paper_metadata(identifier: str) -> Optional[Dict]:
    """Fetch paper metadata from various sources."""
    import urllib.request
    
    # Try Semantic Scholar API first
    ss_patterns = [
        r'semanticscholar\.org/paper/([^/?]+)',
        r'ss:([^/?]+)',
    ]
    
    for pattern in ss_patterns:
        match = re.search(pattern, identifier, re.IGNORECASE)
        if match:
            paper_id = match.group(1)
            return fetch_semanticscholar(paper_id)
    
    # Try arXiv - use Semantic Scholar with arXiv: prefix
    arxiv_pattern = r'(\d{4}\.\d{4,5})'
    match = re.search(arxiv_pattern, identifier)
    if match:
        arxiv_id = match.group(1)
        # Try Semantic Scholar first (more data)
        ss_result = fetch_semanticscholar(f"arXiv:{arxiv_id}")
        if ss_result:
            return ss_result
        # Fallback to arXiv API
        return fetch_arxiv_metadata(arxiv_id)
    
    # Try DOI
    doi_pattern = r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)'
    match = re.search(doi_pattern, identifier, re.IGNORECASE)
    if match:
        return fetch_doi_metadata(match.group(1))
    
    return None


def fetch_semanticscholar(paper_id: str) -> Optional[Dict]:
    """Fetch paper data from Semantic Scholar API."""
    import urllib.request
    
    url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}?fields=title,authors,year,venue,abstract,citationCount,referenceCount,citations.title,references.title,externalIds"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return {
                'id': paper_id,
                'title': data.get('title', ''),
                'authors': [a['name'] for a in data.get('authors', [])],
                'year': data.get('year'),
                'venue': data.get('venue', ''),
                'abstract': data.get('abstract', ''),
                'citations': data.get('citations', []),
                'references': data.get('references', []),
                'citation_count': data.get('citationCount', 0),
                'reference_count': data.get('referenceCount', 0),
                'external_ids': data.get('externalIds', {}),
            }
    except Exception as e:
        logger.warning(f"Semantic Scholar API error: {e}")
        return None


def fetch_arxiv_metadata(arxiv_id: str) -> Optional[Dict]:
    """Fetch metadata from arXiv."""
    import urllib.request
    
    url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            import xml.etree.ElementTree as ET
            data = resp.read().decode()
            root = ET.fromstring(data)
            entry = root.find('{http://www.w3.org/2005/Atom}entry')
            
            if entry is None:
                return None
            
            def text(el, tag):
                e = el.find(f'{{http://www.w3.org/2005/Atom}}{tag}')
                return e.text if e is not None else ''
            
            return {
                'id': arxiv_id,
                'title': text(entry, 'title').replace('\n', ' '),
                'authors': [a.text for a in entry.findall('{http://www.w3.org/2005/Atom}author')],
                'year': text(entry, 'published')[:4],
                'venue': 'arXiv',
                'abstract': text(entry, 'summary').replace('\n', ' '),
                'arxiv_id': arxiv_id,
                'url': f'https://arxiv.org/abs/{arxiv_id}',
            }
    except Exception as e:
        logger.warning(f"arXiv API error: {e}")
        return None


def fetch_doi_metadata(doi: str) -> Optional[Dict]:
    """Fetch metadata from DOI."""
    import urllib.request
    
    url = f"https://doi.org/{doi}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
        req.add_header('Accept', 'application/vnd.citationstyles.csl+json')
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            # Try to follow redirect and get JSON
            final_url = resp.url
            
            # Use CrossRef API
            cr_url = f"https://api.crossref.org/works/{doi}"
            req2 = urllib.request.Request(cr_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req2, timeout=30) as cr_resp:
                data = json.loads(cr_resp.read().decode())
                item = data.get('message', {})
                
                return {
                    'doi': doi,
                    'title': item.get('title', [''])[0] if item.get('title') else '',
                    'authors': [a.get('given', '') + ' ' + a.get('family', '') for a in item.get('author', [])],
                    'year': item.get('published-print', {}).get('date-parts', [[None]])[0][0],
                    'venue': item.get('container-title', [''])[0] if item.get('container-title') else '',
                    'abstract': item.get('abstract', ''),
                }
    except Exception as e:
        logger.warning(f"DOI/CrossRef API error: {e}")
        return None


# =============================================================================
# Feature 1: Multi-Paper Comparison
# =============================================================================

def compare_papers(paper_paths: List[str], output: str = None) -> str:
    """Compare multiple papers and generate a comparison table."""
    papers = []
    
    # Import extract function
    sys.path.insert(0, os.path.dirname(__file__))
    from extract_paper import extract_pdf_to_markdown, extract_metadata
    
    logger.info(f"📊 Comparing {len(paper_paths)} papers...")
    
    for i, path in enumerate(paper_paths):
        logger.info(f"  [{i+1}/{len(paper_paths)}] Processing: {os.path.basename(path)}")
        
        if not os.path.exists(path):
            logger.warning(f"  ⚠️ File not found: {path}")
            continue
        
        try:
            md = extract_pdf_to_markdown(path)
            meta = extract_metadata(path)
            
            # Extract key info
            content = md.get('markdown', '')
            
            papers.append({
                'path': path,
                'filename': os.path.basename(path),
                'metadata': meta,
                'content': content,
                'word_count': len(content.split()),
            })
        except Exception as e:
            logger.warning(f"  ⚠️ Error: {e}")
    
    if not papers:
        return "No papers to compare."
    
    # Generate comparison
    result = f"""# 📊 论文对比分析 / Paper Comparison

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**论文数量**: {len(papers)}

---

## 📋 基本信息 / Basic Info

| 论文 | 标题 | 作者 | 页数 | 字数 |
|------|------|------|------|------|
"""
    
    for p in papers:
        title = p['metadata'].get('title', p['filename'])[:40]
        author = p['metadata'].get('author', 'Unknown')[:20]
        pages = p['metadata'].get('pages', 0)
        words = p['word_count']
        result += f"| {p['filename'][:20]} | {title} | {author} | {pages} | {words} |\n"
    
    result += """
---

## 🔬 方法对比 / Method Comparison

"""
    
    for p in papers:
        result += f"""### {p['filename']}

"""
        # Try to extract method section
        content = p['content']
        method_match = re.search(r'(?i)(##?\s*(?:method|approach|methodology|proposed method|our method|core method)).{0,500}', content)
        if method_match:
            result += f"**方法概要**: {method_match.group(0)[:200]}...\n\n"
        else:
            result += f"**方法概要**: (提取失败，请查看原文)\n\n"
    
    result += """
---

## 📊 实验结果 / Experimental Results

"""
    
    for p in papers:
        result += f"""### {p['filename']}

"""
        content = p['content']
        # Look for tables or results
        results_match = re.search(r'(?i)(##?\s*(?:experiment|result|evaluation|performance)).{0,800}', content)
        if results_match:
            result += f"{results_match.group(0)[:300]}...\n\n"
        else:
            result += "(实验部分提取失败)\n\n"
    
    result += """
---

## 🎯 总结 / Summary

| 论文 | 创新点 | 优势 | 劣势 |
|------|--------|------|------|
"""
    
    for p in papers:
        result += f"| {p['filename'][:15]} | | | |\n"
    
    result += """
---

*此对比由 AI 生成，仅供参考*
"""
    
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            f.write(result)
        logger.info(f"✅ Comparison saved to: {output}")
    
    return result


# =============================================================================
# Feature 2: Citation Network Analysis
# =============================================================================

def analyze_citations(paper_id: str, depth: int = 1, output: str = None) -> str:
    """Analyze citation network of a paper."""
    
    logger.info(f"🔗 Analyzing citation network for: {paper_id}")
    
    # Fetch main paper
    main_paper = fetch_paper_metadata(paper_id)
    
    if not main_paper:
        return f"❌ Could not fetch metadata for: {paper_id}"
    
    result = f"""# 🔗 引用网络分析 / Citation Network Analysis

**目标论文**: {main_paper.get('title', 'Unknown')}
**作者**: {', '.join(main_paper.get('authors', [])[:3])}
**年份**: {main_paper.get('year', 'N/A')}

---

## 📈 基本统计

| 指标 | 数值 |
|------|------|
| 引用数 (Citations) | {main_paper.get('citation_count', 0)} |
| 参考文献数 (References) | {main_paper.get('reference_count', 0)} |

---

## 📚 参考文献 (References)

"""
    
    # Get references
    references = main_paper.get('references', [])
    if references:
        for i, ref in enumerate(references[:20], 1):
            title = ref.get('title', 'Unknown')[:60]
            result += f"{i}. {title}\n"
        
        if len(references) > 20:
            result += f"\n... 还有 {len(references) - 20} 条参考文献\n"
    else:
        result += "(未获取到参考文献)\n"
    
    result += """

---

## 🎯 引用本论文的论文 (Citing Papers)

"""
    
    citations = main_paper.get('citations', [])
    if citations:
        for i, cit in enumerate(citations[:20], 1):
            title = cit.get('title', 'Unknown')[:60]
            result += f"{i}. {title}\n"
        
        if len(citations) > 20:
            result += f"\n... 还有 {len(citations) - 20} 篇引用\n"
    else:
        result += "(未获取到引用数据)\n"
    
    # Build simple network
    result += """
---

## 🕸️ 引用关系图 (简化版)

```
"""
    
    result += f"┌─────────────────────────────────────┐\n"
    result += f"│ {main_paper.get('title', 'Main')[:35]} │\n"
    result += f"└─────────────────────────────────────┘\n"
    result += f"              ↑ 引用\n"
    result += f"              │\n"
    
    if citations:
        cit_title = citations[0].get('title', 'Paper 1')[:25]
        result += f"┌─────────────────────────────────────┐\n"
        result += f"│ {cit_title} │\n"
        result += f"└─────────────────────────────────────┘\n"
    
    result += """```

---

## 💡 关键发现

"""
    
    # Analyze
    if main_paper.get('citation_count', 0) > 100:
        result += f"- 🔥 高影响力论文: 被引用 {main_paper.get('citation_count')} 次\n"
    
    if main_paper.get('reference_count', 0) > 50:
        result += f"- 📚 综述性质: 参考文献达 {main_paper.get('reference_count')} 篇\n"
    
    result += "- 使用 [Semantic Scholar](https://www.semanticscholar.org) 查看完整引用网络\n"
    
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            f.write(result)
        logger.info(f"✅ Analysis saved to: {output}")
    
    return result


# =============================================================================
# Feature 3: Figure/Table OCR Extraction
# =============================================================================

def extract_figures(pdf_path: str, output_dir: str = None) -> str:
    """Extract figures and tables from PDF."""
    
    logger.info(f"📊 Extracting figures from: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        return f"❌ File not found: {pdf_path}"
    
    try:
        import pymupdf
    except ImportError:
        return "❌ pymupdf not installed. Run: pip3 install pymupdf"
    
    doc = pymupdf.open(pdf_path)
    
    output_dir = output_dir or os.path.splitext(pdf_path)[0] + '_figures'
    os.makedirs(output_dir, exist_ok=True)
    
    result = f"""# 📊 图表提取 / Figure & Table Extraction

**来源**: {os.path.basename(pdf_path)}
**页数**: {len(doc)}
**提取时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📑 图表列表

"""
    
    figures_found = 0
    tables_found = 0
    
    for page_num, page in enumerate(doc, 1):
        # Extract images
        images = page.get_images()
        if images:
            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Save image
                img_filename = f"page{page_num}_img{img_index+1}.{base_image['ext']}"
                img_path = os.path.join(output_dir, img_filename)
                
                with open(img_path, "wb") as f:
                    f.write(image_bytes)
                
                result += f"- **图 {page_num}.{img_index+1}**: `{img_filename}` (page {page_num})\n"
                figures_found += 1
        
        # Extract tables
        tabs = page.find_tables()
        if tabs:
            for tab_index, tab in enumerate(tabs):
                table_data = tab.extract()
                if table_data:
                    # Save as markdown
                    table_filename = f"page{page_num}_table{tab_index+1}.md"
                    table_path = os.path.join(output_dir, table_filename)
                    
                    # Convert to markdown
                    md_table = ""
                    for row in table_data[:10]:  # First 10 rows
                        md_table += "| " + " | ".join(str(cell or '') for cell in row) + " |\n"
                    
                    with open(table_path, 'w', encoding='utf-8') as f:
                        f.write(md_table)
                    
                    result += f"- **表 {page_num}.{tab_index+1}**: `{table_filename}` (page {page_num})\n"
                    tables_found += 1
    
    doc.close()
    
    result += f"""

---

## 📊 统计

- 🖼️ 图片总数: {figures_found}
- 📋 表格总数: {tables_found}
- 📁 输出目录: `{output_dir}`

---

*提示: 使用图像识别工具可以进一步提取图表中的文字内容*
"""
    
    logger.info(f"✅ Extracted {figures_found} images and {tables_found} tables")
    
    if output_dir:
        logger.info(f"📁 Files saved to: {output_dir}")
    
    return result


# =============================================================================
# Feature 4: Related Paper Recommendation
# =============================================================================

def recommend_papers(paper_id: str, output: str = None) -> str:
    """Find related papers based on content similarity."""
    
    logger.info(f"🎯 Finding related papers for: {paper_id}")
    
    # Fetch paper
    paper = fetch_paper_metadata(paper_id)
    
    if not paper:
        return f"❌ Could not fetch metadata for: {paper_id}"
    
    # Get external IDs for search
    ext_ids = paper.get('external_ids', {})
    arxiv_id = ext_ids.get('arXiv')
    doi = ext_ids.get('DOI')
    
    result = f"""# 🎯 相关论文推荐 / Related Paper Recommendations

**基于论文**: {paper.get('title', 'Unknown')}
**作者**: {', '.join(paper.get('authors', [])[:3])}
**年份**: {paper.get('year', 'N/A')}

---

## 🔍 推荐依据

"""
    
    if arxiv_id:
        result += f"- arXiv ID: `{arxiv_id}`\n"
    if doi:
        result += f"- DOI: `{doi}`\n"
    
    result += f"- 引用数: {paper.get('citation_count', 0)}\n"
    
    result += """
---

## 📚 推荐论文

"""
    
    # Use Semantic Scholar recommendations if available
    if arxiv_id:
        rec_url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}/recommendations?limit=10"
    else:
        rec_url = None
    
    recommendations = []
    
    if rec_url:
        import urllib.request
        try:
            req = urllib.request.Request(rec_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                recommendations = data.get('data', [])[:10]
        except Exception as e:
            logger.warning(f"Recommendations API error: {e}")
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            title = rec.get('title', 'Unknown')[:60]
            year = rec.get('year', 'N/A')
            citation_count = rec.get('citationCount', 0)
            paper_id = rec.get('paperId', '')
            
            result += f"""### {i}. {title}

- 📅 年份: {year}
- 🔗 引用: {citation_count}
- 🔗 链接: https://www.semanticscholar.org/paper/{paper_id}

"""
    else:
        # Fallback: recommend based on keywords from title
        title = paper.get('title', '')
        keywords = [w for w in re.findall(r'\b[a-zA-Z]{4,}\b', title.lower()) if w not in ['with', 'from', 'using', 'based', 'learning', 'network', 'neural']]
        
        result += "*未能获取自动推荐，请手动搜索以下关键词:*\n\n"
        result += "**建议搜索关键词**:\n"
        for kw in keywords[:5]:
            result += f"- `{kw}`\n"
        
        result += f"""
---

## 🔗 快速搜索链接

- [Semantic Scholar](https://www.semanticscholar.org/search?q={title[:30]})
- [Google Scholar](https://scholar.google.com/scholar?q={title[:30]})
- [arXiv](https://arxiv.org/search/?searchtype=all&query={title[:30]})
"""
    
    if output:
        with open(output, 'w', encoding='utf-8') as f:
            f.write(result)
        logger.info(f"✅ Recommendations saved to: {output}")
    
    return result


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Advanced paper analysis tools',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare multiple papers')
    compare_parser.add_argument('papers', nargs='+', help='PDF files to compare')
    compare_parser.add_argument('--output', '-o', help='Output markdown file')
    
    # Citations command
    citations_parser = subparsers.add_parser('citations', help='Analyze citation network')
    citations_parser.add_argument('paper', help='Paper ID (arXiv, DOI, or Semantic Scholar ID)')
    citations_parser.add_argument('--depth', type=int, default=1, help='Analysis depth')
    citations_parser.add_argument('--output', '-o', help='Output markdown file')
    
    # OCR command
    ocr_parser = subparsers.add_parser('ocr', help='Extract figures and tables')
    ocr_parser.add_argument('pdf', help='PDF file to extract from')
    ocr_parser.add_argument('--output', '-o', help='Output directory')
    
    # Recommend command
    recommend_parser = subparsers.add_parser('recommend', help='Find related papers')
    recommend_parser.add_argument('paper', help='Paper ID')
    recommend_parser.add_argument('--output', '-o', help='Output markdown file')
    
    args = parser.parse_args()
    
    global logger
    logger = setup_logging(args.verbose)
    
    if not args.command:
        parser.print_help()
        print("\n" + "="*50)
        print("快速开始 / Quick Start:")
        print("="*50)
        print("# Compare papers")
        print("python3 advanced_analysis.py compare paper1.pdf paper2.pdf")
        print()
        print("# Citation network")
        print("python3 advanced_analysis.py citations 2301.07054")
        print()
        print("# Extract figures")
        print("python3 advanced_analysis.py ocr paper.pdf")
        print()
        print("# Find related papers")
        print("python3 advanced_analysis.py recommend 10.48550/arXiv.2301.07054")
        return
    
    # Execute command
    if args.command == 'compare':
        result = compare_papers(args.papers, args.output)
        print(result)
    
    elif args.command == 'citations':
        result = analyze_citations(args.paper, args.depth, args.output)
        print(result)
    
    elif args.command == 'ocr':
        result = extract_figures(args.pdf, args.output)
        print(result)
    
    elif args.command == 'recommend':
        result = recommend_papers(args.paper, args.output)
        print(result)


if __name__ == '__main__':
    main()
