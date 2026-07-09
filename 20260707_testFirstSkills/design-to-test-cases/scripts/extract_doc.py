#!/usr/bin/env python3
"""extract_doc.py - Token-efficient text extraction from design documents.

Standard library only (no pip install needed), except PDF which uses pypdf
if available. Intended to be run by an AI agent so that binary Office files
are never read directly and only the needed portion of a document is loaded
into context.

Supported formats:
  .docx           Word (structure = heading outline, extract = text/tables)
  .xlsx / .xlsm   Excel (structure = sheet list + dimensions, extract = one sheet as TSV)
  .pdf            PDF (structure = page count, extract = page range; needs pypdf)
  anything else   Treated as text (structure = headings/line count, extract = line range)
  .doc / .xls     NOT supported (legacy binary) - convert to .docx/.xlsx first.

Usage:
  python extract_doc.py structure FILE
  python extract_doc.py extract FILE [--sheet NAME] [--pages A-B] [--lines A-B]
                                     [--heading TEXT] [--max-chars N]

Examples:
  python extract_doc.py structure spec.docx
  python extract_doc.py extract spec.docx --heading "3.2 Login"
  python extract_doc.py extract screens.xlsx --sheet "MainMenu"
  python extract_doc.py extract api.pdf --pages 4-9
  python extract_doc.py extract notes.md --lines 120-260
"""
import argparse
import io
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKGREL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
HEAD_RE = re.compile(r"heading|見出し", re.IGNORECASE)
MD_HEAD_RE = re.compile(r"^(#{1,6})\s+\S")

DEFAULT_MAX_CHARS = 20000


def out(text, state):
    """Print with a global character budget so one call never floods context."""
    budget = state["max_chars"] - state["written"]
    if budget <= 0:
        return
    if len(text) > budget:
        text = text[:budget]
        state["truncated"] = True
    state["written"] += len(text)
    sys.stdout.write(text)


# ---------------------------------------------------------------- docx

def docx_styles(z):
    styles = {}
    try:
        root = ET.fromstring(z.read("word/styles.xml"))
    except KeyError:
        return styles
    for st in root.findall(f"{W}style"):
        sid = st.get(f"{W}styleId") or ""
        name_el = st.find(f"{W}name")
        styles[sid] = (name_el.get(f"{W}val") if name_el is not None else "") or ""
    return styles


def docx_heading_level(style_id, styles):
    """Return heading level (1..9) or None. Matches 'Heading 1' and '見出し 1'."""
    name = styles.get(style_id or "", "")
    if not (HEAD_RE.search(name) or HEAD_RE.search(style_id or "")):
        return None
    m = re.search(r"(\d+)", name) or re.search(r"(\d+)", style_id or "")
    return int(m.group(1)) if m else 1


def docx_blocks(z):
    """Yield ('p', style_id, text) or ('tbl', None, rows)."""
    root = ET.fromstring(z.read("word/document.xml"))
    body = root.find(f"{W}body")
    if body is None:
        return
    for el in body:
        if el.tag == f"{W}p":
            style = None
            ppr = el.find(f"{W}pPr")
            if ppr is not None:
                ps = ppr.find(f"{W}pStyle")
                if ps is not None:
                    style = ps.get(f"{W}val")
            text = "".join(t.text or "" for t in el.iter(f"{W}t"))
            yield ("p", style, text)
        elif el.tag == f"{W}tbl":
            rows = []
            for tr in el.findall(f"{W}tr"):
                rows.append(
                    [" ".join(t.text or "" for t in tc.iter(f"{W}t")).strip()
                     for tc in tr.findall(f"{W}tc")]
                )
            yield ("tbl", None, rows)


def docx_structure(path, state):
    with zipfile.ZipFile(path) as z:
        styles = docx_styles(z)
        n_para = n_tbl = 0
        headings = []
        for kind, style, payload in docx_blocks(z):
            if kind == "tbl":
                n_tbl += 1
                continue
            n_para += 1
            lvl = docx_heading_level(style, styles)
            if lvl and payload.strip():
                headings.append((lvl, payload.strip()))
    out(f"# DOCX structure: {path}\n", state)
    out(f"# paragraphs={n_para} tables={n_tbl} headings={len(headings)}\n", state)
    if not headings:
        out("# (no heading styles found - use plain `extract` and read sequentially)\n", state)
    for lvl, text in headings:
        out(f"{'  ' * (lvl - 1)}[H{lvl}] {text}\n", state)


def docx_extract(path, heading, state):
    with zipfile.ZipFile(path) as z:
        styles = docx_styles(z)
        emitting = heading is None
        stop_level = None
        matched = False
        for kind, style, payload in docx_blocks(z):
            if kind == "p":
                lvl = docx_heading_level(style, styles)
                if heading is not None and lvl:
                    if emitting and lvl <= stop_level:
                        break  # reached the next section of same/higher rank
                    if not emitting and heading.lower() in payload.lower():
                        emitting, matched, stop_level = True, True, lvl
                if emitting and payload.strip():
                    prefix = f"[H{lvl}] " if lvl else ""
                    out(prefix + payload.strip() + "\n", state)
            elif kind == "tbl" and emitting:
                out("--- table ---\n", state)
                for row in payload:
                    out("\t".join(row) + "\n", state)
                out("--- end table ---\n", state)
        if heading is not None and not matched:
            out(f"# heading not found: {heading!r} (run `structure` to list headings)\n", state)


# ---------------------------------------------------------------- xlsx

def tsv_escape(s):
    """Keep one sheet row on one physical TSV line even when a cell
    contains tabs or line breaks."""
    return s.replace("\t", "\\t").replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")


def col_to_index(ref):
    """'B3' -> 1 (0-based column index)."""
    idx = 0
    for ch in ref:
        if ch.isalpha():
            idx = idx * 26 + (ord(ch.upper()) - 64)
        else:
            break
    return idx - 1


def xlsx_sheets(z):
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rid2target = {r.get("Id"): r.get("Target") for r in rels.findall(f"{PKGREL}Relationship")}
    sheets = []
    sheets_el = wb.find(f"{S}sheets")
    if sheets_el is None:
        return sheets
    for sh in sheets_el:
        target = rid2target.get(sh.get(f"{RID}id"), "") or ""
        target = target.lstrip("/")
        if not target.startswith("xl/"):
            target = "xl/" + target
        sheets.append((sh.get("name"), target))
    return sheets


def xlsx_si_text(si):
    """Text of a shared/inline string, excluding phonetic (furigana) runs <rPh>
    that Japanese workbooks store alongside the visible text."""
    parts = []
    t = si.find(f"{S}t")
    if t is not None:
        parts.append(t.text or "")
    for r in si.findall(f"{S}r"):
        rt = r.find(f"{S}t")
        if rt is not None:
            parts.append(rt.text or "")
    return "".join(parts)


def xlsx_shared_strings(z):
    try:
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return [xlsx_si_text(si) for si in root.findall(f"{S}si")]


def xlsx_cell_value(c, shared):
    t = c.get("t")
    if t == "inlineStr":
        is_el = c.find(f"{S}is")
        return xlsx_si_text(is_el) if is_el is not None else ""
    v = c.find(f"{S}v")
    if v is None or v.text is None:
        return ""
    if t == "s":
        try:
            return shared[int(v.text)]
        except (ValueError, IndexError):
            return v.text
    if t == "b":
        return "TRUE" if v.text == "1" else "FALSE"
    return v.text


def xlsx_structure(path, state):
    out(f"# XLSX structure: {path}\n", state)
    with zipfile.ZipFile(path) as z:
        for name, target in xlsx_sheets(z):
            dim = "?"
            try:
                root = ET.fromstring(z.read(target))
                dim_el = root.find(f"{S}dimension")
                if dim_el is not None:
                    dim = dim_el.get("ref") or "?"
                else:
                    rows = root.find(f"{S}sheetData")
                    dim = f"~{len(rows)} rows" if rows is not None else "empty"
            except KeyError:
                dim = "missing"
            out(f"sheet: {name}\trange: {dim}\n", state)
    out("# Next: extract one sheet at a time with --sheet NAME\n", state)


def xlsx_extract(path, sheet_name, state):
    with zipfile.ZipFile(path) as z:
        sheets = dict(xlsx_sheets(z))
        if sheet_name not in sheets:
            out(f"# sheet not found: {sheet_name!r}. Sheets: {', '.join(sheets)}\n", state)
            return
        shared = xlsx_shared_strings(z)
        root = ET.fromstring(z.read(sheets[sheet_name]))
        data = root.find(f"{S}sheetData")
        if data is None:
            out("# empty sheet\n", state)
            return
        out(f"# sheet {sheet_name!r} as TSV (row number first)\n", state)
        for row in data.findall(f"{S}row"):
            cells = {}
            for c in row.findall(f"{S}c"):
                val = xlsx_cell_value(c, shared)
                if val != "":
                    cells[col_to_index(c.get("r") or "A1")] = tsv_escape(val)
            if not cells:
                continue
            width = max(cells) + 1
            line = "\t".join(cells.get(i, "") for i in range(width))
            out(f"{row.get('r')}\t{line}\n", state)


# ---------------------------------------------------------------- pdf

def pdf_reader(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader  # noqa: N811
        except ImportError:
            sys.exit(
                "pypdf is not installed. Either run `pip install pypdf`, "
                "or read the PDF with your agent's native PDF reading using "
                "small page ranges instead of this script."
            )
    return PdfReader(path)


def pdf_structure(path, state):
    reader = pdf_reader(path)
    out(f"# PDF structure: {path}\n# pages={len(reader.pages)}\n", state)
    try:
        outline = reader.outline
    except Exception:
        outline = None
    if outline:
        def walk(items, depth):
            for it in items:
                if isinstance(it, list):
                    walk(it, depth + 1)
                else:
                    title = getattr(it, "title", None)
                    if title:
                        out(f"{'  ' * depth}{title}\n", state)
        out("# bookmarks:\n", state)
        walk(outline, 0)
    else:
        out("# (no bookmarks - extract with --pages in small ranges, e.g. 1-5)\n", state)


def pdf_extract(path, pages, state):
    reader = pdf_reader(path)
    n = len(reader.pages)
    first, last = pages if pages else (1, min(n, 5))
    first, last = max(1, first), min(n, last)
    for i in range(first, last + 1):
        out(f"--- page {i}/{n} ---\n", state)
        out((reader.pages[i - 1].extract_text() or "").strip() + "\n", state)


# ---------------------------------------------------------------- text

def read_text(path):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def text_structure(path, state):
    lines = read_text(path).splitlines()
    out(f"# TEXT structure: {path}\n# lines={len(lines)}\n", state)
    heads = [(i + 1, ln.strip()) for i, ln in enumerate(lines) if MD_HEAD_RE.match(ln)]
    if heads:
        for lineno, text in heads:
            out(f"L{lineno}: {text}\n", state)
    else:
        out("# (no markdown headings - first 30 lines shown)\n", state)
        for i, ln in enumerate(lines[:30]):
            out(f"L{i + 1}: {ln}\n", state)
    out("# Next: extract with --lines A-B\n", state)


def text_extract(path, lines_range, state):
    lines = read_text(path).splitlines()
    first, last = lines_range if lines_range else (1, min(len(lines), 200))
    for i in range(max(1, first), min(len(lines), last) + 1):
        out(f"{lines[i - 1]}\n", state)


# ---------------------------------------------------------------- main

def parse_range(text):
    m = re.fullmatch(r"(\d+)(?:-(\d+))?", text.strip())
    if not m:
        raise argparse.ArgumentTypeError("range must look like 3 or 4-9")
    a = int(m.group(1))
    return (a, int(m.group(2)) if m.group(2) else a)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["structure", "extract"])
    ap.add_argument("file")
    ap.add_argument("--sheet", help="xlsx: worksheet name")
    ap.add_argument("--pages", type=parse_range, help="pdf: page range, e.g. 4-9")
    ap.add_argument("--lines", type=parse_range, help="text: line range, e.g. 100-200")
    ap.add_argument("--heading", help="docx: extract the section under this heading text")
    ap.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS)
    args = ap.parse_args()

    state = {"max_chars": args.max_chars, "written": 0, "truncated": False}
    ext = args.file.lower().rsplit(".", 1)[-1] if "." in args.file else ""

    if ext in ("doc", "xls", "ppt"):
        sys.exit(f".{ext} is a legacy binary format. Ask the user to convert it "
                 f"to .{ext}x (e.g. save-as in Office or LibreOffice) first.")

    if ext == "docx":
        docx_structure(args.file, state) if args.mode == "structure" else docx_extract(args.file, args.heading, state)
    elif ext in ("xlsx", "xlsm"):
        if args.mode == "structure":
            xlsx_structure(args.file, state)
        elif not args.sheet:
            sys.exit("extract on xlsx requires --sheet NAME (run `structure` first to list sheets)")
        else:
            xlsx_extract(args.file, args.sheet, state)
    elif ext == "pdf":
        pdf_structure(args.file, state) if args.mode == "structure" else pdf_extract(args.file, args.pages, state)
    else:
        text_structure(args.file, state) if args.mode == "structure" else text_extract(args.file, args.lines, state)

    if state["truncated"]:
        sys.stdout.write(
            "\n# OUTPUT TRUNCATED at --max-chars. Narrow the request "
            "(--sheet / --pages / --lines / --heading) or raise --max-chars.\n"
        )


if __name__ == "__main__":
    main()
