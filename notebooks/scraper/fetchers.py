import os
import io
import re
import time
import requests
import tarfile
import gzip
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from typing import Tuple, List, Optional, Dict

SESSION = requests.Session()
HEADERS = {"User-Agent": "Mozilla/5.0"}
MAX_HTTP_RETRIES = 5

def download_binary(url: str, path: str):
    r = SESSION.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()

    with open(path, "wb") as f:
        f.write(r.content)

def unpack_archive(content: bytes) -> Dict[str, str]:
    files = {}

    try:
        with tarfile.open(fileobj=io.BytesIO(content), mode="r:*") as tar:
            for member in tar.getmembers():
                if member.isfile() and member.name.lower().endswith(".tex"):
                    extracted = tar.extractfile(member)
                    if extracted is None:
                        continue
                    files[member.name] = extracted.read().decode("utf-8", errors="ignore")
        if files:
            return files
    except tarfile.ReadError:
        pass

    try:
        text = gzip.decompress(content).decode("utf-8", errors="ignore")
        return {"main.tex": text}
    except Exception:
        return {}

def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver

def is_arxiv_identifier(doi: str) -> bool:
    doi_lower = doi.lower()
    if "arxiv" in doi_lower:
        return True
    if re.match(r"^([a-z\-]+(\.[a-z]{2})?/)?\d{4}\.\d{4,5}(v\d+)?$", doi_lower):
        return True
    return False

def doi_to_arxiv_id(doi: str) -> Optional[str]:
    m = re.search(r"(\d{4}\.\d{4,5}(v\d+)?)", doi.lower())
    if m:
        return m.group(1)
    
    m = re.search(r"([a-z\-]+(?:\.[a-z]{2})?/\d{7}(v\d+)?)", doi.lower())
    if m:
        return m.group(1)
        
    return None

def fetch_real_html_pmc(pmcid: str) -> str:
    driver = get_driver()
    url = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"

    print(f"Opening browser for {pmcid} (Selenium Fallback)...")
    driver.get(url)

    print("Waiting for rendered content / anti-bot redirect...")
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//article | //div[contains(@class, 'article')] | //div[@id='mc']"))
        )
        time.sleep(2)
    except Exception as e:
        print(f"[Selenium] Timeout waiting for {pmcid}: {e}")

    html = driver.page_source
    driver.quit()
    return html

def doi_to_pmcid(doi: str) -> Optional[str]:
    url = "https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/"
    params = {"ids": doi, "format": "json"}

    for _ in range(MAX_HTTP_RETRIES):
        try:
            r = SESSION.get(url, params=params, headers=HEADERS, timeout=30)
            data = r.json()
            if data.get("records"):
                return data["records"][0].get("pmcid")
        except Exception:
            pass
        time.sleep(1)

    return None

def fetch_pmc_xml(pmcid: str) -> Optional[str]:
    pmc_num = pmcid[3:]

    url = "https://pmc.ncbi.nlm.nih.gov/api/oai/v1/mh/"
    params = {
        "verb": "GetRecord",
        "identifier": f"oai:pubmedcentral.nih.gov:{pmc_num}",
        "metadataPrefix": "pmc",
    }

    for _ in range(MAX_HTTP_RETRIES):
        try:
            r = SESSION.get(url, params=params, headers=HEADERS, timeout=60)
            if r.status_code == 200:
                return r.text
        except Exception:
            pass
        time.sleep(1)

    return None

def extract_images_from_oa(pmcid: str, png_dir: str, pdf_dir: str) -> Tuple[Optional[List[str]], Optional[str]]:
    try:
        r = requests.get('https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi', params={"id": pmcid})
        if r.status_code != 200:
            return None, None
            
        root = ET.fromstring(r.text)
        tgz = root.find(".//{*}link[@format='tgz']")
        
        if tgz is None:
            return None, None
            
        href = tgz.attrib.get("href")
        link = f'https{href[3:]}'

        r = requests.get(link, stream=True)

        if r.status_code != 200:
            link = link.replace('https://ftp.ncbi.nlm.nih.gov/pub/pmc/', 'https://ftp.ncbi.nlm.nih.gov/pub/pmc/deprecated/')
            r = requests.get(link, stream=True)

        if r.status_code != 200:
            print(f"[OA API] Failed to download package for {pmcid}: {r.status_code}")
            return None, None
        
        doc_img_dir = os.path.join(png_dir, pmcid)
        os.makedirs(doc_img_dir, exist_ok=True)
        local_paths = []
        pdf_path = None

        with tarfile.open(fileobj=io.BytesIO(r.content), mode="r:gz") as tar:
            for member in tar.getmembers():
                if member.isfile():
                    if re.search(r"\.(jpg|jpeg|png|gif|tif|tiff|webp)$", member.name, re.I):
                        f = tar.extractfile(member)
                        if f:
                            filename = os.path.basename(member.name)
                            local_path = os.path.join(doc_img_dir, filename)
                            with open(local_path, "wb") as out_f:
                                out_f.write(f.read())
                            local_paths.append(local_path)
                    elif re.search(r"\.pdf$", member.name, re.I):
                        f = tar.extractfile(member)
                        if f:
                            os.makedirs(pdf_dir, exist_ok=True)
                            pdf_path = os.path.join(pdf_dir, f"{pmcid}.pdf")
                            with open(pdf_path, "wb") as out_f:
                                out_f.write(f.read())

        return local_paths, pdf_path
    except Exception as e:
        print(f"[OA API] Exception for {pmcid}: {e}")
        return None, None

def fetch_ar5iv_html(arxiv_id: str) -> Optional[str]:
    url = f"https://ar5iv.org/html/{arxiv_id}"

    for _ in range(MAX_HTTP_RETRIES):
        try:
            r = SESSION.get(url, headers=HEADERS, timeout=60)
            if r.status_code == 200:
                return r.text
        except Exception:
            pass
        time.sleep(1)

    return None

def download_arxiv_source(arxiv_id: str) -> bytes:
    url = f"https://arxiv.org/e-print/{arxiv_id}"
    r = SESSION.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.content

def download_single_image(url: str, doc_id: str, idx: int, png_dir: str) -> Optional[str]:
    if url.startswith("/"):
        url = "https://ar5iv.org" + url

    img_dir = os.path.join(png_dir, doc_id)
    os.makedirs(img_dir, exist_ok=True)

    try:
        r = SESSION.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            ctype = r.headers.get("Content-Type", "")
            ext = ".png"
            if "jpeg" in ctype:
                ext = ".jpg"
            elif "gif" in ctype:
                ext = ".gif"
            elif "svg" in ctype:
                ext = ".svg"
            
            p = urlparse(url).path
            orig_ext = os.path.splitext(p)[1]
            if orig_ext:
                ext = orig_ext
            
            out_path = os.path.join(img_dir, f"image_{idx}{ext}")
            with open(out_path, "wb") as f:
                f.write(r.content)
            return out_path
    except Exception:
        pass
    return None
