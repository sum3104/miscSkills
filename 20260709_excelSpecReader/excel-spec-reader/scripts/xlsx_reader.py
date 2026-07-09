#!/usr/bin/env python3
"""xlsx_reader.py - Token-efficient reader for Excel spec workbooks.

Standard library only (no pip install). Built for AI agents reading spec
workbooks (API specs, test specs) where the header row is not row 1, merged
cells abound, and every project uses a different column layout.

Modes:
  structure FILE                       sheet list: range, rows, merges, hidden, header-guess
  extract   FILE --sheet NAME          one sheet as TSV (row number first)
            [--rows A-B] [--cols A-C] [--raw] [--show-formulas]
  search    FILE --text KEYWORD        find rows containing KEYWORD
            [--sheet NAME] [--limit N]
  convert   FILE --sheet NAME --profile PROFILE.json
            [--format json|markdown] [--rows A-B]

Behavior notes:
  - Merged cells: the anchor (top-left) value is filled into the whole merged
    range so grouped rows stay readable. Disable with --raw.
  - Formula cells show the cached value Excel stored on last save (what a
    human sees on screen). --show-formulas appends the formula as {=...};
    a cell with no cached value shows {=...} alone.
  - Date/time serials are rendered ISO (2026-07-09 / 13:45:00) based on the
    cell number format, including Japanese era and CJK builtin formats.
  - Output is budgeted (--max-chars, default 20000; convert is unlimited)
    and a truncation notice tells you how to narrow the request.
  - .xls / password-protected books are not supported: ask the user to
    re-save as plain .xlsx first.
"""
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timedelta

S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKGREL = "{http://schemas.openxmlformats.org/package/2006/relationships}"

DEFAULT_MAX_CHARS = 20000
# Builtin numFmtIds that render as dates/times, including the CJK/era ones
# (27-36, 50-58) that Japanese workbooks rely on.
BUILTIN_DATE_FMTS = set(range(14, 23)) | set(range(27, 37)) | {45, 46, 47} | set(range(50, 59))
NUM_RE = re.compile(r"-?\d+(\.\d+)?([eE][+-]?\d+)?")


def out(text, state):
    """Print with a global character budget so one call never floods context."""
    if state["max_chars"] <= 0:  # unlimited
        state["written"] += len(text)
        sys.stdout.write(text)
        return
    budget = state["max_chars"] - state["written"]
    if budget <= 0:
        state["truncated"] = True
        return
    if len(text) > budget:
        text = text[:budget]
        state["truncated"] = True
    state["written"] += len(text)
    sys.stdout.write(text)


def esc(s):
    """Keep one logical row on one physical TSV line."""
    return s.replace("\t", "\\t").replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")


# ---------------------------------------------------------------- refs

def col_to_index(ref):
    """'B3' or 'B' -> 1 (0-based column index)."""
    idx = 0
    for ch in ref:
        if ch.isalpha():
            idx = idx * 26 + (ord(ch.upper()) - 64)
        else:
            break
    return idx - 1


def index_to_col(idx):
    """1 -> 'B' (0-based)."""
    name = ""
    idx += 1
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        name = chr(65 + rem) + name
    return name


def parse_ref(ref):
    """'B3' -> (3, 1) as (row, 0-based col)."""
    m = re.match(r"([A-Za-z]+)(\d+)", ref)
    if not m:
        return None
    return int(m.group(2)), col_to_index(m.group(1))


def parse_range(text):
    m = re.fullmatch(r"(\d+)(?:-(\d+))?", text.strip())
    if not m:
        raise argparse.ArgumentTypeError("range must look like 3 or 4-9")
    a = int(m.group(1))
    return (a, int(m.group(2)) if m.group(2) else a)


def parse_colrange(text):
    m = re.fullmatch(r"([A-Za-z]+)(?:-([A-Za-z]+))?", text.strip())
    if not m:
        raise argparse.ArgumentTypeError("column range must look like B or A-F")
    a = col_to_index(m.group(1))
    return (a, col_to_index(m.group(2)) if m.group(2) else a)


# ---------------------------------------------------------------- workbook parts

def open_book(path):
    try:
        return zipfile.ZipFile(path)
    except FileNotFoundError:
        sys.exit(f"file not found: {path}")
    except zipfile.BadZipFile:
        sys.exit(f"{path} is not a readable .xlsx package. Password-protected or "
                 "corrupted books are not supported; ask the user for a plain .xlsx.")


def book_sheets(z):
    """Return [(name, part_target, hidden_bool)] in workbook order."""
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rid2target = {r.get("Id"): r.get("Target") for r in rels.findall(f"{PKGREL}Relationship")}
    sheets = []
    sheets_el = wb.find(f"{S}sheets")
    if sheets_el is None:
        return sheets
    for sh in sheets_el:
        target = (rid2target.get(sh.get(f"{RID}id"), "") or "").lstrip("/")
        if not target.startswith("xl/"):
            target = "xl/" + target
        hidden = (sh.get("state") or "visible") != "visible"
        sheets.append((sh.get("name"), target, hidden))
    return sheets


def book_date1904(z):
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    pr = wb.find(f"{S}workbookPr")
    return pr is not None and (pr.get("date1904") or "").lower() in ("1", "true")


def si_text(si):
    """Text of a shared/inline string, excluding phonetic (furigana) runs <rPh>."""
    parts = []
    t = si.find(f"{S}t")
    if t is not None:
        parts.append(t.text or "")
    for r in si.findall(f"{S}r"):
        rt = r.find(f"{S}t")
        if rt is not None:
            parts.append(rt.text or "")
    return "".join(parts)


def shared_strings(z):
    try:
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    except KeyError:
        return []
    return [si_text(si) for si in root.findall(f"{S}si")]


def _format_is_date(code):
    """True when a custom number format renders as a date/time."""
    code = re.sub(r'"[^"]*"', "", code)      # quoted literals: yyyy"年"
    code = re.sub(r"\[[^\]]*\]", "", code)   # colors, locale [$-411], elapsed [h]
    code = re.sub(r"\\.", "", code)          # escaped characters
    code = re.sub(r"general", "", code, flags=re.I)
    code = re.sub(r"[eE][+-]0*", "", code)   # scientific notation exponents
    # y/m/d/h/s plus e (year) and g (era) used by Japanese formats like ge.m.d
    return bool(re.search(r"[ymdhsegYMDHSEG]", code))


def date_styles(z):
    """Return a list: cellXfs index -> True if that style renders dates."""
    try:
        root = ET.fromstring(z.read("xl/styles.xml"))
    except KeyError:
        return []
    custom = {}
    num_fmts = root.find(f"{S}numFmts")
    if num_fmts is not None:
        for nf in num_fmts.findall(f"{S}numFmt"):
            try:
                custom[int(nf.get("numFmtId"))] = nf.get("formatCode") or ""
            except (TypeError, ValueError):
                pass
    is_date = []
    cell_xfs = root.find(f"{S}cellXfs")
    if cell_xfs is not None:
        for xf in cell_xfs.findall(f"{S}xf"):
            try:
                fmt_id = int(xf.get("numFmtId") or 0)
            except ValueError:
                fmt_id = 0
            is_date.append(fmt_id in BUILTIN_DATE_FMTS
                           or (fmt_id in custom and _format_is_date(custom[fmt_id])))
    return is_date


def serial_to_iso(serial, d1904):
    epoch = datetime(1904, 1, 1) if d1904 else datetime(1899, 12, 30)
    try:
        dt = epoch + timedelta(days=serial)
    except OverflowError:
        return str(serial)
    if dt.microsecond >= 500000:
        dt += timedelta(seconds=1)
    dt = dt.replace(microsecond=0)
    if 0 <= serial < 1:
        return dt.strftime("%H:%M:%S")
    if abs(serial - round(serial)) < 1e-9:
        return dt.strftime("%Y-%m-%d")
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------- sheet parsing

# A parsed cell is (value:str, is_text:bool, formula:str|None).

def parse_sheet(z, target, shared, isdate, d1904):
    """Return (rows, merges): rows = {rownum: {colidx: cell}}, merges = [(r1,c1,r2,c2)]."""
    try:
        root = ET.fromstring(z.read(target))
    except KeyError:
        return {}, []
    rows = {}
    data = root.find(f"{S}sheetData")
    if data is not None:
        next_row = 1
        for row_el in data.findall(f"{S}row"):
            r = int(row_el.get("r") or next_row)
            next_row = r + 1
            cells = {}
            next_col = 0
            for c in row_el.findall(f"{S}c"):
                ref = parse_ref(c.get("r") or "")
                col = ref[1] if ref else next_col
                next_col = col + 1
                cell = parse_cell(c, shared, isdate, d1904)
                if cell is not None:
                    cells[col] = cell
            if cells:
                rows[r] = cells
    merges = []
    mc = root.find(f"{S}mergeCells")
    if mc is not None:
        for m in mc.findall(f"{S}mergeCell"):
            ref = m.get("ref") or ""
            if ":" in ref:
                a, b = ref.split(":", 1)
                pa, pb = parse_ref(a), parse_ref(b)
                if pa and pb:
                    merges.append((pa[0], pa[1], pb[0], pb[1]))
    return rows, merges


def parse_cell(c, shared, isdate, d1904):
    t = c.get("t")
    formula = None
    f_el = c.find(f"{S}f")
    if f_el is not None:
        if f_el.text:
            formula = "=" + f_el.text
        elif (f_el.get("t") or "") == "shared":
            formula = "=shared"  # shifted references not reconstructed
    if t == "inlineStr":
        is_el = c.find(f"{S}is")
        val = si_text(is_el) if is_el is not None else ""
        return (val, True, formula)
    v = c.find(f"{S}v")
    if v is None or v.text is None:
        return (("", False, formula) if formula else None)
    raw = v.text
    if t == "s":
        try:
            return (shared[int(raw)], True, formula)
        except (ValueError, IndexError):
            return (raw, True, formula)
    if t == "b":
        return ("TRUE" if raw == "1" else "FALSE", False, formula)
    if t in ("str", "e", "d"):  # formula string / error / ISO date
        return (raw, True, formula)
    # numeric: date-styled cells become ISO strings
    try:
        style = int(c.get("s") or -1)
    except ValueError:
        style = -1
    if 0 <= style < len(isdate) and isdate[style]:
        try:
            return (serial_to_iso(float(raw), d1904), False, formula)
        except ValueError:
            pass
    return (raw, False, formula)


def fill_merges(rows, merges):
    """Copy each merge anchor's value over the covered range (rows gain
    synthesized entries so fully-merged rows are not silently dropped)."""
    for r1, c1, r2, c2 in merges:
        anchor = rows.get(r1, {}).get(c1)
        if anchor is None or anchor[0] == "":
            continue
        for r in range(r1, r2 + 1):
            cells = rows.setdefault(r, {})
            for c in range(c1, c2 + 1):
                if (r, c) == (r1, c1):
                    continue
                cur = cells.get(c)
                if cur is None or cur[0] == "":
                    cells[c] = anchor
    return rows


def render_cell(cell, show_formulas):
    val, _, formula = cell
    if show_formulas and formula:
        return f"{val} {{{formula}}}".strip() if val else f"{{{formula}}}"
    if val == "" and formula:  # no cached value: the formula is all we have
        return f"{{{formula}}}"
    return val


def row_tsv(rownum, cells, cols, show_formulas):
    lo = cols[0] if cols else 0
    hi = cols[1] if cols else max(cells)
    line = "\t".join(esc(render_cell(cells[i], show_formulas)) if i in cells else ""
                     for i in range(lo, hi + 1))
    return f"{rownum}\t{line}\n"


def guess_header(rows):
    """Best-effort header row guess over the first 20 non-empty raw rows.
    Raw (unfilled) data on purpose: a merged title row has only one real cell."""
    stats = []
    for r in sorted(rows)[:20]:
        cells = {c: v for c, v in rows[r].items() if v[0].strip()}
        if cells:
            n_text = sum(1 for v in cells.values() if v[1])
            stats.append((r, set(cells), n_text))
    if not stats:
        return None
    max_n = max(len(cols) for _, cols, _ in stats)
    for i, (r, cols, n_text) in enumerate(stats):
        n = len(cols)
        if n < 3 or n_text / n < 0.7 or n < 0.6 * max_n:
            continue
        if i + 1 < len(stats):
            next_cols = stats[i + 1][1]
            overlap = len(cols & next_cols) / max(1, min(n, len(next_cols)))
            if overlap < 0.5:
                continue
        return r
    return None


# ---------------------------------------------------------------- modes

def mode_structure(z, state):
    shared = shared_strings(z)
    isdate = date_styles(z)
    d1904 = book_date1904(z)
    for name, target, hidden in book_sheets(z):
        rows, merges = parse_sheet(z, target, shared, isdate, d1904)
        if rows:
            r_lo, r_hi = min(rows), max(rows)
            c_hi = max(max(c) for c in rows.values())
            rng = f"A{r_lo}:{index_to_col(c_hi)}{r_hi}"
        else:
            rng = "empty"
        guess = guess_header(rows)
        out(f"sheet: {name}\trange: {rng}\trows={len(rows)}\tmerges={len(merges)}"
            f"\thidden={'yes' if hidden else 'no'}"
            f"\theader-guess={guess if guess else '?'}\n", state)
    out("# header-guess is a hint - verify against real rows before trusting it.\n"
        "# Next: 'search --text KEYWORD' to locate content, or "
        "'extract --sheet NAME [--rows A-B]' to read one sheet.\n", state)


DEFAULT_EXTRACT_ROWS = 50


def load_sheet_or_exit(z, sheet_name, fill=True):
    sheets = {name: (target, hidden) for name, target, hidden in book_sheets(z)}
    if sheet_name not in sheets:
        sys.exit(f"sheet not found: {sheet_name!r}. Sheets: {', '.join(sheets)}")
    shared = shared_strings(z)
    isdate = date_styles(z)
    d1904 = book_date1904(z)
    rows, merges = parse_sheet(z, sheets[sheet_name][0], shared, isdate, d1904)
    if fill:
        rows = fill_merges(rows, merges)
    return rows


def mode_extract(z, args, state):
    if not args.sheet:
        sys.exit("extract requires --sheet NAME (run `structure` first to list sheets)")
    rows = load_sheet_or_exit(z, args.sheet, fill=not args.raw)
    if not rows:
        out("# empty sheet\n", state)
        return
    out(f"# sheet {args.sheet!r} as TSV (row number first"
        f"{', merged cells filled' if not args.raw else ', raw'})\n", state)
    row_nums = sorted(rows)
    if args.rows:
        row_nums = [r for r in row_nums if args.rows[0] <= r <= args.rows[1]]
    shown = 0
    last = None
    capped = False
    for r in row_nums:
        if args.rows is None and shown >= DEFAULT_EXTRACT_ROWS:
            capped = True
            break
        out(row_tsv(r, rows[r], args.cols, args.show_formulas), state)
        shown += 1
        last = r
    if capped:
        out(f"# stopped after {DEFAULT_EXTRACT_ROWS} rows (sheet has {len(rows)} non-empty rows). "
            f"Continue with --rows {last + 1}-{max(rows)}.\n", state)


def mode_search(z, args, state):
    if not args.text:
        sys.exit("search requires --text KEYWORD")
    shared = shared_strings(z)
    isdate = date_styles(z)
    d1904 = book_date1904(z)
    needle = args.text.casefold()
    hits = 0
    for name, target, hidden in book_sheets(z):
        if args.sheet and name != args.sheet:
            continue
        if hidden and not args.sheet:
            continue  # hidden sheets are searched only when named explicitly
        rows, merges = parse_sheet(z, target, shared, isdate, d1904)
        rows = fill_merges(rows, merges)
        for r in sorted(rows):
            if any(needle in cell[0].casefold() for cell in rows[r].values()):
                out(f"# match: sheet {name!r} row {r}\n", state)
                out(row_tsv(r, rows[r], None, False), state)
                hits += 1
                if hits >= args.limit:
                    out(f"# stopped at --limit {args.limit}. Narrow with --sheet or a longer keyword.\n", state)
                    return
    if hits == 0:
        out(f"# no match for {args.text!r}"
            f"{' in sheet ' + repr(args.sheet) if args.sheet else ' in any visible sheet'}\n", state)
    else:
        out("# Next: extract --sheet NAME --rows A-B around a hit to read its context.\n", state)


def _json_value(cell):
    val, is_text, _ = cell
    if not is_text:
        if val == "TRUE":
            return True
        if val == "FALSE":
            return False
        if NUM_RE.fullmatch(val):
            try:
                return int(val)
            except ValueError:
                return float(val)
    return val


def mode_convert(z, args, state):
    if not args.profile:
        sys.exit("convert requires --profile PROFILE.json - build one per the skill "
                 "workflow (see references/profile-format.md) and save it in the "
                 "target project under docs/excel-formats/.")
    if not args.sheet:
        sys.exit("convert requires --sheet NAME")
    try:
        with open(args.profile, encoding="utf-8-sig") as f:
            profile = json.load(f)
    except FileNotFoundError:
        sys.exit(f"profile not found: {args.profile}")
    except json.JSONDecodeError as e:
        sys.exit(f"profile is not valid JSON: {e}")

    cfg = dict(profile.get("sheet_defaults") or {})
    cfg.update((profile.get("sheets") or {}).get(args.sheet) or {})
    columns = cfg.get("columns")
    if not columns:
        sys.exit(f"profile has no column mapping for sheet {args.sheet!r} "
                 "(neither sheet_defaults.columns nor sheets[name].columns)")
    header_row = cfg.get("header_row")
    data_start = cfg.get("data_start_row") or ((header_row or 0) + 1)
    skip_if_empty = cfg.get("skip_row_if_empty") or []

    rows = load_sheet_or_exit(z, args.sheet, fill=True)

    col_map = []  # (colidx, field, label)
    for letter, spec in columns.items():
        field = (spec or {}).get("field") or letter
        col_map.append((col_to_index(letter), field, (spec or {}).get("label")))
    col_map.sort()

    # Drift check: does the sheet still have the headers the profile recorded?
    if header_row:
        actual = rows.get(header_row, {})
        for colidx, _, label in col_map:
            if not label:
                continue
            got = (actual.get(colidx, ("", False, None))[0] or "").strip()
            if got != label.strip():
                out(f"# WARNING: column {index_to_col(colidx)} header is {got!r} but the "
                    f"profile expects {label!r} - the format may have changed. "
                    "Re-verify the layout and update the profile.\n", state)

    records = []
    for r in sorted(rows):
        if r < data_start:
            continue
        if args.rows and not (args.rows[0] <= r <= args.rows[1]):
            continue
        cells = rows[r]
        rec = {"_row": r}
        for colidx, field, _ in col_map:
            cell = cells.get(colidx)
            rec[field] = _json_value(cell) if cell else ""
        check = skip_if_empty or [f for _, f, _ in col_map]
        if all(rec[f] is None or str(rec[f]).strip() == ""
               for f in check if f in rec):  # whitespace-only counts as empty
            continue
        records.append(rec)

    if args.format == "markdown":
        heads = [label or field for _, field, label in col_map]

        def md(v):
            if v is True or v is False:
                return "TRUE" if v else "FALSE"
            return re.sub(r"[\t\r\n]", " ", str(v)).replace("|", "\\|")

        out("| row | " + " | ".join(md(h) for h in heads) + " |\n", state)
        out("|---" * (len(heads) + 1) + "|\n", state)
        for rec in records:
            vals = [md(rec[f]) for _, f, _ in col_map]
            out(f"| {rec['_row']} | " + " | ".join(vals) + " |\n", state)
    else:
        out("[\n", state)
        for i, rec in enumerate(records):
            sep = "," if i < len(records) - 1 else ""
            out(json.dumps(rec, ensure_ascii=False) + sep + "\n", state)
        out("]\n", state)


# ---------------------------------------------------------------- main

def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["structure", "extract", "search", "convert"])
    ap.add_argument("file")
    ap.add_argument("--sheet", help="worksheet name")
    ap.add_argument("--rows", type=parse_range, help="Excel row range, e.g. 4-120")
    ap.add_argument("--cols", type=parse_colrange, help="column range, e.g. B-F")
    ap.add_argument("--raw", action="store_true", help="extract: do not fill merged cells")
    ap.add_argument("--show-formulas", action="store_true",
                    help="extract: append {=formula} to computed cells")
    ap.add_argument("--text", help="search: keyword (case-insensitive substring)")
    ap.add_argument("--limit", type=int, default=20, help="search: max matches (default 20)")
    ap.add_argument("--profile", help="convert: path to a format profile JSON")
    ap.add_argument("--format", choices=["json", "markdown"], default="json",
                    help="convert: output format (default json)")
    ap.add_argument("--max-chars", type=int, default=None,
                    help=f"output budget (default {DEFAULT_MAX_CHARS}; convert unlimited)")
    args = ap.parse_args()

    ext = args.file.lower().rsplit(".", 1)[-1] if "." in args.file else ""
    if ext == "xls":
        sys.exit(".xls is a legacy binary format. Ask the user to re-save it "
                 "as .xlsx (save-as in Excel or LibreOffice) first.")
    if ext not in ("xlsx", "xlsm"):
        sys.exit(f"unsupported extension .{ext} - this tool reads .xlsx/.xlsm only.")

    max_chars = args.max_chars if args.max_chars is not None else (
        0 if args.mode == "convert" else DEFAULT_MAX_CHARS)
    state = {"max_chars": max_chars, "written": 0, "truncated": False}

    with open_book(args.file) as z:
        if args.mode == "structure":
            mode_structure(z, state)
        elif args.mode == "extract":
            mode_extract(z, args, state)
        elif args.mode == "search":
            mode_search(z, args, state)
        else:
            mode_convert(z, args, state)

    if state["truncated"]:
        sys.stdout.write("\n# OUTPUT TRUNCATED at --max-chars. Narrow the request "
                         "(--sheet / --rows / --cols / --limit) or raise --max-chars.\n")


if __name__ == "__main__":
    main()
