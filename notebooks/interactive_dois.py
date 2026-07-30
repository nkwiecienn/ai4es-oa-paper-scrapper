import sys
import os
import time

# Add parent directory to path if needed to run directly
from scraper.providers import process_document
from scraper.exporters import export_documents

def main():
    print("="*60)
    print("Interactive DOI Processor (Minimal JSON format)")
    print("="*60)
    
    dois = []
    while True:
        doi = input("Enter DOI to process (or press Enter to finish): ").strip()
        if not doi:
            break
        dois.append(doi)
        
    if not dois:
        print("No DOIs entered. Exiting.")
        sys.exit(0)
        
    results = []
    print(f"\nProcessing {len(dois)} DOI(s)...")
    
    # Use absolute path to paper_pipeline_data (in notebooks folder)
    notebooks_dir = os.path.dirname(__file__)
    base_dir = os.path.join(notebooks_dir, "paper_pipeline_data")
    base_dir = os.path.abspath(base_dir)
    
    for doi in dois:
        print(f"\nProcessing: {doi}")
        try:
            res = process_document(doi, base_dir=base_dir)
            if res:
                results.append(res)
                print(f"  [+] Success")
            else:
                print(f"  [-] Failed (returned None)")
        except Exception as e:
            print(f"  [!] Error: {e}")

    if results:
        export_dir = os.path.join(base_dir, "exports")
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = int(time.time())
        output_filename = f"processed_export_{timestamp}.json"
        output_path = os.path.join(export_dir, output_filename)
        
        export_documents(results, output_path)
        print(f"\n✅ Exported {len(results)} document(s) to: {output_path}")
    else:
        print("\n❌ No documents were successfully processed.")

if __name__ == "__main__":
    main()
