#!/usr/bin/env python3
"""
Extract text from academic papers (PDF files) and convert to Markdown.
Supports: local PDF, arXiv, DOI, Semantic Scholar, PubMed, and remote PDF URLs.

Usage:
  python3 extract_paper.py <input> [--output <path>] [--format <markdown|json>]

  <input> can be:
    - Local PDF path:     /path/to/paper.pdf
    - arXiv ID:           2301.07041 or arXiv:2301.07041
    - arXiv URL:          https://arxiv.org/abs/2301.07041
    - DOI:                10.1234/example.doi
    - Semantic Scholar:   https://www.semanticscholar.org/paper/...
    - PubMed ID:         12345678 or PMID:12345678
    - Remote PDF URL:    https://example.com/paper.pdf

  --output <path>:   Write extracted content to file instead of stdout
  --format <format>: Output format: markdown (default) or json
  --tables:          Extract tables using pdfplumber (better for complex tables)
  --cache-dir:       Cache downloaded PDFs to specified directory
"""

import sys
import os
import re
import json
import tempfile
import hashlib
import logging
from datetime import datetime
from pathlib import Path

# =============================================================================
# Logging Setup
# =============================================================================

def setup_logging(verbose: bool = False):
    """Configure logging with timestamps and progress info."""
    level = logging.DEBUG if verbose else logging.INFO
    format_str = '%(asctime)s [%(levelname)s] %(message)s'
    logging.basicConfig(level=level, format=format_str, datefmt='%H:%M:%S')
    return logging.getLogger(__name__)

logger = logging.getLogger(__name__)

# =============================================================================
# Cache Manager
# =============================================================================

class PDFCache:
    """Downloaded PDF cache to avoid re-downloading."""
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
    
    def _hash_url(self, url: str) -> str:
        """Generate hash for URL to use as filename."""
        return hashlib.sha256(url.encode()).hexdigest()[:16]
    
    def get(self, url: str) -> str:
        """Get cached PDF path if exists."""
        if not self.cache_dir:
            return None
        cache_file = os.path.join(self.cache_dir, f"{self._hash_url(url)}.pdf")
        if os.path.exists(cache_file):
            logger.info(f"📂 Using cached: {cache_file}")
            return cache_file
        return None
    
    def put(self, url: str, pdf_path: str) -> str:
        """Cache a downloaded PDF."""
        if not self.cache_dir:
            return pdf_path
        
        cache_file = os.path.join(self.cache_dir, f"{self._hash_url(url)}.pdf")
        import shutil
        shutil.copy2(pdf_path, cache_file)
        logger.info(f"💾 Cached to: {cache_file}")
        return cache_file

# =============================================================================
# URL/ID Resolvers
# =============================================================================

def resolve_arxiv_url(identifier: str) -> str:
    """Convert arxiv ID or URL to direct PDF download URL."""
    identifier = re.sub(r'^arxiv:', '', identifier, flags=re.IGNORECASE).strip()
    
    # Extract ID from URL
    match = re.search(r'arxiv\.org/(?:abs|pdf)/(\d+\.\d+(?:v\d+)?)', identifier)
    if match:
        return f"https://arxiv.org/pdf/{match.group(1)}.pdf"
    
    # Plain ID like 2301.07041
    if re.match(r'^\d{4}\.\d{4,5}(?:v\d+)?$', identifier):
        return f"https://arxiv.org/pdf/{identifier}.pdf"
    
    return None


def resolve_doi_url(doi: str) -> str:
    """Convert DOI to a URL via doi.org redirect. Enhanced for multiple publishers."""
    doi = doi.strip()
    if doi.startswith('10.'):
        return f"https://doi.org/{doi}"
    match = re.match(r'(?:https?://)?doi\.org/(10\..+)', doi)
    if match:
        return f"https://doi.org/{match.group(1)}"
    return None


def get_doi_pdf_url(doi: str, timeout: int = 30) -> str:
    """Enhanced DOI resolver - tries multiple approaches to get PDF URL."""
    import urllib.request
    import urllib.error
    
    doi = doi.strip()
    if not doi.startswith('10.'):
        if re.match(r'(?:https?://)?doi\.org/(10\..+)', doi):
            doi = re.match(r'(?:https?://)?doi\.org/(10\..+)', doi).group(1)
        else:
            return None
    
    # Try doi.org redirect
    try:
        url = f"https://doi.org/{doi}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            final_url = resp.url
            
            # Check if directly a PDF
            if final_url.endswith('.pdf'):
                return final_url
            
            # Common publisher PDF patterns
            publisher_patterns = [
                (r'sciencedirect\.com/science/article/([^/]+)', 'sciencedirect'),
                (r'springer\.com/[^/]+/[^/]+/([^/]+)', 'springer'),
                (r'ieeexplore\.ieee\.org/document/(\d+)', 'ieee'),
                (r'acm\.org/doi/([^/]+)', 'acm'),
                (r' nature\.com/articles/([^/]+)', 'nature'),
                (r'plos\.org/([^/]+)', 'plos'),
                (r'arxiv\.org/abs/(\d+\.\d+)', 'arxiv'),
            ]
            
            for pattern, publisher in publisher_patterns:
                match = re.search(pattern, final_url)
                if match:
                    paper_id = match.group(1)
                    # Build direct PDF URL
                    if publisher == 'sciencedirect':
                        return f"https://www.sciencedirect.com/science/article/pii/{paper_id}/pdf"
                    elif publisher == 'springer':
                        return f"https://link.springer.com/content/pdf/{paper_id}.pdf"
                    elif publisher == 'ieee':
                        return f"https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={paper_id}"
                    elif publisher == 'acm':
                        return f"https://dl.acm.org/doi/pdf/{paper_id}"
                    elif publisher == 'nature':
                        return f"https://www.nature.com/articles/{paper_id}.pdf"
                    elif publisher == 'plos':
                        return f"https://journals.plos.org/plosone/article/file?id=10.1371/journal.{paper_id}&type=printable"
                    elif publisher == 'arxiv':
                        return f"https://arxiv.org/pdf/{paper_id}.pdf"
            
            # If not matched, try direct PDF URL patterns
            return final_url
            
    except Exception as e:
        logger.warning(f"DOI resolution failed: {e}")
        return None


def resolve_semanticscholar(identifier: str) -> str:
    """Extract PDF URL from Semantic Scholar page."""
    import urllib.request
    
    match = re.search(r'semanticscholar\.org/(?:paper|reader)/([^/?\s]+)', identifier)
    if not match:
        return None
    
    paper_id = match.group(1)
    api_url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}?fields=title,authors,venue,year,externalIds,openAccessPdf"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            
            if data.get('openAccessPdf'):
                return data['openAccessPdf'].get('url')
            
            external = data.get('externalIds', {})
            if external.get('arXiv'):
                return f"https://arxiv.org/pdf/{external['arXiv']}.pdf"
            
            if external.get('DOI'):
                return f"https://doi.org/{external['DOI']}"
        
        return None
    except Exception as e:
        logger.warning(f"Semantic Scholar API error: {e}")
        return None


def resolve_pubmed(identifier: str) -> str:
    """Get PDF URL from PubMed ID."""
    import urllib.request
    
    match = re.search(r'(?:pmid:)?(\d+)', identifier, re.IGNORECASE)
    if not match:
        return None
    
    pmid = match.group(1)
    api_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            result = data.get('result', {}).get(pmid, {})
            
            if result.get('elocationid'):
                doi_match = re.search(r'doi:(.+)$', result['elocationid'])
                if doi_match:
                    return f"https://doi.org/{doi_match.group(1).strip()}"
        
        return None
    except Exception as e:
        logger.warning(f"PubMed API error: {e}")
        return None


# =============================================================================
# PDF Download & Extraction
# =============================================================================

def download_pdf(url: str, timeout: int = 60, cache: PDFCache = None) -> str:
    """Download PDF from URL to a temp file. Returns temp file path."""
    import urllib.request
    import urllib.error

    # Check cache first
    if cache:
        cached = cache.get(url)
        if cached:
            return cached

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/120.0.0.0 Safari/537.36'
    }
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get('Content-Type', '')
            
            if 'pdf' not in content_type.lower() and not url.endswith('.pdf'):
                final_url = resp.url
                if 'arxiv.org' in final_url and not final_url.endswith('.pdf'):
                    final_url = final_url.replace('/abs/', '/pdf/') + '.pdf'
                    req2 = urllib.request.Request(final_url, headers=headers)
                    resp = urllib.request.urlopen(req2, timeout=timeout)

            tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            tmp.write(resp.read())
            tmp.close()
            
            # Cache if enabled
            if cache:
                tmp_path = cache.put(url, tmp.name)
                return tmp_path
            
            return tmp.name
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} downloading {url}: {e.reason}")
    except Exception as e:
        raise RuntimeError(f"Failed to download {url}: {e}")


def extract_pdf_to_markdown(pdf_path: str, extract_tables: bool = False) -> dict:
    """Extract PDF content as Markdown, optionally with tables."""
    try:
        import pymupdf4llm
    except ImportError:
        print("ERROR: pymupdf4llm not installed. Run: pip3 install pymupdf4llm", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    result = {'markdown': pymupdf4llm.to_markdown(pdf_path)}
    
    if extract_tables:
        try:
            import pymupdf
            doc = pymupdf.open(pdf_path)
            tables = []
            
            for page_num, page in enumerate(doc):
                tabs = page.find_tables()
                for tab in tabs:
                    if tab.extract():
                        tables.append({
                            'page': page_num + 1,
                            'content': tab.extract()
                        })
            
            if tables:
                result['tables'] = tables
            doc.close()
        except Exception as e:
            logger.warning(f"Table extraction failed: {e}")
    
    return result


def extract_metadata(pdf_path: str) -> dict:
    """Extract basic metadata from PDF."""
    try:
        import pymupdf
        doc = pymupdf.open(pdf_path)
        meta = doc.metadata or {}
        doc.close()
        return {
            'title': meta.get('title', ''),
            'author': meta.get('author', ''),
            'subject': meta.get('subject', ''),
            'pages': doc.page_count if hasattr(doc, 'page_count') else 0,
        }
    except Exception:
        return {}


# =============================================================================
# Main
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Extract academic paper text as Markdown')
    parser.add_argument('input', help='PDF path, arXiv ID/URL, DOI, Semantic Scholar URL, PubMed ID, or remote PDF URL')
    parser.add_argument('--output', '-o', help='Output file path (default: stdout)')
    parser.add_argument('--metadata', action='store_true', help='Also print metadata as JSON header')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown', help='Output format')
    parser.add_argument('--tables', action='store_true', help='Extract tables using pdfplumber')
    parser.add_argument('--timeout', type=int, default=60, help='Download timeout in seconds')
    parser.add_argument('--cache-dir', '-c', help='Cache downloaded PDFs to directory')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    logger = setup_logging(args.verbose)
    
    raw_input = args.input.strip()
    tmp_pdf = None
    cache = PDFCache(args.cache_dir) if args.cache_dir else None

    try:
        # 1) Determine source type and get local PDF path
        pdf_path = None
        source_type = None
        source_url = None
        
        # Check local file
        if os.path.isfile(raw_input):
            pdf_path = os.path.abspath(raw_input)
            source_type = 'local'
        
        # Check arXiv
        elif not pdf_path:
            arxiv_url = resolve_arxiv_url(raw_input)
            if arxiv_url:
                logger.info(f"📥 Downloading from arXiv: {arxiv_url}")
                pdf_path = download_pdf(arxiv_url, timeout=args.timeout, cache=cache)
                source_type = 'arxiv'
                source_url = arxiv_url
        
        # Check DOI
        elif not pdf_path:
            doi_url = resolve_doi_url(raw_input)
            if doi_url:
                logger.info(f"🔗 Resolving DOI: {doi_url}")
                # Enhanced DOI resolution
                pdf_url = get_doi_pdf_url(doi_url, timeout=args.timeout)
                if pdf_url:
                    logger.info(f"📥 Downloading PDF from: {pdf_url}")
                    pdf_path = download_pdf(pdf_url, timeout=args.timeout, cache=cache)
                    source_type = 'doi'
                    source_url = pdf_url
                else:
                    logger.info(f"📥 Downloading via DOI redirect: {doi_url}")
                    pdf_path = download_pdf(doi_url, timeout=args.timeout, cache=cache)
                    source_type = 'doi'
                    source_url = doi_url
        
        # Check Semantic Scholar
        elif not pdf_path and 'semanticscholar' in raw_input.lower():
            ss_url = resolve_semanticscholar(raw_input)
            if ss_url:
                logger.info(f"📥 Downloading from Semantic Scholar: {ss_url}")
                pdf_path = download_pdf(ss_url, timeout=args.timeout, cache=cache)
                source_type = 'semanticscholar'
                source_url = ss_url
        
        # Check PubMed
        elif not pdf_path and re.search(r'pmid[:\s]?\d+', raw_input, re.IGNORECASE):
            pm_url = resolve_pubmed(raw_input)
            if pm_url:
                logger.info(f"📥 Resolving PubMed: {pm_url}")
                pdf_path = download_pdf(pm_url, timeout=args.timeout, cache=cache)
                source_type = 'pubmed'
                source_url = pm_url
        
        # Check remote URL
        elif not pdf_path and raw_input.startswith(('http://', 'https://')):
            logger.info(f"📥 Downloading PDF: {raw_input}")
            pdf_path = download_pdf(raw_input, timeout=args.timeout, cache=cache)
            source_type = 'url'
            source_url = raw_input
        
        else:
            logger.error(f"ERROR: Cannot resolve input '{raw_input}'")
            sys.exit(1)

        # 2) Extract
        logger.info(f"📄 Extracting text from PDF ({source_type})...")
        extraction = extract_pdf_to_markdown(pdf_path, extract_tables=args.tables)
        md_text = extraction['markdown']
        
        # 3) Metadata
        meta = extract_metadata(pdf_path)
        meta['source_type'] = source_type
        if source_url:
            meta['source_url'] = source_url

        # 4) Output
        if args.format == 'json':
            output_data = {
                'metadata': meta,
                'content': md_text,
            }
            if 'tables' in extraction:
                output_data['tables'] = extraction['tables']
            
            result = json.dumps(output_data, ensure_ascii=False, indent=2)
        else:
            output_parts = []
            if args.metadata and meta:
                output_parts.append(f"<!-- METADATA: {json.dumps(meta, ensure_ascii=False)} -->")
            output_parts.append(md_text)
            result = '\n'.join(output_parts)

        if args.output:
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)
            logger.info(f"✅ Extracted to: {args.output}")
        else:
            print(result)

    finally:
        if tmp_pdf and os.path.exists(tmp_pdf):
            os.unlink(tmp_pdf)


if __name__ == '__main__':
    main()
