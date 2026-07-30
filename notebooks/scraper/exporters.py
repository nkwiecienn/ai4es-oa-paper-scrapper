import os
import json
import zipfile
from pathlib import Path
from typing import List
from .models import DocumentInfo

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

def export_documents(docs: List[DocumentInfo], output_path: str):
    """
    Exports a list of DocumentInfo models to a single JSON file.
    
    Args:
        docs: List of DocumentInfo objects to export
        output_path: Full file path for the output JSON (e.g., "exports/processed_export_123456.json")
    """
    # Ensure the directory exists
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    
    data = [doc.to_dict() for doc in docs]
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"[EXPORT] Successfully saved {len(docs)} documents to {output_path}")


def compress_directory(directory_path: str, output_dir: str, archive_name: str) -> str:
    """
    Compresses an entire directory into a ZIP archive with optional progress bar.
    
    Args:
        directory_path: Full path to the directory to compress
        output_dir: Directory where the ZIP file will be saved
        archive_name: Base name for the archive (without .zip extension)
    
    Returns:
        Full path to the created ZIP file
    """
    os.makedirs(output_dir, exist_ok=True)
    
    archive_path = os.path.join(output_dir, f"{archive_name}.zip")
    
    # Collect all files to compress first (for progress bar)
    files_to_compress = []
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, directory_path)
            files_to_compress.append((file_path, arcname))
    
    # Create ZIP archive with progress bar if tqdm is available
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        if TQDM_AVAILABLE:
            for file_path, arcname in tqdm(files_to_compress, desc="Compressing", unit="file"):
                zipf.write(file_path, arcname=arcname)
        else:
            for file_path, arcname in files_to_compress:
                zipf.write(file_path, arcname=arcname)
            print(f"[COMPRESS] Processing {len(files_to_compress)} files...")
    
    print(f"[COMPRESS] Successfully compressed {directory_path} to {archive_path}")
    return archive_path
