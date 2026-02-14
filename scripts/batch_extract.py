#!/usr/bin/env python3
"""
Batch extract multiple papers from a directory of PDFs.

Usage:
  python3 batch_extract.py <input_dir> [--output-dir <dir>]

Processes all .pdf files in <input_dir> and outputs individual .md files.
"""

import os
import sys
import glob
import subprocess


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Batch extract PDFs to Markdown')
    parser.add_argument('input_dir', help='Directory containing PDF files')
    parser.add_argument('--output-dir', '-o', default=None,
                        help='Output directory (default: <input_dir>/extracted)')
    args = parser.parse_args()

    input_dir = os.path.abspath(args.input_dir)
    if not os.path.isdir(input_dir):
        print(f"ERROR: {input_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    output_dir = args.output_dir or os.path.join(input_dir, 'extracted')
    os.makedirs(output_dir, exist_ok=True)

    pdfs = sorted(glob.glob(os.path.join(input_dir, '*.pdf')))
    if not pdfs:
        print(f"No PDF files found in {input_dir}", file=sys.stderr)
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    extract_script = os.path.join(script_dir, 'extract_paper.py')

    print(f"Found {len(pdfs)} PDF(s) in {input_dir}")
    results = []

    for i, pdf in enumerate(pdfs, 1):
        name = os.path.splitext(os.path.basename(pdf))[0]
        out_file = os.path.join(output_dir, f"{name}.md")
        print(f"\n[{i}/{len(pdfs)}] Processing: {os.path.basename(pdf)}")

        try:
            result = subprocess.run(
                [sys.executable, extract_script, pdf, '--output', out_file, '--metadata'],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                print(f"  ✅ → {out_file}")
                results.append({'file': os.path.basename(pdf), 'output': out_file, 'status': 'ok'})
            else:
                print(f"  ❌ Error: {result.stderr.strip()}")
                results.append({'file': os.path.basename(pdf), 'status': 'error', 'error': result.stderr.strip()})
        except subprocess.TimeoutExpired:
            print(f"  ⏰ Timeout processing {os.path.basename(pdf)}")
            results.append({'file': os.path.basename(pdf), 'status': 'timeout'})

    # Summary
    ok = sum(1 for r in results if r['status'] == 'ok')
    print(f"\n{'='*40}")
    print(f"Done: {ok}/{len(pdfs)} papers extracted successfully")
    print(f"Output directory: {output_dir}")

    # Write manifest
    import json
    manifest_path = os.path.join(output_dir, '_manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Manifest: {manifest_path}")


if __name__ == '__main__':
    main()
