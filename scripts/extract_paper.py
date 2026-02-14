#!/usr/bin/env python3
"""
Extract text from academic papers (PDF files) and convert to Markdown.
Supports: local PDF paths, arxiv URLs/IDs, and remote PDF URLs.

Usage:
  python3 extract_paper.py <input> [--output <path>]

  <input> can be:
    - Local PDF path:  /path/to/paper.pdf
    - arXiv ID:        2301.07041 or arXiv:2301.07041
    - arXiv URL:       https://arxiv.org/abs/2301.07041
    - Remote PDF URL:  https://example.com/paper.pdf
    - DOI:             10.1234/example.doi

  --output <path>:  Write extracted markdown to file instead of stdout
"""

import sys
import os
import re
import tempfile
import json

def resolve_arxiv_url(identifier: str) -> str:
    """Convert arxiv ID or URL to direct PDF download URL."""
    # Strip 'arXiv:' prefix
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
    """Convert DOI to a URL via doi.org redirect."""
    doi = doi.strip()
    if doi.startswith('10.'):
        return f"https://doi.org/{doi}"
    match = re.match(r'(?:https?://)?doi\.org/(10\..+)', doi)
    if match:
        return f"https://doi.org/{match.group(1)}"
    return None


def download_pdf(url: str, timeout: int = 60) -> str:
    """Download PDF from URL to a temp file. Returns temp file path."""
    import urllib.request
    import urllib.error

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/120.0.0.0 Safari/537.36'
    }
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get('Content-Type', '')
            # Follow redirects to actual PDF (e.g., DOI → publisher → PDF)
            if 'pdf' not in content_type.lower() and not url.endswith('.pdf'):
                # Try appending .pdf for arxiv-style URLs
                final_url = resp.url
                if 'arxiv.org' in final_url and not final_url.endswith('.pdf'):
                    final_url = final_url.replace('/abs/', '/pdf/') + '.pdf'
                    req2 = urllib.request.Request(final_url, headers=headers)
                    resp = urllib.request.urlopen(req2, timeout=timeout)

            tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            tmp.write(resp.read())
            tmp.close()
            return tmp.name
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} downloading {url}: {e.reason}")
    except Exception as e:
        raise RuntimeError(f"Failed to download {url}: {e}")


def extract_pdf_to_markdown(pdf_path: str) -> str:
    """Use pymupdf4llm to extract PDF content as Markdown."""
    try:
        import pymupdf4llm
    except ImportError:
        print("ERROR: pymupdf4llm not installed. Run: pip3 install pymupdf4llm", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    md = pymupdf4llm.to_markdown(pdf_path)
    return md


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


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Extract academic paper text as Markdown')
    parser.add_argument('input', help='PDF path, arXiv ID/URL, DOI, or remote PDF URL')
    parser.add_argument('--output', '-o', help='Output file path (default: stdout)')
    parser.add_argument('--metadata', action='store_true', help='Also print metadata as JSON header')
    args = parser.parse_args()

    raw_input = args.input.strip()
    tmp_pdf = None  # track temp files for cleanup

    try:
        # 1) Determine source type and get local PDF path
        arxiv_url = resolve_arxiv_url(raw_input)
        doi_url = resolve_doi_url(raw_input)

        if os.path.isfile(raw_input):
            pdf_path = os.path.abspath(raw_input)
            source_type = 'local'
        elif arxiv_url:
            print(f"📥 Downloading from arXiv: {arxiv_url}", file=sys.stderr)
            pdf_path = download_pdf(arxiv_url)
            tmp_pdf = pdf_path
            source_type = 'arxiv'
        elif doi_url:
            print(f"📥 Resolving DOI: {doi_url}", file=sys.stderr)
            pdf_path = download_pdf(doi_url)
            tmp_pdf = pdf_path
            source_type = 'doi'
        elif raw_input.startswith(('http://', 'https://')):
            print(f"📥 Downloading PDF: {raw_input}", file=sys.stderr)
            pdf_path = download_pdf(raw_input)
            tmp_pdf = pdf_path
            source_type = 'url'
        else:
            # Try as local path
            if os.path.isfile(raw_input):
                pdf_path = os.path.abspath(raw_input)
                source_type = 'local'
            else:
                print(f"ERROR: Cannot resolve input '{raw_input}' as file, arXiv ID, DOI, or URL.", file=sys.stderr)
                sys.exit(1)

        # 2) Extract
        print(f"📄 Extracting text from PDF ({source_type})...", file=sys.stderr)
        md_text = extract_pdf_to_markdown(pdf_path)

        # 3) Metadata
        meta = extract_metadata(pdf_path)

        # 4) Output
        output_parts = []
        if args.metadata and meta:
            output_parts.append(f"<!-- METADATA: {json.dumps(meta, ensure_ascii=False)} -->")
        output_parts.append(md_text)

        result = '\n'.join(output_parts)

        if args.output:
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"✅ Extracted to: {args.output}", file=sys.stderr)
        else:
            print(result)

    finally:
        if tmp_pdf and os.path.exists(tmp_pdf):
            os.unlink(tmp_pdf)


if __name__ == '__main__':
    main()
