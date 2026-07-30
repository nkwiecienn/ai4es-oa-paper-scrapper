import re

def normalize(text):
    return re.sub(r"\s+", " ", text or "").strip()

def parse_md_table(text):
    lines = [l.strip() for l in text.split("\n") if l.strip().startswith("|")]

    if len(lines) < 2:
        return None

    def split_row(line):
        cells = [x.strip() for x in line.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        return cells

    rows_raw = [split_row(line) for line in lines]

    header = rows_raw[0]
    max_width = len(header)

    data = []
    for r in rows_raw[1:]:
        if all(re.fullmatch(r"-+", cell or "") for cell in r):
            continue

        if len(r) < max_width:
            r += [""] * (max_width - len(r))
        elif len(r) > max_width:
            r = r[:max_width]

        data.append(r)

    return header, data

def parse_markdown(md_text):
    title = ""
    sections = []
    current = None
    current_table = []
    recent_lines = []

    def flush_table():
        nonlocal current_table, current

        if current and current_table:
            idx = len(current["tables"])
            current["tables"].append("\n".join(current_table))
            current["text"] += f" [[TABLE_{idx}]] "
            current_table.clear()

    for line in md_text.split("\n"):
        stripped = line.strip()

        if not stripped:
            flush_table()
            continue

        if stripped.startswith("# ") and not title:
            title = normalize(stripped[2:])
            recent_lines.append(line)
            continue

        if re.match(r"^##+\s+", stripped):
            flush_table()
            if current:
                sections.append(current)

            heading = re.sub(r"^##+\s*", "", stripped)

            if heading.lower() in ["authors", "emails"]:
                current = None
                continue

            current = {"heading": heading, "text": "", "tables": []}
            recent_lines.append(line)
            continue

        if stripped.startswith("|"):
            current_table.append(stripped)
            continue

        flush_table()

        if current:
            current["text"] += " " + line

        recent_lines.append(line)
        if len(recent_lines) > 10:
            recent_lines.pop(0)

    flush_table()

    if current:
        sections.append(current)

    return title, sections

def clean_sections(sections):
    return [s for s in sections if len(normalize(s["text"])) > 5 or s["tables"]]

def clean_markdown(md_text):
    lines = md_text.split("\n")

    cleaned = []
    current_section = None
    current_content = []
    seen_sections = set()

    def flush():
        nonlocal current_section, current_content

        if current_section:
            content = "\n".join(current_content).strip()
            if content:
                key = normalize(current_section.lower() + content[:200])
                if key not in seen_sections:
                    seen_sections.add(key)
                    cleaned.append(current_section)
                    cleaned.append(content)
                    cleaned.append("")

        current_section = None
        current_content = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("## "):
            flush()
            current_section = stripped
        else:
            if current_section:
                current_content.append(line)
            else:
                cleaned.append(line)

    flush()
    return "\n".join(cleaned)
