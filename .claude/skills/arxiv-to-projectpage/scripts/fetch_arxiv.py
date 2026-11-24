# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pymupdf>=1.24",
# ]
# ///
"""
Fetch a paper's metadata, figures, and tables for filling in a project-page
`template.yaml`. Works from an arXiv link/id OR a direct PDF (URL or local file).

Run it through uv so the PEP 723 header above provides the (only) dependency,
PyMuPDF, which is used solely for the PDF path — the arXiv path is pure stdlib:

    pixi run uv run scripts/fetch_arxiv.py <arxiv-url-or-id> --out /tmp/paper.json
    pixi run uv run scripts/fetch_arxiv.py --pdf paper.pdf   --out /tmp/paper.json

Two-phase, so the skill keeps control of *which* images matter:

  1. List mode (default): emit a JSON summary of the paper — front matter,
     captioned figures, and tables converted to the template's uk-table HTML.
     Downloads/saves nothing. Each selectable image has a stable `id`.

  2. Save mode: pass --teaser <id> and/or --method <id[,id,...]> (ids as shown
     in list mode; a bare integer N is accepted as "Figure N") to write just
     those images into --public-dir as teaser.<ext> / method.<ext> /
     method2.<ext>… The `saved` block echoes the real filenames back.

Both input modes produce the same shape of result, so the skill's workflow is
identical either way. In PDF mode figures are found by their captions and
rendered as tight page clips (this handles vector figures and multi-panel
composites, which extracting embedded rasters cannot), and tables are read from
their ruled grid, so `tables[i].html` is populated for PDFs too.

arXiv input accepts: https://arxiv.org/abs/2312.02008v1 · /html/… · /pdf/… ·
2312.02008v1 · 2312.02008. PDF input: any local path or http(s) URL to a .pdf.
"""
import argparse
import html
import json
import os
import re
import sys
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin

UA = "Mozilla/5.0 (projectpage-template arxiv-to-projectpage skill)"


def eprint(*a):
    print(*a, file=sys.stderr)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def parse_arxiv_id(s):
    s = s.strip()
    m = re.search(r'(\d{4}\.\d{4,5})(v\d+)?', s)
    if not m:
        m = re.search(r'([a-z\-]+(?:\.[A-Z]{2})?/\d{7})(v\d+)?', s)
    if not m:
        raise SystemExit(f"Could not find an arXiv id in: {s!r}")
    return m.group(1) + (m.group(2) or "")


def fetch(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")


def strip_tags(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    return html.unescape(re.sub(r'\s+', ' ', s)).strip()


def safe_ext(src, allowed, default=".png"):
    ext = os.path.splitext(src.split("?")[0])[1].lower()
    return ext if ext in allowed else default


def parse_id_list(s):
    return [x for x in re.split(r'[,\s]+', s.strip()) if x] if s else []


def build_bibtex(arxiv_id, meta):
    bare = re.sub(r'v\d+$', '', arxiv_id) if arxiv_id else ""
    last = "unknown"
    if meta.get("authors"):
        last = re.sub(r'[^A-Za-z]', '', meta["authors"][0].split()[-1]).lower() or "unknown"
    authors = " and ".join(meta.get("authors", []))
    if not bare:
        # No arXiv id: a PDF doesn't state its venue, so leave that one field for
        # the human instead of guessing a booktitle onto their citation.
        word = re.sub(r'[^a-z0-9]', '', (meta.get("title", "").split() or [""])[0].lower())
        return (f"@inproceedings{{{last}{meta.get('year','')}{word},\n"
                f"  title={{{meta.get('title','')}}},\n"
                f"  author={{{authors}}},\n"
                f"  booktitle={{TODO(human): venue}},\n"
                f"  year={{{meta.get('year','')}}}\n"
                f"}}")
    return (f"@article{{{last}{meta.get('year','')}arxiv,\n"
            f"  title={{{meta.get('title','')}}},\n"
            f"  author={{{authors}}},\n"
            f"  journal={{arXiv preprint arXiv:{bare}}},\n"
            f"  year={{{meta.get('year','')}}}\n"
            f"}}")


# ---------------------------------------------------------------------------
# arXiv metadata (Atom API)
# ---------------------------------------------------------------------------
def get_metadata(arxiv_id):
    bare = re.sub(r'v\d+$', '', arxiv_id)
    xml = fetch(f"http://export.arxiv.org/api/query?id_list={bare}&max_results=1")
    entry = re.search(r'<entry>(.*?)</entry>', xml, re.S)
    entry = entry.group(1) if entry else xml

    def tag(name, s=entry):
        m = re.search(rf'<{name}>(.*?)</{name}>', s, re.S)
        return html.unescape(re.sub(r'\s+', ' ', m.group(1)).strip()) if m else ""

    published = tag("published")
    authors = [html.unescape(re.sub(r'\s+', ' ', a).strip())
               for a in re.findall(r'<author>\s*<name>(.*?)</name>', entry, re.S)]
    cats = re.findall(r'<category[^>]*term="([^"]+)"', entry)
    return {"title": tag("title"), "abstract": tag("summary"), "authors": authors,
            "year": published[:4] if published else "",
            "primary_category": cats[0] if cats else "", "doi": tag("arxiv:doi")}


# ---------------------------------------------------------------------------
# arXiv HTML: figures, standalone graphics, tables
# ---------------------------------------------------------------------------
class FigureTableParser(HTMLParser):
    """Collect top-level <figure class="ltx_figure|ltx_table"> blocks (raw inner
    HTML), and standalone <img class="ltx_graphics"> that live OUTSIDE any figure
    (the uncaptioned pull figures many papers put at the very top)."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.figures, self.tables, self.graphics = [], [], []
        self._stack, self._depth = [], 0
        self._fig_depth = None  # depth at which we're inside a figure

    def handle_starttag(self, tag, attrs):
        self._depth += 1
        a = dict(attrs)
        if tag == "figure":
            cls = a.get("class", "")
            kind = "table" if "ltx_table" in cls else ("figure" if "ltx_figure" in cls else None)
            if kind and not self._stack:
                self._stack.append([kind, self._depth, []])
                self._fig_depth = self._depth
        elif tag == "img" and not self._stack:
            cls = a.get("class", "")
            src = a.get("src", "")
            if "ltx_graphics" in cls and src and not src.startswith("data:"):
                self.graphics.append({"src": html.unescape(src),
                                      "width": a.get("width"), "height": a.get("height")})
        if self._stack:
            self._stack[-1][2].append(self.get_starttag_text())

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self._depth -= 1  # self-closing: undo the increment

    def handle_endtag(self, tag):
        if self._stack:
            self._stack[-1][2].append(f"</{tag}>")
            if tag == "figure" and self._depth == self._stack[-1][1]:
                kind, _, buf = self._stack.pop()
                raw = "".join(buf)
                (self.tables if kind == "table" else self.figures).append(raw)
                self._fig_depth = None
        self._depth -= 1

    def handle_data(self, data):
        if self._stack:
            self._stack[-1][2].append(data)

    def handle_entityref(self, name):
        if self._stack:
            self._stack[-1][2].append(f"&{name};")

    def handle_charref(self, name):
        if self._stack:
            self._stack[-1][2].append(f"&#{name};")


def caption_number(caption, kind):
    m = re.match(rf'\s*{kind}\s+(\d+)', caption, re.I)
    return int(m.group(1)) if m else None


def extract_caption(raw):
    m = re.search(r'<figcaption[^>]*>(.*?)</figcaption>', raw, re.S)
    return strip_tags(m.group(1)) if m else ""


def first_img_src(raw):
    m = re.search(r'<img[^>]*\ssrc="([^"]+)"', raw)
    return html.unescape(m.group(1)) if m else None


def extract_svg(raw):
    m = re.search(r'<svg\b.*?</svg>', raw, re.S)
    return m.group(0) if m else None


def catalog_html_images(fp):
    """Unify figures + standalone graphics into one list of selectable images.
    `id`: F<order> for figures, G<order> for standalone graphics. `figure`: the
    real Figure number (or null). `image_kind`: raster | svg | none."""
    images = []
    for order, raw in enumerate(fp.figures, 1):
        caption = extract_caption(raw)
        src = first_img_src(raw)
        if src and not src.startswith("data:"):
            kind, keep_src, svg = "raster", src, None
        elif extract_svg(raw):
            kind, keep_src, svg = "svg", None, extract_svg(raw)
        else:
            kind, keep_src, svg = "none", None, None
        images.append({"id": f"F{order}", "figure": caption_number(caption, "Figure"),
                       "caption": caption, "image_kind": kind, "has_image": kind != "none",
                       "src": keep_src, "_svg": svg})
    for gi, g in enumerate(fp.graphics, 1):
        images.append({"id": f"G{gi}", "figure": None,
                       "caption": "(uncaptioned graphic near top of paper)",
                       "image_kind": "raster", "has_image": True, "src": g["src"],
                       "_svg": None, "width": g.get("width"), "height": g.get("height")})
    return images


# ---- Table -> uk-table HTML ------------------------------------------------
class TabularParser(HTMLParser):
    """Grid of cells from <table class="ltx_tabular">, tracking header rows,
    bold, colspan, rowspan. Math is taken from the TeX <annotation> (so we don't
    duplicate MathML presentation text) with ^{}/_{} mapped to <sup>/<sub>."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self.header_rows = [], set()
        self._row = self._cell = None
        self._in_thead = False
        self._row_is_header = False
        self._math = 0          # depth inside <math>
        self._ann = 0           # depth inside TeX <annotation>
        self._math_tex = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "")
        if tag == "thead":
            self._in_thead = True
        elif tag == "tr":
            self._row, self._row_is_header = [], self._in_thead
        elif tag in ("td", "th"):
            # A cell is bold if the cell itself carries the bold class; inline
            # <b>/<strong>/bold-span below can also flip it on. Per-cell, so bold
            # never leaks across cells (an unmatched </td> can't unbalance a counter).
            self._cell = {"text": "", "bold": "ltx_font_bold" in cls,
                          "is_th": tag == "th" or "ltx_th" in cls,
                          "colspan": int(a.get("colspan", 1) or 1), "rowspan": int(a.get("rowspan", 1) or 1)}
        elif tag == "math":
            self._math += 1
            self._math_tex = ""
        elif tag == "annotation" and a.get("encoding") == "application/x-tex":
            self._ann += 1
        elif (tag in ("b", "strong") or "ltx_font_bold" in cls) and self._cell is not None:
            self._cell["bold"] = True
        elif tag == "br" and self._cell is not None:
            self._cell["text"] += " / "

    def handle_endtag(self, tag):
        if tag == "thead":
            self._in_thead = False
        elif tag == "tr":
            if self._row and any(c["text"].strip() for c in self._row):
                if self._row_is_header or all(c["is_th"] for c in self._row):
                    self.header_rows.add(len(self.rows))
                self.rows.append(self._row)
            self._row = None
        elif tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._cell["text"] = re.sub(r'\s+', ' ', self._cell["text"]).strip()
            self._row.append(self._cell)
            self._cell = None
        elif tag == "math":
            self._math = max(0, self._math - 1)
            if self._math == 0 and self._cell is not None:
                self._cell["text"] += tex_to_html(self._math_tex)
        elif tag == "annotation":
            self._ann = max(0, self._ann - 1)

    def handle_data(self, data):
        if self._cell is None:
            return
        if self._math:
            if self._ann:
                self._math_tex += data
            return
        self._cell["text"] += data


def tex_to_html(tex):
    tex = (tex or "").strip()
    tex = re.sub(r'\^\{([^{}]*)\}', r'<sup>\1</sup>', tex)
    tex = re.sub(r'_\{([^{}]*)\}', r'<sub>\1</sub>', tex)
    tex = re.sub(r'\^(\w)', r'<sup>\1</sup>', tex)
    tex = re.sub(r'_(\w)', r'<sub>\1</sub>', tex)
    tex = tex.replace(r'\%', '%').replace(r'\times', '×').replace(r'\pm', '±')
    tex = re.sub(r'\\(?:mathrm|mathbf|text|mathit)\{([^{}]*)\}', r'\1', tex)
    return tex


def mkcell(text, bold=False, colspan=1, rowspan=1):
    return {"text": text, "bold": bold, "colspan": colspan, "rowspan": rowspan}


def uktable_html(header_rows, body_rows):
    """Render cell grids as the template's uk-table markup. Shared by both input
    modes so an arXiv table and a PDF table come out looking identical."""

    def cell(c, tag):
        t = c["text"]  # may already contain inline <sup>/<sub> from math
        # escape only the non-tag text: our own tags are <b>/<sup>/<sub>
        t = re.sub(r'&(?!(?:amp|lt|gt|#\d+|sup|/sup|sub|/sub|b|/b);)', '&amp;', t)
        if c["bold"]:
            t = f"<b>{t}</b>"
        span = (f' colspan="{c["colspan"]}"' if c["colspan"] > 1 else "") + \
               (f' rowspan="{c["rowspan"]}"' if c["rowspan"] > 1 else "")
        return f"<{tag}{span}>{t}</{tag}>"

    L = ['<div class="uk-overflow-auto">',
         '  <table class="uk-table uk-table-small uk-text-small uk-table-divider">',
         '    <thead>']
    for row in header_rows:
        L.append("      <tr>" + "".join(cell(c, "th") for c in row) + "</tr>")
    L += ["    </thead>", "    <tbody>"]
    for row in body_rows:
        L.append("      <tr>" + "".join(cell(c, "td") for c in row) + "</tr>")
    L += ["    </tbody>", "  </table>", "</div>"]
    return "\n".join(L)


def table_to_ukhtml(raw):
    caption = extract_caption(raw)
    m = re.search(r'<table[^>]*class="[^"]*ltx_tabular[^"]*".*?</table>', raw, re.S)
    if not m:
        return None
    p = TabularParser()
    p.feed(m.group(0))
    if not p.rows:
        return None

    # Header rows: the contiguous leading rows that are either flagged headers
    # (inside <thead> / all-<th>) or entirely bold — this pulls a bold "N object
    # level | (%) (%)" sub-header row up into <thead> instead of stranding it in
    # the body. Data rows that merely bold their winning value aren't all-bold,
    # so they stay in <tbody>.
    header_idx, i = [], 0
    while i < len(p.rows) and (i in p.header_rows or all(c["bold"] for c in p.rows[i])):
        header_idx.append(i)
        i += 1
    if not header_idx:
        header_idx = [0]
    header_set = set(header_idx)
    html_out = uktable_html([p.rows[i] for i in header_idx],
                            [r for i, r in enumerate(p.rows) if i not in header_set])
    return {"number": caption_number(caption, "Table"), "caption": caption, "html": html_out}


# ---------------------------------------------------------------------------
# Saving images (arXiv figures/graphics or PDF images)
# ---------------------------------------------------------------------------
def save_html_image(img, base_url, public_dir, stem):
    if img["image_kind"] == "svg":
        dest = os.path.join(public_dir, stem + ".svg")
        with open(dest, "w", encoding="utf-8") as f:
            f.write(img["_svg"])
        eprint(f"  saved {img['id']} (svg) -> {dest} ({len(img['_svg'])} B)")
        return {"id": img["id"], "figure": img["figure"], "saved_as": os.path.basename(dest),
                "path": dest, "bytes": len(img["_svg"]), "kind": "svg", "src": "inline-svg"}
    ext = safe_ext(img["src"], (".png", ".jpg", ".jpeg", ".gif", ".webp"))
    dest = os.path.join(public_dir, stem + ext)
    data = fetch(urljoin(base_url, img["src"]), binary=True)
    with open(dest, "wb") as f:
        f.write(data)
    eprint(f"  saved {img['id']} -> {dest} ({len(data)} B)")
    return {"id": img["id"], "figure": img["figure"], "saved_as": os.path.basename(dest),
            "path": dest, "bytes": len(data), "kind": "raster", "src": urljoin(base_url, img["src"])}


def resolve_id(images, token):
    """Accept an explicit id (F3/G1/P2), or a bare int N == arXiv Figure N."""
    token = token.strip()
    by_id = {im["id"]: im for im in images}
    if token in by_id:
        return by_id[token]
    if re.fullmatch(r'\d+', token):
        n = int(token)
        for im in images:
            if im.get("figure") == n and im["has_image"]:
                return im
        # fall back to positional F<n>
        return by_id.get(f"F{n}")
    return None


def do_saves(images, base_url, public_dir, teaser, method, figures, saver):
    saved = {"teaser": None, "method": [], "figures": []}
    if teaser:
        im = resolve_id(images, teaser)
        if im and im["has_image"]:
            saved["teaser"] = saver(im, base_url, public_dir, "teaser")
        else:
            eprint(f"WARN: teaser id {teaser!r} not found / no image")
    for i, tok in enumerate(parse_id_list(method)):
        im = resolve_id(images, tok)
        if im and im["has_image"]:
            saved["method"].append(saver(im, base_url, public_dir, "method" if i == 0 else f"method{i+1}"))
        else:
            eprint(f"WARN: method id {tok!r} not found / no image")
    for tok in parse_id_list(figures):
        im = resolve_id(images, tok)
        if im and im["has_image"]:
            saved["figures"].append(saver(im, base_url, public_dir, f"fig_{im['id']}"))
        else:
            eprint(f"WARN: figure id {tok!r} not found / no image")
    return saved


# ---------------------------------------------------------------------------
# PDF path (PyMuPDF)
#
# A PDF has no figure/table markup, so everything here is anchored on the one
# structure a paper reliably does have: captions. "Fig. 3: …" tells us both that
# a figure exists and roughly where — the artwork is the inked area directly
# above the caption. Rendering that region beats pulling embedded rasters out of
# the file, because a LaTeX figure is usually vector (or a grid of sub-images),
# so the embedded streams are fragments of a figure, never the figure itself.
# ---------------------------------------------------------------------------
MARKS = "*∗†‡§¶#"
CAPTION_RE = re.compile(
    r'^\s*(Fig\.|Figure|FIG\.|FIGURE|Table|TABLE|Tab\.)\s*([IVXLC]+|\d+)\s*[:.—–-]')
ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
INSTITUTION_RE = re.compile(
    r'University|Universit|Institute|Corporation|Company|Laborator|College|School|'
    r'Academy|Research Center|Research Centre|Inc\b|Ltd\b|GmbH|Dept|Department')


def load_pdf_bytes(src):
    if re.match(r'^https?://', src):
        eprint(f"Downloading PDF: {src}")
        return fetch(src, binary=True)
    with open(os.path.expanduser(src), "rb") as f:
        return f.read()


def roman_to_int(s):
    if s.isdigit():
        return int(s)
    total, prev = 0, 0
    for ch in reversed(s.upper()):
        v = ROMAN.get(ch, 0)
        total += -v if v < prev else v
        prev = max(prev, v)
    return total or None


HYPHEN_BREAK = re.compile(r'([A-Za-z][\w-]*?)-[ \t]*\n[ \t]*(\w[\w-]*)')


class Vocab:
    """The paper's own words, used to tell apart the two hyphens that can end a
    line: the one LaTeX inserted to break "promis-ing", and the real one in
    "phase-specific". Dropping the second welds words together
    ("phasespecific") — the kind of typo a reader spots instantly."""

    def __init__(self, doc):
        self.words = set()
        for i in range(doc.page_count):
            for tok in re.findall(r'[A-Za-z][A-Za-z-]*', doc[i].get_text()):
                self.words.add(tok.strip("-").lower())
        # words the paper habitually hyphenates onto something: phase-aware,
        # phase-consistent → "phase-" is a compound former, so a broken
        # "phase-<x>" keeps its hyphen even if that exact compound occurs once
        self.prefixes = {w.split("-")[0] for w in self.words if "-" in w}

    def hyphenated(self, a, b):
        if (a + b).lower() in self.words:
            return False
        if (a + "-" + b).lower() in self.words:
            return True
        return a.split("-")[-1].lower() in self.prefixes


def build_vocab(doc):
    return Vocab(doc)


def repair_hyphens(s, vocab=None):
    """Rejoin words split across lines, keeping the hyphen when the paper itself
    treats the pieces as a compound."""
    def fix(m):
        a, b = m.group(1), m.group(2)
        return f"{a}-{b}" if vocab and vocab.hyphenated(a, b) else a + b
    return HYPHEN_BREAK.sub(fix, s)


def join_lines(s, vocab=None):
    """Reflow extracted text into prose."""
    return re.sub(r'\s*\n\s*', ' ', repair_hyphens(s, vocab)).strip()


def pdf_lines(page):
    """Text lines with font-size info, in reading order (row-major: lines whose
    y overlaps are one visual row, left to right — this keeps a multi-column
    author block in the order a reader would say the names).

    Rotated lines are dropped: on a preprint the sidebar stamp
    ("arXiv:2312.02008v4 [cs.RO] 27 Jan 2025") is set large enough to outrank the
    real title, and it is never part of the paper's content."""
    import fitz
    out = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for line in b["lines"]:
            if abs(line.get("dir", (1, 0))[1]) > 0.01:
                continue
            text = "".join(s["text"] for s in line["spans"])
            sizes = [round(s["size"], 1) for s in line["spans"] if s["text"].strip()]
            if not text.strip() or not sizes or re.match(r'^\s*arXiv:\d', text):
                continue
            out.append({"text": text, "bbox": fitz.Rect(line["bbox"]), "max_size": max(sizes),
                        "mode_size": max(set(sizes), key=sizes.count)})
    rows, tol = [], 4.0
    for ln in sorted(out, key=lambda l: l["bbox"].y0):
        if rows and ln["bbox"].y0 - rows[-1][0]["bbox"].y0 < tol:
            rows[-1].append(ln)
        else:
            rows.append([ln])
    return [ln for row in rows for ln in sorted(row, key=lambda l: l["bbox"].x0)]


def pdf_blocks(page):
    import fitz
    out = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        text, sizes = "", []
        for line in b["lines"]:
            for s in line["spans"]:
                text += s["text"]
                sizes.append(round(s["size"], 1))
            text += "\n"
        out.append({"bbox": fitz.Rect(b["bbox"]), "text": text,
                    "max_size": max(sizes) if sizes else 0})
    return out


def body_font_size(lines):
    if not lines:
        return 10.0
    sizes = [l["mode_size"] for l in lines]
    return max(set(sizes), key=sizes.count)


def parse_front_matter(doc, vocab=None):
    """Title, authors (with affiliation superscripts), affiliations, notes,
    abstract. All best-effort: a paper's front matter is visually structured,
    not semantically tagged, so this reads font sizes the way an eye would."""
    page = doc[0]
    lines = pdf_lines(page)
    body = body_font_size(lines)
    # Group by each line's *dominant* size, not its largest glyph: a title like
    # "π0: A Vision-Language-Action Flow Model for / General Robot Control" sets
    # the π in a bigger math font, which would otherwise orphan the second line.
    biggest = max((l["mode_size"] for l in lines), default=body)

    title_lines, started = [], False
    for l in lines:
        if abs(l["mode_size"] - biggest) < 0.6:
            title_lines.append(l["text"].strip())
            started = True
        elif started:
            break
    title = join_lines(" ".join(title_lines), vocab) if biggest > body + 0.5 else ""

    # hyperref-produced PDFs carry \title and \author in the document metadata,
    # which beats anything inferred from layout when it's there
    dmeta = doc.metadata or {}
    if len(dmeta.get("title") or "") > 8:
        title = re.sub(r'\s+', ' ', dmeta["title"]).strip()

    authors, seen_names = [], set()
    for l in lines[len(title_lines):]:
        t = l["text"].strip()
        if re.match(r'^(Abstract|ABSTRACT|Index Terms|Keywords|I\.|1\.?\s+Introduction)', t):
            break
        if l["max_size"] < body - 0.2 or "@" in t or INSTITUTION_RE.search(t):
            continue
        # split "A. Author1, B. Author2 and C. Author3" but keep "Name1,2" intact
        for part in re.split(r',(?!\s*[\d' + re.escape(MARKS) + r'])|\band\b', t):
            part = part.strip().strip(",")
            m = re.match(rf'^(.+?)[\s]*([\d{re.escape(MARKS)},\s]*)$', part)
            if not m:
                continue
            name = re.sub(rf'[\d{re.escape(MARKS)},\s]+$', '', m.group(1)).strip()
            if len(name) < 3 or not re.search(r'[A-Za-z]{2}', name) or name in seen_names:
                continue
            seen_names.add(name)
            authors.append({"name": name,
                            "affiliation": [int(d) for d in re.findall(r'\d', m.group(2) or "")],
                            "marks": [c for c in (m.group(2) or "") if c in MARKS]})

    if dmeta.get("author"):
        sep = ";" if ";" in dmeta["author"] else ","
        meta_authors = [a.strip() for a in dmeta["author"].split(sep) if len(a.strip()) > 2]
        if len(meta_authors) >= 2:
            # metadata lists names only — keep the superscript-derived
            # affiliations for the names we recognise
            by_name = {a["name"]: a for a in authors}
            authors = [by_name.get(n, {"name": n, "affiliation": [], "marks": []})
                       for n in meta_authors]

    text = page.get_text()
    m = re.search(r'\b(?:Abstract|ABSTRACT)\b\s*[:.—–-]*\s*(.+?)'
                  r'(?=\n\s*(?:I\.\s|1\.?\s+Introduction|Index Terms|Keywords|CCS\b))',
                  text, re.S)
    abstract = join_lines(m.group(1), vocab) if m else ""

    affiliations, notes = {}, []
    for line in text.split("\n"):
        s = line.strip()
        m = re.match(r'^(\d)\s*[.)]?\s+([A-Z][^,.;]{3,90})', s)
        if m and INSTITUTION_RE.search(m.group(2)):
            affiliations.setdefault(int(m.group(1)), m.group(2).strip())
        m = re.match(rf'^([{re.escape(MARKS)}])\s*(\w.{{3,150}}?)\s*$', s)
        if m:
            notes.append(f"{m.group(1)} {m.group(2).strip()}")

    # arXiv re-renders PDFs on demand, so its creation date can be today's;
    # the "arXiv:… [cs.RO] 31 Oct 2024" stamp is the real date when present
    year = ""
    for cand in re.findall(r'arXiv:\d+\.\d+v?\d*\s*\[[^\]]*\]\s*\d*\s*\w*\s*(\d{4})', text) + \
            re.findall(r'(\d{4})', dmeta.get("creationDate") or ""):
        if 1990 < int(cand) < 2100:
            year = cand
            break

    # Some PDFs embed subsetted fonts with no Unicode mapping: the text layer
    # comes out as control characters. Say so rather than letting the caller
    # write an empty overview and assume the paper had no abstract.
    warnings = []
    unmapped = sum(1 for c in text if (c < " " and c not in "\n\t\r") or 0xE000 <= ord(c) <= 0xF8FF)
    if text and unmapped / len(text) > 0.02:
        warnings.append("page-1 text has unmapped glyphs (subsetted font without a ToUnicode "
                        "map), so parsed text is unreliable — render PAGE1 and read it, or ask "
                        "the user for the abstract")
    if not title:
        warnings.append("could not identify a title from the layout — read text_pages[0]")
    if not abstract:
        warnings.append("no abstract found (the paper may not label it, or the text layer is "
                        "unreadable) — take it from the paper before filling `overview`")
    if len(authors) < 1:
        warnings.append("no authors parsed — read them from text_pages[0]")

    return {"title": title, "authors": authors, "abstract": abstract,
            "affiliations": [affiliations[k] for k in sorted(affiliations)],
            "author_notes": notes, "year": year, "warnings": warnings}


def autocrop(page, band, bg=248):
    """Shrink a rect to its inked content, measured on a cheap 1x grayscale
    render. The band we start from is deliberately generous (it stretches up to
    whatever text sits above the caption); this is what turns it into a tight
    crop around the artwork, and it works the same for vector and raster."""
    import fitz
    if band.width < 4 or band.height < 4:
        return band
    pix = page.get_pixmap(clip=band, colorspace=fitz.csGRAY)
    if not pix.width or not pix.height:
        return band
    data, w, h, s = pix.samples, pix.width, pix.height, pix.stride
    rows = [y for y in range(h) if min(data[y * s:y * s + w]) < bg]
    if not rows:
        return None  # nothing drawn here
    cols = [x for x in range(w) if min(data[y * s + x] for y in rows) < bg]
    sx, sy = band.width / w, band.height / h
    return fitz.Rect(band.x0 + cols[0] * sx, band.y0 + rows[0] * sy,
                     band.x0 + (cols[-1] + 1) * sx, band.y0 + (rows[-1] + 1) * sy)


def figure_band(page, blocks, cap, body, above=True):
    """The slab of page the figure can occupy: the caption's column, running
    away from the caption until we hit real text (a paragraph, a heading, or
    another caption). Small text is left in — those are axis labels."""
    import fitz
    x0, x1 = cap["bbox"].x0, cap["bbox"].x1
    edge = page.rect.y0 + 18 if above else page.rect.y1 - 18
    for b in blocks:
        r = b["bbox"]
        if above and r.y1 > cap["bbox"].y0 - 2:
            continue
        if not above and r.y0 < cap["bbox"].y1 + 2:
            continue
        if min(r.x1, x1) - max(r.x0, x0) < 0.3 * (x1 - x0):
            continue
        stops = len(b["text"].strip()) > 80 and b["max_size"] <= body + 0.6
        if stops or CAPTION_RE.match(b["text"]):
            edge = max(edge, r.y1) if above else min(edge, r.y0)
    return (fitz.Rect(x0 - 6, edge + 2, x1 + 6, cap["bbox"].y0 - 2) if above
            else fitz.Rect(x0 - 6, cap["bbox"].y1 + 2, x1 + 6, edge - 2))


def find_captions(page, blocks, vocab=None):
    caps = []
    for b in blocks:
        m = CAPTION_RE.match(b["text"])
        if not m:
            continue
        caps.append({"kind": "table" if m.group(1).lower().startswith("tab") else "figure",
                     "number": roman_to_int(m.group(2)),
                     "label": f"{m.group(1)} {m.group(2)}".replace("  ", " "),
                     "text": re.sub(r'\s+', ' ', join_lines(b["text"], vocab)).strip(),
                     "bbox": b["bbox"]})
    return sorted(caps, key=lambda c: (c["bbox"].y0, c["bbox"].x0))


def catalog_pdf_figures(doc, zoom=3.0, pad=3, vocab=None):
    """One entry per figure caption, with the page clip to render on save."""
    out = []
    for pno in range(doc.page_count):
        page = doc[pno]
        blocks = pdf_blocks(page)
        body = body_font_size(pdf_lines(page))
        for cap in find_captions(page, blocks, vocab):
            if cap["kind"] != "figure":
                continue
            # captions normally sit below the artwork; fall back to above it
            region = autocrop(page, figure_band(page, blocks, cap, body, above=True))
            if region is None or region.get_area() < 200:
                region = autocrop(page, figure_band(page, blocks, cap, body, above=False))
            if region is None or region.get_area() < 200:
                continue
            region = (region + (-pad, -pad, pad, pad)) & page.rect
            out.append({"id": f"F{len(out)+1}", "figure": cap["number"], "page": pno + 1,
                        "caption": cap["text"], "image_kind": "raster", "has_image": True,
                        "width": round(region.width * zoom), "height": round(region.height * zoom),
                        "_page": pno, "_clip": region})
    return out


class Rule:
    """A horizontal table rule. Deliberately not a fitz.Rect: these lines have
    zero height, and fitz treats a zero-height rect as empty, which makes rect
    unions silently drop segments."""

    def __init__(self, y, x0, x1):
        self.y0 = self.y1 = y
        self.x0, self.x1 = x0, x1

    @property
    def width(self):
        return self.x1 - self.x0


def h_rules(page, x0, x1, ytop, ybot):
    """Horizontal rules (booktabs \\toprule/\\midrule/\\cmidrule/\\bottomrule)
    inside a window: they delimit the table, split header from body, and mark
    column groups. LaTeX emits one rule as a run of per-column segments, so
    collinear neighbours are stitched back together first — otherwise a
    full-width \\midrule looks like five short lines and gets discarded."""
    import fitz
    segs = []
    for d in page.get_drawings():
        r = fitz.Rect(d["rect"])
        if r.height > 2.5 or r.width < 8:
            continue
        if r.y0 < ytop or r.y1 > ybot or r.x1 < x0 - 12 or r.x0 > x1 + 12:
            continue
        segs.append(Rule(r.y0, r.x0, r.x1))
    out = []
    for r in sorted(segs, key=lambda r: (round(r.y0 * 2) / 2, r.x0)):
        if out and abs(out[-1].y0 - r.y0) < 0.6 and r.x0 - out[-1].x1 < 3:
            out[-1].x1 = max(out[-1].x1, r.x1)
        else:
            out.append(r)
    return sorted(out, key=lambda r: r.y0)


def full_width(rules, x0, x1, gap=120):
    """The rules that bound this table: ones spanning the caption's full column
    width, taken as a contiguous run. Spanning matters because a two-column page
    puts a *neighbouring* table's rules in the same vertical window — those are
    narrower than the caption, and mistaking one for the bottom rule would drag
    a page of prose into the grid. The gap cutoff stops the run at the next
    table further down the column."""
    out = []
    W = x1 - x0
    for r in rules:
        if r.x0 > x0 + 0.15 * W or r.x1 < x1 - 0.15 * W:
            continue
        if out and r.y0 - out[-1].y0 > gap:
            break
        out.append(r)
    return out


def bold_rects(page):
    import fitz
    out = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for line in b["lines"]:
            for s in line["spans"]:
                if (s.get("flags", 0) & 2 ** 4) or \
                        re.search(r'bold|-medi|semib|black', s.get("font", ""), re.I):
                    out.append(fitz.Rect(s["bbox"]))
    return out


def word_grid(page, clip, divider_y=None, group_rules=()):
    """Read a ruled table into a cell grid. Rows come from y-overlap; columns
    come from gaps in the x-projection of the *body* rows only — headers often
    contain wide spanning labels ("Seen Shapes") that would otherwise smear the
    column boundaries. A run of words that straddles several columns becomes one
    cell with a colspan, which is how those group headers survive."""
    import fitz
    words = [w for w in page.get_text("words") if fitz.Rect(w[:4]).intersects(clip)]
    if not words:
        return [], []
    bolds = bold_rects(page)

    rows = []
    for w in sorted(words, key=lambda w: w[1]):
        y0, y1 = w[1], w[3]
        for r in rows:
            if min(r["y1"], y1) - max(r["y0"], y0) > 0.4 * min(r["y1"] - r["y0"], y1 - y0):
                r["words"].append(w)
                r["y0"], r["y1"] = min(r["y0"], y0), max(r["y1"], y1)
                break
        else:
            rows.append({"y0": y0, "y1": y1, "words": [w]})
    rows.sort(key=lambda r: r["y0"])
    for r in rows:
        # compare row centres, not edges: descenders push y1 past the rule
        r["header"] = divider_y is not None and (r["y0"] + r["y1"]) / 2 < divider_y

    ref = [r for r in rows if not r["header"]] or rows
    spans = sorted((w[0], w[2]) for r in ref for w in r["words"])
    merged = []
    for a, b in spans:
        if merged and a <= merged[-1][1] + 1.5:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    # Distinguish the space inside a cell ("50/100 (50%)") from the gutter
    # between columns. Both are just whitespace, but they differ by an order of
    # magnitude, so scale the threshold off the gaps this table actually uses.
    gaps = sorted(merged[i + 1][0] - merged[i][1] for i in range(len(merged) - 1))
    gap_limit = max(2.5, 0.4 * gaps[len(gaps) // 2]) if gaps else 2.5
    cols = [list(merged[0])] if merged else []
    for a, b in merged[1:]:
        if a - cols[-1][1] < gap_limit:
            cols[-1][1] = max(cols[-1][1], b)
        else:
            cols.append([a, b])
    bounds = [(cols[i][1] + cols[i + 1][0]) / 2 for i in range(len(cols) - 1)]
    ncols = len(bounds) + 1

    def col_of(x):
        return sum(1 for b in bounds if x > b)

    def is_bold(w):
        cx, cy = (w[0] + w[2]) / 2, (w[1] + w[3]) / 2
        return any(b.x0 <= cx <= b.x1 and b.y0 <= cy <= b.y1 for b in bolds)

    grid = []
    for r in rows:
        # Which \cmidrule (if any) sits directly under this word? A group header
        # like "Unseen Shapes" is centred over several columns and narrower than
        # them, so the rule beneath it — not the text extent — is its true span.
        def group_of(w):
            if not r["header"]:
                return None
            cx = (w[0] + w[2]) / 2
            for i, gr in enumerate(group_rules):
                if 0 < gr.y0 - r["y1"] < 8 and gr.x0 - 2 <= cx <= gr.x1 + 2:
                    return i
            return None

        # Group words into runs, one run per cell: words join a run when they
        # belong to the same column group, or (outside a group) when the gap is
        # narrow enough to be an in-cell space and they share a column.
        runs = []
        for w in sorted(r["words"], key=lambda w: w[0]):
            g = group_of(w)
            joins = runs and runs[-1]["group"] == g and (
                g is not None or (w[0] - runs[-1]["x1"] < gap_limit
                                  and col_of((w[0] + w[2]) / 2) == runs[-1]["col"]))
            if joins:
                runs[-1]["text"] += " " + w[4]
                runs[-1]["x1"] = w[2]
                runs[-1]["bold"] &= is_bold(w)
            else:
                runs.append({"text": w[4], "x0": w[0], "x1": w[2], "group": g,
                             "col": col_of((w[0] + w[2]) / 2), "bold": is_bold(w)})
        cells, next_col = [], 0
        for run in runs:
            lo, hi = run["x0"], run["x1"]
            if run["group"] is not None:
                lo, hi = group_rules[run["group"]].x0, group_rules[run["group"]].x1
            first, last = max(col_of(lo + 1), next_col), max(col_of(hi - 1), next_col)
            cells += [mkcell("") for _ in range(first - next_col)]
            cells.append(mkcell(clean_cell(run["text"]), bold=run["bold"],
                                colspan=last - first + 1))
            next_col = last + 1
        cells += [mkcell("") for _ in range(ncols - next_col)]
        grid.append({"cells": cells, "header": r["header"]})
    return [g["cells"] for g in grid if g["header"]], [g["cells"] for g in grid if not g["header"]]


def clean_cell(t):
    t = t.replace("↑", "&#8593;").replace("↓", "&#8595;")
    return re.sub(r'\s+', ' ', t).strip()


def catalog_pdf_tables(doc, vocab=None):
    """Tables are found from their caption plus the rules beneath it. The rules
    also give us the table's true bottom edge, which keeps trailing "Note: …"
    prose out of the grid."""
    import fitz
    out = []
    for pno in range(doc.page_count):
        page = doc[pno]
        blocks = pdf_blocks(page)
        for cap in find_captions(page, blocks, vocab):
            if cap["kind"] != "table":
                continue
            x0, x1 = cap["bbox"].x0, cap["bbox"].x1
            rules = h_rules(page, x0, x1, cap["bbox"].y1, page.rect.y1)
            if len(full_width(rules, x0, x1)) < 2:
                rules = h_rules(page, x0, x1, page.rect.y0, cap["bbox"].y0)  # caption below table
            entry = {"number": cap["number"], "caption": cap["text"], "page": pno + 1,
                     "html": None}
            full = full_width(rules, x0, x1)
            if len(full) >= 2:
                clip = fitz.Rect(x0 - 3, full[0].y0 - 3, x1 + 3, full[-1].y1 + 1)
                # the first interior full-width rule is the header/body split
                divider = full[1].y0 if len(full) > 2 else None
                groups = [r for r in rules if r not in full and r.y1 <= clip.y1]
                header, body = word_grid(page, clip, divider_y=divider, group_rules=groups)
                if not header and body:
                    header, body = body[:1], body[1:]
                if body:
                    entry["html"] = uktable_html(header, body)
            if entry["html"] is None:
                entry["note"] = ("could not read a grid here (no table rules found) — "
                                 "transcribe this one by hand from the paper")
            out.append(entry)
    return out


def process_pdf(src, public_dir, teaser, method, figures, out_path=None,
                text_pages=3, zoom=3.0, min_px=200):
    import fitz  # PyMuPDF, from the PEP 723 header
    doc = fitz.open(stream=load_pdf_bytes(src), filetype="pdf")
    vocab = build_vocab(doc)
    front = parse_front_matter(doc, vocab)
    images = catalog_pdf_figures(doc, zoom=zoom, vocab=vocab)
    eprint(f"PDF: {doc.page_count} pages, {len(images)} captioned figures")
    for w in front["warnings"]:
        eprint(f"WARN: {w}")

    # Embedded rasters stay available as a fallback (photo-only figures, or a
    # caption the regex missed), de-duplicated by xref and filtered by size.
    seen = set()
    for pno in range(doc.page_count):
        for info in doc.get_page_images(pno, full=True):
            xref = info[0]
            if xref in seen:
                continue
            seen.add(xref)
            try:
                ext = doc.extract_image(xref)
            except Exception:
                continue
            w, h = ext.get("width", 0), ext.get("height", 0)
            if w < min_px or h < min_px:
                continue
            n = sum(1 for im in images if im["id"].startswith("P"))
            images.append({"id": f"P{n+1}", "figure": None, "page": pno + 1,
                           "caption": f"(embedded image on page {pno+1}, uncaptioned)",
                           "image_kind": "raster", "has_image": True, "width": w, "height": h,
                           "_ext": ext["ext"], "_bytes": ext["image"]})
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
    images.append({"id": "PAGE1", "figure": None, "page": 1,
                   "caption": "(rendered image of page 1 — last-resort teaser)",
                   "image_kind": "raster", "has_image": True, "width": pix.width,
                   "height": pix.height, "_render": pix.tobytes("png")})

    def saver(im, base_url, pdir, stem):
        if "_clip" in im:
            data = doc[im["_page"]].get_pixmap(matrix=fitz.Matrix(zoom, zoom),
                                               clip=im["_clip"]).tobytes("png")
            ext = ".png"
        else:
            data, ext = im.get("_bytes") or im.get("_render"), "." + im.get("_ext", "png")
        dest = os.path.join(pdir, stem + ext)
        with open(dest, "wb") as f:
            f.write(data)
        eprint(f"  saved {im['id']} -> {dest} ({len(data)} B)")
        return {"id": im["id"], "figure": im.get("figure"), "saved_as": os.path.basename(dest),
                "path": dest, "bytes": len(data), "kind": "raster", "src": f"pdf:{src}"}

    saved = do_saves(images, "", public_dir, teaser, method, figures, saver)
    tables = catalog_pdf_tables(doc, vocab)

    text_path = None
    if out_path and out_path != "-":
        text_path = os.path.splitext(out_path)[0] + ".txt"
        with open(text_path, "w", encoding="utf-8") as f:
            for i in range(doc.page_count):
                f.write(f"\n=== page {i+1} ===\n{repair_hyphens(doc[i].get_text(), vocab)}")
        eprint(f"Wrote {text_path} (full text, {doc.page_count} pages)")

    catalog = [{k: v for k, v in im.items() if not k.startswith("_")} for im in images]
    meta = {"title": front["title"], "authors": [a["name"] for a in front["authors"]],
            "year": front["year"]}
    return {"source": "pdf", "pdf_path": src, "pdf_metadata": doc.metadata or {},
            **{k: v for k, v in front.items() if k != "authors"},
            "authors": front["authors"], "author_names": meta["authors"],
            "tl_dr_source": front["abstract"],
            "text_pages": [doc[i].get_text() for i in range(min(text_pages, doc.page_count))],
            "text_path": text_path, "page_count": doc.page_count,
            "images": catalog, "tables": tables,
            "bibtex": build_bibtex("", meta), "saved": saved,
            "note": ("Front matter is parsed from page-1 layout — sanity-check title/authors "
                     "against text_pages[0] before writing YAML. Figures (F*) are rendered "
                     "page clips anchored on captions; P*/PAGE1 are fallbacks. Venue is not "
                     "in the PDF, so bibtex needs the booktitle filled in.")}


# ---------------------------------------------------------------------------
# arXiv path
# ---------------------------------------------------------------------------
def process_arxiv(arxiv_in, public_dir, teaser, method, figures):
    arxiv_id = parse_arxiv_id(arxiv_in)
    eprint(f"arXiv id: {arxiv_id}")
    meta = get_metadata(arxiv_id)
    html_url = f"https://arxiv.org/html/{arxiv_id}"
    base_url = html_url + "/"
    eprint(f"Fetching HTML: {html_url}")
    images, tables = [], []
    try:
        fp = FigureTableParser()
        fp.feed(fetch(html_url))
        eprint(f"Found {len(fp.figures)} figures, {len(fp.graphics)} standalone graphics, {len(fp.tables)} tables")
        images = catalog_html_images(fp)
        tables = [t for t in (table_to_ukhtml(t) for t in fp.tables) if t]
    except Exception as e:
        eprint(f"WARN: could not process HTML ({e}). Metadata/bibtex still available; figures/tables skipped.")

    saved = do_saves(images, base_url, public_dir, teaser, method, figures, save_html_image)
    catalog = [{k: v for k, v in im.items() if not k.startswith("_")} for im in images]
    return {"source": "arxiv", "arxiv_id": arxiv_id,
            "abs_url": f"https://arxiv.org/abs/{arxiv_id}", "html_url": html_url, **meta,
            "tl_dr_source": meta["abstract"], "bibtex": build_bibtex(arxiv_id, meta),
            "images": catalog, "tables": tables, "saved": saved}


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("arxiv", nargs="?", help="arXiv url or id (omit if using --pdf)")
    ap.add_argument("--pdf", help="path or http(s) URL to a PDF (direct-PDF mode)")
    ap.add_argument("--public-dir", default="public")
    ap.add_argument("--out", default="-")
    ap.add_argument("--teaser", default=None, help="image id (or bare Figure N) -> teaser.<ext>")
    ap.add_argument("--method", default="", help="comma list of ids -> method.<ext>, method2.<ext>, …")
    ap.add_argument("--figures", default="", help="comma list of ids -> fig_<id>.<ext>")
    ap.add_argument("--zoom", type=float, default=3.0,
                    help="PDF mode: render scale for figure clips (3 ~= 216 dpi)")
    ap.add_argument("--text-pages", type=int, default=3,
                    help="PDF mode: pages of text inlined in the JSON (full text goes to <out>.txt)")
    args = ap.parse_args()

    if not args.pdf and not args.arxiv:
        ap.error("provide an arXiv url/id or --pdf")
    os.makedirs(args.public_dir, exist_ok=True)

    if args.pdf:
        result = process_pdf(args.pdf, args.public_dir, args.teaser, args.method, args.figures,
                             out_path=args.out, text_pages=args.text_pages, zoom=args.zoom)
    else:
        result = process_arxiv(args.arxiv, args.public_dir, args.teaser, args.method, args.figures)

    out = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out == "-":
        print(out)
    else:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(out)
        eprint(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
