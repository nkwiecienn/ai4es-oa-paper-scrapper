import re
import os
import io
import gzip
import tarfile
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def normalize(text):
    return re.sub(r"\s+", " ", text or "").strip()

def parse_html_table(table):
    rows = []

    for tr in table.find_all("tr"):
        cols = tr.find_all(["td", "th"])
        row = [normalize(c.get_text(" ", strip=True)) for c in cols]
        if row:
            rows.append(row)

    if not rows:
        return ""

    md = []
    md.append("| " + " | ".join(rows[0]) + " |")
    md.append("| " + " | ".join("---" for _ in rows[0]) + " |")

    for r in rows[1:]:
        if len(r) < len(rows[0]):
            r += [""] * (len(rows[0]) - len(r))
        elif len(r) > len(rows[0]):
            r = r[:len(rows[0])]
        md.append("| " + " | ".join(r) + " |")

    return "\n".join(md)

def parse_html_figure(fig):
    img = fig.find("img")
    caption = fig.find("figcaption")

    src = ""
    if img and img.has_attr("src"):
        src = img["src"]
        if src.startswith("/"):
            src = "https://ar5iv.org" + src

    cap = caption.get_text(" ", strip=True) if caption else ""
    return f"\n![{cap}]({src})\n"

def html_to_markdown_arxiv(html):
    soup = BeautifulSoup(html, "html.parser")
    article = soup.find("article")

    if not article:
        return None

    md = []

    for tag in article.find_all([
        "h1", "h2", "h3",
        "p", "li", "pre",
        "figure", "table"
    ]):
        text = normalize(tag.get_text(" ", strip=True))

        if tag.name == "h1":
            md.append(f"# {text}")
        elif tag.name == "h2":
            md.append(f"\n## {text}")
        elif tag.name == "h3":
            md.append(f"\n### {text}")
        elif tag.name == "p":
            if text:
                md.append(text)
        elif tag.name == "li":
            md.append(f"- {text}")
        elif tag.name == "pre":
            md.append(f"\n```\n{text}\n```")
        elif tag.name == "figure":
            md.append(parse_html_figure(tag))
        elif tag.name == "table":
            table_md = parse_html_table(tag)
            if table_md:
                md.append("\n" + table_md + "\n")

    return "\n\n".join(md)

# =========================================================
# ARXIV AUTHORS / EMAILS FROM TEX
# =========================================================

def extract_balanced_blocks(text, command):
    results = []
    pattern = re.compile(rf"\\{re.escape(command)}\s*\{{")

    for match in pattern.finditer(text):
        brace_start = match.end() - 1
        depth = 0
        end = None

        for i in range(brace_start, len(text)):
            char = text[i]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break

        if end is not None:
            results.append(text[brace_start + 1:end])

    return results

def find_author_files(files):
    author_files = {}

    for filename, tex in files.items():
        blocks = extract_balanced_blocks(tex, "author")
        if blocks:
            author_files[filename] = blocks

    return author_files

def normalize_author_name(name):
    name = name.strip()
    name = re.sub(r"^(?:AND|And|and)\s+", "", name)
    name = re.sub(r"(?<=[A-Za-z])\s*\d{4}-\d{4}-\d{4}-\d{3,4}[0-9X]\b", "", name)
    name = re.sub(r"\b\d{4}-\d{4}-\d{4}-\d{3,4}[0-9X]\b", "", name)
    name = re.sub(r"\s*\.\s*mm\s*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s+mm\s*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"[^A-Za-z.\-'\s]", " ", name)
    name = re.sub(r"(?:\s*-\s*){2,}X?\s*$", "", name)
    name = re.sub(r"-{2,}X?\s*$", "", name)
    name = re.sub(r"(?:\s*-\s*)+X\s*$", "", name)
    name = re.sub(r"\s*-\s*$", "", name)
    name = re.sub(r"[-–—\s]+$", "", name)
    name = re.sub(r"\s+", " ", name).strip(" ,;")
    return name

def looks_like_person_name(line):
    line = line.strip(" ,;")
    if not line or "@" in line:
        return False

    low = line.lower()

    bad_keywords = [
        "university", "department", "institute", "school", "centre", "center",
        "lab", "labs", "laboratory", "faculty", "college",
        "research", "brain", "google", "openai", "meta", "microsoft",
        "amazon", "deepmind", "anthropic", "nvidia",
        "economics", "business", "law",
        "corresponding author", "email", "orcid", "https", "http"
    ]
    if any(k in low for k in bad_keywords):
        return False

    words = line.split()
    if len(words) < 2 or len(words) > 6:
        return False

    valid_words = 0
    for word in words:
        cleaned = re.sub(r"[^A-Za-z.\-']", "", word)
        if not cleaned:
            continue
        if cleaned[0].isupper():
            valid_words += 1

    if valid_words < 2:
        return False

    if len(line) > 60:
        return False

    return True

def clean_single_author_block(block):
    text = block.replace("\r", "\n")

    text = text.replace("\\\\", "\n")
    text = re.sub(r"\\and\b|\\And\b|\\AND\b", "\n", text)
    text = re.sub(r"\\quad\b|\\qquad\b", "\n", text)
    text = re.sub(r"\s+\band\b\s+", "\n", text, flags=re.IGNORECASE)

    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\\thanks\s*\{([^{}]|\{[^{}]*\})*\}", "", text)

    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\\footnote\s*\{([^{}]|\{[^{}]*\})*\}", "", text)

    text = re.sub(r"\$\^\{[^$]*\}\$", "", text)
    text = re.sub(r"\$[^$]*\$", "", text)

    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"\\[A-Za-z*]+\s*\{([^{}]*)\}", r"\1", text)

    text = re.sub(r"\\[A-Za-z*]+", " ", text)
    text = text.replace("{", "").replace("}", "")

    raw_lines = []
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip(" ,;")
        if line:
            raw_lines.append(line)

    candidates = []

    for line in raw_lines:
        comma_parts = [p.strip() for p in re.split(r"\s*,\s*", line) if p.strip()]
        normalized_parts = [normalize_author_name(p) for p in comma_parts]

        if len(comma_parts) > 1 and all(looks_like_person_name(p) for p in normalized_parts):
            candidates.extend(normalized_parts)
        else:
            candidates.append(normalize_author_name(line))

    authors = []
    seen = set()

    for cand in candidates:
        cand = normalize_author_name(cand)
        if looks_like_person_name(cand):
            key = cand.lower()
            if key not in seen:
                seen.add(key)
                authors.append(cand)

    return authors

def extract_emails_from_text(tex):
    emails = []

    grouped = re.findall(r"\{([^{}]+)\}\\?@([A-Za-z0-9.\-]+\.[A-Za-z]{2,})", tex)
    for users, domain in grouped:
        for user in users.split(","):
            user = user.strip().strip("\\")
            if user:
                emails.append(f"{user}@{domain}")

    normal = re.findall(
        r"[A-Za-z0-9._%+\-]+\\?@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}",
        tex,
    )
    emails.extend(normal)

    cleaned = []
    seen = set()
    for email in emails:
        email = email.replace("\\@", "@").strip(".,;:()[]{}<> ")
        key = email.lower()
        if key and key not in seen:
            seen.add(key)
            cleaned.append(email)

    return cleaned

def collect_authors_and_emails(files):
    author_files = find_author_files(files)
    if not author_files:
        return [], []

    all_authors = []
    all_emails = []

    for filename, author_blocks in author_files.items():
        for block in author_blocks:
            authors = clean_single_author_block(block)
            all_authors.extend(authors)

        all_emails.extend(extract_emails_from_text(files[filename]))

    dedup_authors = []
    seen_authors = set()
    for author in all_authors:
        key = re.sub(r"\s+", " ", author.strip().lower())
        if key and key not in seen_authors:
            seen_authors.add(key)
            dedup_authors.append(author.strip())

    dedup_emails = []
    seen_emails = set()
    for email in all_emails:
        key = email.lower().strip()
        if key and key not in seen_emails:
            seen_emails.add(key)
            dedup_emails.append(email.strip())

    return dedup_authors, dedup_emails
