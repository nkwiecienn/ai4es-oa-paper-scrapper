import os
import sys
import argparse
import time
from scraper.providers import process_document
from scraper.exporters import export_documents, compress_directory

def main():
    parser = argparse.ArgumentParser(description="Batch process DOIs to JSON")
    parser.add_argument("dois_file", help="Path to the .txt file containing DOIs")
    parser.add_argument("--compress", action="store_true", help="Compress paper_pipeline_data directory to ZIP after processing")
    args = parser.parse_args()

    if not os.path.exists(args.dois_file):
        print(f"Error: File {args.dois_file} not found.")
        sys.exit(1)

    dois = []
    with open(args.dois_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                dois.append(line)

    # Use absolute path to paper_pipeline_data (in notebooks folder)
    notebooks_dir = os.path.dirname(__file__)
    base_dir = os.path.join(notebooks_dir, "paper_pipeline_data")
    base_dir = os.path.abspath(base_dir)
    
    results = []
    total_dois = len(dois)
    for idx, do in enumerate(dois, 1):
        print(f"[{idx}/{total_dois}] Processing {do}...")
        try:
            res = process_document(do, base_dir=base_dir)
            if res:
                results.append(res)
        except Exception as e:
            print(f"Error processing {do}: {e}")

    export_dir = os.path.join(base_dir, "exports")
    os.makedirs(export_dir, exist_ok=True)
    
    timestamp = int(time.time())
    output_filename = f"processed_export_{timestamp}.json"
    output_path = os.path.join(export_dir, output_filename)
    
    export_documents(results, output_path)
    print(f"Exported to {output_path}")
    
    # Optionally compress the entire paper_pipeline_data directory
    if args.compress:
        print("\nCompressing paper_pipeline_data directory...")
        zip_filename = f"processed_export_{timestamp}"
        # Save zip file outside paper_pipeline_data to avoid recursive compression
        zip_output_dir = notebooks_dir  # Save in notebooks folder instead
        compress_directory(base_dir, zip_output_dir, zip_filename)
    else:
        print("\nSkipping compression (use --compress flag to enable)")

if __name__ == "__main__":
    main()
