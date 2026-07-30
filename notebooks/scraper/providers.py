import os
import re
import time
import csv
import requests
from urllib.parse import urlparse
from typing import Optional, List

from .models import DocumentInfo, SectionInfo, ImageInfo, TableInfo
from .fetchers import (
    doi_to_pmcid, 
    doi_to_arxiv_id, 
    is_arxiv_identifier,
    fetch_pmc_xml, 
    extract_images_from_oa, 
    fetch_real_html_pmc, 
    fetch_ar5iv_html,
    download_arxiv_source, 
    unpack_archive, 
    download_binary,
    SESSION, HEADERS
)
from .parsers_pmc import (
    parse_pmc_article_to_markdown, 
    extract_pmc_authors_emails,
    extract_pmc_image_urls_from_rendered_html
)
from .parsers_arxiv import (
    html_to_markdown_arxiv, 
    collect_authors_and_emails
)
from .parsers_md import (
    parse_markdown, 
    clean_markdown, 
    parse_md_table
)

def safe_filename(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-\.]+", "_", name).strip("_") or "document"


def save_text(text: str, path: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def process_sections_and_tables(doc: DocumentInfo, md_text: str, base_dir: str, local_images: List[str]):
    """
    Parses markdown, extracts sections, saves each section to separate markdown file,
    handles tables and images.
    """
    title, sections = parse_markdown(md_text)
    
    doc_id = safe_filename(doc.paper_id)
    tables_dir = os.path.join(base_dir, "tables", doc_id)
    sections_dir = os.path.join(base_dir, "md", doc_id, "sections")
    os.makedirs(sections_dir, exist_ok=True)
    
    global_table_counter = 0

    for sec_idx, sec in enumerate(sections):
        section_info = SectionInfo(heading=sec.get("heading", ""))
        
        # Build section markdown content lines
        section_md_lines = [f"## {sec['heading']}", ""]
        
        # Process tables
        for table_idx, table_md in enumerate(sec.get("tables", [])):
            parsed = parse_md_table(table_md)
            if parsed:
                header, rows = parsed
                os.makedirs(tables_dir, exist_ok=True)
                table_filename = f"table_{global_table_counter}.csv"
                table_path = os.path.join(tables_dir, table_filename)
                
                with open(table_path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(header)
                    writer.writerows(rows)
                
                section_info.tables.append(TableInfo(
                    csv_path=os.path.relpath(table_path, base_dir),
                    table_index=table_idx,
                    global_index=global_table_counter
                ))
                global_table_counter += 1
                
                # Add table markdown to section content
                section_md_lines.append(table_md)
                section_md_lines.append("")

        # Process text and images
        text = sec.get("text", "")
        matches = re.findall(r'!\[(.*?)\]\((.*?)\)', text)
        for alt, ref in matches:
            if doc.source == "pmc" and ref.startswith("PMC_FIG_"):
                m = re.search(r"PMC_FIG_(\d+)", ref)
                if m:
                    idx = int(m.group(1))
                    path = local_images[idx] if idx < len(local_images) else ""
                    section_info.images.append(ImageInfo(
                        placeholder=ref,
                        caption=alt,
                        path=path
                    ))
            elif doc.source == "arxiv":
                # For arxiv, 'ref' usually holds the path we injected
                section_info.images.append(ImageInfo(
                    placeholder=ref,
                    caption=alt,
                    path=ref 
                ))
        
        # Add text content to section markdown
        section_md_lines.append(text)
        
        # Save section markdown to separate file with sanitized heading
        section_heading_sanitized = safe_filename(sec["heading"])
        section_filename = f"section_{sec_idx:03d}_{section_heading_sanitized}.md"
        section_md_path = os.path.join(sections_dir, section_filename)
        
        with open(section_md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(section_md_lines))
        
        section_info.md_path = os.path.relpath(section_md_path, base_dir)
        doc.sections.append(section_info)


def process_arxiv(doi: str, base_dir: str) -> Optional[DocumentInfo]:
    arxiv_id = doi_to_arxiv_id(doi)
    if not arxiv_id:
        return None

    print(f"[ARXIV] Processing {arxiv_id} from {doi}...")

    md_dir = os.path.join(base_dir, "md")
    html_dir = os.path.join(base_dir, "html")
    png_dir = os.path.join(base_dir, "png", arxiv_id)
    pdf_dir = os.path.join(base_dir, "pdf")
    
    os.makedirs(md_dir, exist_ok=True)
    os.makedirs(html_dir, exist_ok=True)
    os.makedirs(png_dir, exist_ok=True)
    os.makedirs(pdf_dir, exist_ok=True)

    html_path = os.path.join(html_dir, f"{arxiv_id}.html")
    md_path = os.path.join(md_dir, f"{arxiv_id}.md")
    
    doc = DocumentInfo(
        paper_id=arxiv_id,
        source="arxiv",
        arxiv_id=arxiv_id,
    )

    ar5iv_source = fetch_ar5iv_html(arxiv_id)
    if not ar5iv_source:
        return None
        
    save_text(ar5iv_source, html_path)
    doc.html_path = os.path.relpath(html_path, base_dir)

    md_text = html_to_markdown_arxiv(ar5iv_source)
    if not md_text:
        return None
        
    md_text = clean_markdown(md_text)

    # Extract authors and emails from Tex
    try:
        tex_bytes = download_arxiv_source(arxiv_id)
        files = unpack_archive(tex_bytes)
        authors, emails = collect_authors_and_emails(files)
        doc.authors = authors
        doc.emails = emails
    except Exception as e:
        print(f"[ARXIV TEX] Failed: {e}")
        
    # Process Arxiv images right before storing md
    local_images = []
    matches = re.findall(r'!\[(.*?)\]\((.*?)\)', md_text)
    updated_md_text = md_text
    for i, (alt, ref) in enumerate(matches):
        if ref.startswith("/"):
            url = "https://ar5iv.org" + ref
        else:
            url = ref
        
        # Extract filename from URL
        filename = os.path.basename(urlparse(url).path)
        if not filename or "." not in filename:
            filename = f"image_{i}.png"
        
        # Always use arxiv_id as subdirectory for consistency
        img_subdir = os.path.join(png_dir, arxiv_id)
        os.makedirs(img_subdir, exist_ok=True)
        path = os.path.join(img_subdir, filename)
        
        # Try to download if not already exists
        downloaded = False
        if not os.path.exists(path):
            try:
                print(f"[ARXIV IMG] Downloading {filename} from {url}")
                r = SESSION.get(url, headers=HEADERS, timeout=30)
                if r.status_code == 200:
                    with open(path, "wb") as f:
                        f.write(r.content)
                    downloaded = True
                    print(f"[ARXIV IMG] Successfully saved {filename}")
            except Exception as e:
                print(f"[ARXIV IMG] Failed to download {filename}: {e}")
        else:
            downloaded = True
        
        # Only store relative path if successfully downloaded
        if downloaded and os.path.exists(path):
            rel_path = os.path.relpath(path, base_dir)
            updated_md_text = updated_md_text.replace(ref, rel_path)
            local_images.append(rel_path)
        else:
            # Keep original URL as fallback
            local_images.append(url)

    if md_text != updated_md_text:
        md_text = updated_md_text

    save_text(md_text, md_path)
    doc.md_path = os.path.relpath(md_path, base_dir)

    process_sections_and_tables(doc, md_text, base_dir, local_images)
    
    pdf_path = os.path.join(pdf_dir, f"{arxiv_id}.pdf")
    if not os.path.exists(pdf_path):
        try:
            r = SESSION.get(f"https://arxiv.org/pdf/{arxiv_id}.pdf", headers=HEADERS, timeout=60)
            if r.status_code == 200:
                with open(pdf_path, "wb") as f:
                    f.write(r.content)
                doc.pdf_path = os.path.relpath(pdf_path, base_dir)
        except:
            pass

    return doc


def process_pmc(doi: str, base_dir: str) -> Optional[DocumentInfo]:
    pmcid = doi_to_pmcid(doi)
    if not pmcid:
        return None
        
    print(f"[PMC] Processing {pmcid} from {doi}...")

    md_dir = os.path.join(base_dir, "md")
    html_dir = os.path.join(base_dir, "html")
    png_dir = os.path.join(base_dir, "png")
    pdf_dir = os.path.join(base_dir, "pdf")
    
    os.makedirs(md_dir, exist_ok=True)
    os.makedirs(html_dir, exist_ok=True)
    os.makedirs(png_dir, exist_ok=True)
    os.makedirs(pdf_dir, exist_ok=True)
    
    doc = DocumentInfo(
        paper_id=pmcid,
        source="pmc",
        pmcid=pmcid,
    )
    
    xml = fetch_pmc_xml(pmcid)
    if not xml:
        return None
        
    md_text = parse_pmc_article_to_markdown(xml)
    if not md_text:
        return None
        
    md_text = clean_markdown(md_text)
    md_path = os.path.join(md_dir, f"{pmcid}.md")
    save_text(md_text, md_path)
    # Store relative path (relative to base_dir)
    doc.md_path = os.path.relpath(md_path, base_dir)
    
    authors, emails = extract_pmc_authors_emails(xml)
    doc.authors = authors
    doc.emails = emails
    
    oa_paths, oa_pdf_path = extract_images_from_oa(pmcid, png_dir, pdf_dir)
    html_path = os.path.join(html_dir, f"{pmcid}.html")
    
    if oa_paths is not None:
        save_text("HTML not fetched. OA API was used.", html_path)
        doc.html_path = os.path.relpath(html_path, base_dir)
        doc.pdf_path = os.path.relpath(oa_pdf_path, base_dir) if oa_pdf_path else None
        doc.extraction_method = "oa_api"
        # Convert all OA API paths to relative paths
        local_images = [os.path.relpath(path, base_dir) for path in oa_paths]
    else:
        html = fetch_real_html_pmc(pmcid)
        save_text(html, html_path)
        doc.html_path = os.path.relpath(html_path, base_dir)
        doc.extraction_method = "selenium"
        
        urls = extract_pmc_image_urls_from_rendered_html(html)
        doc_img_dir = os.path.join(png_dir, pmcid)
        os.makedirs(doc_img_dir, exist_ok=True)

        local_images = []
        for idx, url in enumerate(urls):
            try:
                filename = os.path.basename(urlparse(url).path)
                if not filename or "." not in filename:
                    filename = f"pmc_image_{idx}.png"

                local_path = os.path.join(doc_img_dir, filename)
                if not os.path.exists(local_path):
                    download_binary(url, local_path)

                rel_path = os.path.relpath(local_path, base_dir)
                local_images.append(rel_path)
                time.sleep(0.3)
            except Exception as e:
                print(f"[PMC IMG FAIL] {url} -> {e}")

    process_sections_and_tables(doc, md_text, base_dir, local_images)
    return doc


def process_document(doi: str, base_dir: str = "paper_pipeline_data") -> Optional[DocumentInfo]:
    if is_arxiv_identifier(doi) or doi_to_arxiv_id(doi):
        doc = process_arxiv(doi, base_dir)
        if doc:
            return doc
            
    doc = process_pmc(doi, base_dir)
    if doc:
        return doc
    
    print(f"[SKIP] Could not process {doi}: not recognized as arXiv or PMC document")
    return None
