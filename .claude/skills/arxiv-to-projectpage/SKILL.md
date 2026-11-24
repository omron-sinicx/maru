---
name: arxiv-to-projectpage
description: >-
  Fill in this repo's project-page `template.yaml` from a paper — an arXiv link
  or id (arxiv.org/abs/..., /html/..., /pdf/..., or a bare id like 2312.02008),
  or a PDF (a local draft such as `draft.pdf`, a camera-ready, or a .pdf URL).
  Use this whenever the user points at a paper and wants a project page, teaser,
  paper page, or template.yaml populated — even if they only paste the link or
  the filename and say "make a project page" or "fill the template". It pulls
  the title, authors, affiliations, and abstract, saves the teaser and method
  figures into `public/`, writes a TL;DR, and converts the paper's result tables
  into the UIKit HTML tables the template expects.
compatibility: >-
  Runs scripts/fetch_arxiv.py through uv (PEP 723 inline deps). Requires `pixi`
  with the `uv` dependency (already in pixi.toml); no manual pip installs.
  Network access to arxiv.org for arXiv input; PDF input works offline.
---

# Paper → project page template.yaml

This skill turns a paper into a filled-in `template.yaml` for the omron-sinicx
project-page template. `scripts/fetch_arxiv.py` does the deterministic work —
reading metadata, cropping the right figures, converting tables. Your job is the
judgment it can't do: choosing the teaser, writing a crisp TL;DR, and slotting
the content into the template's structure while preserving everything the paper
doesn't touch.

## Running the script (uv / PEP 723)

The script declares its own dependencies in a PEP 723 header, so **always run it
through uv** — never `python3` it directly:

```bash
pixi run uv run .claude/skills/arxiv-to-projectpage/scripts/fetch_arxiv.py <args>
```

uv reads the header and provides the one dependency (PyMuPDF, used for the PDF
path). The arXiv path is pure stdlib, so the first run is quick.

## Two input modes, one workflow

- **arXiv**: metadata from the arXiv API, figures and tables from the rendered
  HTML (`arxiv.org/html/<id>`).
- **PDF** (`--pdf <path-or-url>`): for a paper that isn't on arXiv yet — an
  in-progress draft, a submission, a camera-ready. Front matter is read from the
  page-1 layout, figures are cropped from the pages by their captions, and
  tables are read out of their ruled grid.

Both return the same JSON shape, so the steps below are the same either way.
Prefer arXiv when the paper is public (its metadata is authoritative); use
`--pdf` for anything unpublished, and note that a *draft* PDF's numbers may
still change — worth mentioning to the user when the page quotes results.

## Workflow

### 1. List the paper's contents (no downloads yet)

Use a **per-paper output path** so parallel runs don't clobber each other:

```bash
# arXiv
pixi run uv run .claude/skills/arxiv-to-projectpage/scripts/fetch_arxiv.py \
  "<arxiv-url-or-id>" --out /tmp/paper-<arxiv-id>.json
# or a PDF (local file or URL)
pixi run uv run .claude/skills/arxiv-to-projectpage/scripts/fetch_arxiv.py \
  --pdf "<path-or-url>" --out /tmp/paper-<name>.json
```

Read the JSON. Both modes give `title`, `authors`, `abstract`, `year`, `bibtex`,
an `images` catalog, and `tables` with pre-converted UIKit HTML. Mode-specific
extras:

- **arXiv**: `abs_url` (use it for `resources.paper`), authors as plain names.
- **PDF**: `authors` as `{name, affiliation, marks}` — the affiliation numbers
  and `*`/`†` markers come from the superscripts by each name — plus
  `affiliations` (the footnote institutions), `author_notes` (the `*`/`†`
  footnotes), `warnings`, and `text_path`, a sidecar `.txt` with the full paper
  text. Read that file when you write the Method/Results prose; `text_pages[0]`
  is enough to sanity-check the front matter.

**Read `warnings` first** — it's where the script tells you what it couldn't do,
e.g. a PDF whose fonts have no Unicode mapping (the text layer comes out as
control characters, so there is no abstract to extract; render `PAGE1` and read
it, or ask the user to paste the abstract). An empty `abstract` with a warning
means "unavailable", not "the paper has none".

Front matter otherwise comes from the PDF's own `\title`/`\author` metadata when
present — authoritative, and it keeps LaTeX like `$\pi_0$` intact for KaTeX —
falling back to font-size inference. Either way, **check it against
`text_pages[0]`** before writing YAML. `year` is the weakest field (a draft's
creation date, or an arXiv re-render date that isn't the paper's year), so verify
it before it lands in the bibtex.

Every selectable image has a stable **`id`**:

| id            | meaning                                                                        |
| ------------- | ------------------------------------------------------------------------------ |
| `F1`, `F2`, … | figures in document order; `figure` = the real "Figure N" (may be null on arXiv) |
| `G1`, `G2`, … | uncaptioned graphics near the top of an arXiv paper (often the true teaser)     |
| `P1`, `P2`, … | raw images embedded in a PDF — fragments, useful only as a fallback             |
| `PAGE1`       | a rendered image of the PDF's first page (last-resort teaser)                   |

In PDF mode, `F*` entries are page clips cropped to the artwork above each
caption, which is what you almost always want: a LaTeX figure is usually vector
or a grid of sub-images, so the embedded `P*` streams are pieces of a figure
rather than the figure. Reach for `P*` only when a caption's crop came back
wrong, and for `PAGE1` only when nothing else works.

`image_kind` is `raster` (downloadable/renderable), `svg` (inline vector, saved
as `.svg`), or `none` (an arXiv placeholder the HTML didn't inline). Only
`has_image: true` images can be saved.

### 2. Choose the teaser and method figures — from the captions

This is the one editorial step. Read the captions and pick:

- **Teaser**: the single image that best sells the paper. Usually the
  lowest-numbered figure whose caption reads like an overview or headline result
  ("overview", "given a collection of…", "we propose", qualitative samples).
  Figure 1 is the common choice — but on arXiv check `has_image`: **Figure 1
  sometimes has `image_kind: none`** (a composite the HTML didn't inline). When
  that happens, use a `G*` uncaptioned graphic if present, else the next figure
  with an image, and say which you used. Prefer `raster` over `svg` for the
  teaser since it's also the social/OGP card.
- **Method figure(s)**: one or two figures of the architecture / approach —
  captions with "framework", "architecture", "overview", "our model", "pipeline".

If nothing suitable has an image, say so and leave the teaser as-is — tell the
user to drop a `public/teaser.png` in manually.

### 3. Save the chosen images

Select by **id** (a bare integer also works as "Figure N"):

```bash
pixi run uv run .claude/skills/arxiv-to-projectpage/scripts/fetch_arxiv.py \
  --pdf draft.pdf --public-dir public --teaser F1 --method F2,F3 \
  --out /tmp/paper-<name>.json
```

This writes `public/teaser.<ext>`, `public/method.<ext>`, `public/method2.<ext>`
(arXiv extensions are preserved; PDF clips are always `.png`). The JSON's `saved`
block echoes the real filenames — use those exact names in the YAML, because a
jpg teaser is saved as `teaser.jpg`. Selecting by id matters: figures LaTeXML
split into subcaptions come back with `figure: null` and are only reachable by
their `F*` id.

**Look at what you saved** — a Read on the PNG costs one tool call and catches a
mis-cropped figure (a neighbouring caption line at the bottom, a slab of
whitespace) before it lands on the page. If a crop is off, the usual fixes are
the corresponding `P*` image or a larger `--zoom`. If a saved image is very large
(say >2 MB), mention it — the user may want to downsize it for page speed — but
don't block on it.

### 4. Ask the two things the paper cannot tell you

Before writing the YAML, ask the user — **one `AskUserQuestion` call with both
questions**, so they answer once and you fill everything in a single pass. These
two are asked *every run*, even when the PDF looks like it answered them:

1. **The repository name**, for `image:` and `url:`. The template ships
   `https://omron-sinicx.github.io/${your-repository-name}/teaser.png` — a
   placeholder that is **invisible on the rendered page** and only fails when
   someone shares the link, at which point the OGP/Twitter card has a broken
   image and a dead canonical URL. Never guess it from the paper title, the arXiv
   id, or the method name, and never ship it unresolved. Ask, then substitute the
   name into **both** fields. Offer the likeliest candidates as options (the
   method name lower-cased, the repo of `resources.code` if the paper gives one)
   and let them correct you.
2. **Who carries which author note** — which authors are interns, which
   contributed equally, and who are joint last authors. `author_notes` from a PDF
   only catches footnotes typeset in the front matter, arXiv metadata has none at
   all, and a mark the paper omitted is exactly the kind of credit error a project
   page shouldn't introduce. When the PDF *did* give marks, ask them to confirm
   what you extracted (offer it as the first option, e.g. "Jeremy = intern, Hamaya
   + Nishimura = joint last authors — as printed in the PDF"); when it gave
   nothing, ask outright. "No notes" is a legitimate answer — take it and move on.

Only these two block the fill. Everything else you can't determine goes to the
handover checklist in step 7 instead of a question.

### 5. Fill in template.yaml

Edit `template.yaml` **in place**. Fill what the paper gives you; leave
repo-specific fields alone.

- `title` — the paper title (keep LaTeX like `$\pi_0$` so KaTeX renders it).
- `resources.paper` — the `abs_url` (arXiv) or the paper URL. A local PDF has no
  URL: leave it empty with a `TODO(human)` rather than inventing one.
- `description` — a **1–2 sentence TL;DR you write** (not the raw abstract). This
  is the OGP/Twitter text and the page's one-line hook: problem, what's new,
  result. **It must fit on two rendered lines — keep it under ~140 characters**,
  because it renders as a centred paragraph beside a `TL;DR` label in a narrow
  container. Cut the baseline's full name, cut hedges, keep the number.
- `image` / `url` — **ask** for the repository name and substitute it (see below);
  the teaser _filename_ still goes in `teaser`.
- `teaser` — the saved teaser filename (`teaser.png` / `teaser.jpg` / `teaser.svg`).
- `authors` — one entry per author, in order (see note below).
- `bibtex` — start from the `bibtex` in the JSON, then **fix the venue** (see
  below) before it lands in the YAML (block scalar with `>`).
- `overview` — the abstract, lightly cleaned (drop a leading "Abstract"). A TL;DR
  sentence up front is fine; stay faithful — don't invent claims.
- `body` — see structure below.

**Authors.** The arXiv API gives names only: write each as `- name: <full name>`
with `affiliation: [1]` as a safe default, then flag affiliations for a human
pass. A PDF gives more — the superscripts resolve to real `affiliation` indices
and the footnotes name the institutions, so fill `authors[].affiliation`, the
`affiliations:` list, `authors[].mark`, and `meta:`. `position` stays human-only;
never guess a job title.

**Author marks and `meta` notes.** Write what the user told you in step 4, using
`authors[].marks` from the JSON and `author_notes` as the starting point (their
answer wins over both). A mark goes in `authors[].mark` — a string, or a list if
an author carries two — and renders as `Mai Nishimura`&nbsp;`1†`. The matching
footnote goes in `meta:`, **one note per list entry**:

```yaml
authors:
  - name: Jeremy Siburian
    affiliation: [1, 2]
    mark: '*'
  - name: Mai Nishimura
    affiliation: [1]
    mark: '†'
meta:
  - '* Equal contribution.'
  - '* Work done during an internship at OMRON SINIC X.'
  - '† Joint last authors.'
```

Each entry renders on its own line, so never join two notes into one string.
Keep the paper's own wording and glyphs, and keep the glyph in the note
identical to the `mark` on the author it refers to. Include only the notes the
paper actually makes — the three above are the common ones (equal contribution,
internship, joint last authors), not a checklist to fill. If the PDF's marks
came through as Unicode variants (`∗` U+2217 vs `*`), normalize both the note
and the `mark` to the plain ASCII `*`.

**Homepages.** Search the web for each author's homepage and fill
`authors[].url` — a personal site (`*.github.io`, a lab-hosted page), the
institution's researcher page, or Google Scholar, in that order of preference.
Confirm it's the right person before writing it: the page must match on name
*and* affiliation or research area, since common names collide. Skip the URL for
anyone you can't place confidently rather than linking a plausible stranger.

**Venue and bibtex.** The script's bibtex is a stub with a placeholder venue.
When the venue *is* known — `conference:` is already filled in `template.yaml`,
or the paper's header says "accepted to …" — **look up the venue's official name
for that year** and write a real entry instead of leaving a `TODO(human)`:

```yaml
conference: IROS2026
bibtex: >
  @inproceedings{siburian2026phase,
    title={PHASE: Compliance-Enabled Tactile Phase Retrieval for Few-Shot Insertion Learning},
    author={Siburian, Jeremy and Beltran-Hernandez, Cristian C. and Matsushima, Tatsuya and Iwasawa, Yusuke and Hamaya, Masashi and Nishimura, Mai},
    booktitle={2026 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)},
    address={Pittsburgh, PA, USA},
    organization={IEEE},
    year={2026}
  }
```

Rules for that entry: `author` in BibTeX `Last, First` form joined with `and`;
`booktitle` the year-prefixed proceedings title as the publisher writes it (the
search that settles it is "<venue> <year> official name", or the conference
site); `address` the host city if the search gives it; `organization` the sponsor
(IEEE, ACM, IEEE/RSJ…). Only a genuinely undecided venue (a draft under
submission) stays `TODO(human): venue` — and say so in your summary. Never invent
an acceptance the paper doesn't claim.

**Preserve vs. purge — an important distinction.** The template ships pre-filled
with a _different_ paper's data (the MULTIPOLAR example). Two kinds of fields:

- **Repo/venue-generic — preserve**: `theme`, `organization`, `twitter`,
  `speakerdeck`, `header`, `projects`. Leave these exactly as-is unless the user
  asks otherwise.
- **Paper-specific — replace or clear, never leave stale**: `title`, `authors`,
  `affiliations`, `meta`, `description`, `overview`, `bibtex`, `teaser`,
  `resources.*` (paper/code/video/blog/demo/huggingface), `conference`. If the
  new paper doesn't supply one (no code repo yet, venue not decided, a PDF with
  no arXiv link), **clear it and add a `TODO(human)` marker** rather than leaving
  the old paper's value — a stale `code: github.com/…/multipolar` on a different
  paper's page is a real bug.

#### Prose rules for every field on the page

**Never use an em dash.** Not in `description`, not in `overview`, not in `body`
prose, not in a figure caption you shorten — nowhere the page renders. Rewrite as
two clauses joined by "so"/"and", a colon, a comma, or two sentences:

| don't                                         | do                                             |
| --------------------------------------------- | ---------------------------------------------- |
| `dynamics — no phase labels required`          | `dynamics without any phase labels`            |
| `below $\eta$ — the onset of stable engagement` | `below $\eta$, the onset of stable engagement` |
| `five geometries — circle and square are seen` | `five geometries: circle and square are seen`   |

Hyphens in compounds (`peg-in-hole`, `phase-consistent`) are fine, and an en dash
inside a numeric range (`0–1`) is fine. Only the em dash is banned. This applies
to text you write *and* to text you copy: an abstract or caption that contains one
gets rewritten, not pasted through.

**Put spaces around inline math.** `body` and `overview` go through
`marked-katex-extension`, whose inline rule only fires when the opening `$`
follows whitespace and the closing `$` is followed by whitespace or `,` `.` `:`.
Glued delimiters silently ship as literal `$…$` on the page:

| markdown                | renders as             |
| ----------------------- | ---------------------- |
| `MAT$^3$ encoder`       | literal `MAT$^3$` ✗    |
| `(MAT $^3$)`            | literal `$^3$` ✗ (`)` immediately after the closing `$`) |
| `MAT $^3$ encoder`      | KaTeX ✓                |
| `below $\eta$, the …`   | KaTeX ✓                |

So write `an encoder named MAT $^3$ is trained`, not `an encoder (MAT$^3$)`. When
a space would read wrong and you can't reword, use the HTML form
`MAT<sup>3</sup>`, which the markdown passes through untouched. After a build,
`grep -o '\$[^$]\{1,40\}\$' build/index.html` should come back empty; anything it
prints is math that failed to parse.

**Centre every image.** Give each `<img>` the classes the template's own image
renderer uses, or a figure narrower than the container sits flush left:

```html
<img src="method.png" class="uk-align-center uk-responsive-width" alt="" />
```

#### Body structure

Replace the demo `body` sections with real content. A paper page typically wants
an Overview, a Method section (with the method figure), and a Results section
(with the converted table). Match the reference layout at
`https://omron-sinicx.github.io/mabr/` (Overview → Video → Method → Results):

```yaml
body:
  - title: Method
    text: |
      <one or two paragraphs summarizing the approach, in your words>

      <img src="method.png" class="uk-align-center uk-responsive-width" alt="" />
      <span class="uk-text-meta">Figure N: <the figure's caption></span>
  - title: Results
    text: |
      <a sentence framing the main result>

      #### <Table caption, shortened>
      <paste tables[i].html from the JSON here, indented to the block scalar>
```

**Show the headline tables, not every table.** A project page is not the paper:
include the main comparison against baselines and the one table that carries the
paper's second claim (a generalization or robustness result). Leave out offline
diagnostics, dataset statistics, and hyperparameter tables, however cleanly the
script converted them — they cost the reader more than they tell. Two or three
tables is a full Results section; if a table needs a paragraph of setup to make
sense, it belongs in the paper.

**Always write tables as HTML, never as a markdown table.** `body[].text` goes
through `marked`, so a markdown table would render — but it can't carry
`colspan`, group headers, or the row highlight, and it comes out visually
unrelated to the rest of the page. Paste the script's `uk-table` markup verbatim,
and hand-write the same structure for a table the script couldn't read.

**Mark your own row with `class="uk-active"`.** The theme sets
`$table-row-active-background` for exactly this, so the row the reader should
land on gets a tinted background:

```html
<tr class="uk-active"><td><b>PHASE (Ours)</b></td><td>18/20</td>…</tr>
```

One row per table — your method. Keep the `<b>` bold on the winning numbers
(that's the paper's own emphasis); the highlight is a separate, additional cue
saying "this is us". UIkit only styles `tr.uk-active` inside `<tbody>`, so it does
nothing on a `<thead>` row or an individual `<td>`: when your method is a *column*
rather than a row (an ablation laid out sideways), leave it bold and skip the
highlight.

Figures are referenced as `<img src="method.png" />` (files resolve from
`public/`), captions use `<span class="uk-text-meta">`, and tables use the
`uk-table` HTML the script produced — paste it verbatim. Keep the `|`
block-scalar indentation consistent or the YAML won't parse.

### 6. Verify — and let the user see it

```bash
pixi run uv run --with pyyaml python -c "import yaml,sys; yaml.safe_load(open('template.yaml')); print('yaml ok')"
ls -la public/ | grep -E 'teaser|method'
grep -o '\$[^$]\{1,40\}\$' build/index.html   # after a build: empty = all math parsed
grep -rn 'your-repository-name' template.yaml # must print nothing
```

Then start the site so the user can look at the page instead of reading YAML.
Run it in the background and hand them the URL:

```bash
pixi run preview   # builds, then serves the built site (vite preview)
```

`preview` is the honest check because it builds first — a YAML or markup mistake
fails the build rather than showing up as a blank section. Use `pixi run dev`
instead when you expect to keep editing and want hot reload. Either way, report
the localhost URL (and don't leave a server running once the user is done with
it).

### 7. Hand over a human checklist

Finish every run with two things: a short note of what you filled and which
figures you chose (and why), then **a checklist of what a human still has to
decide or verify**. Print it as real markdown checkboxes so it can be pasted into
a PR description, and fill in the specifics — say which authors have no homepage,
which resource fields are empty, not "check the authors":

```markdown
- [ ] **Author order and affiliation numbers** match the paper
- [ ] **Author notes** (`meta:`) and the `*`/`†` on each name are right: <what you wrote>
- [ ] **`position:`** for <authors with none> (never guessed)
- [ ] **Homepages** — filled for <n> authors, missing for <names>
- [ ] **OGP** — `image:` / `url:` use `<repo-name>`; share the URL once deployed and
      confirm the card shows the teaser
- [ ] **`resources`** — empty: <poster, video, blog, demo, huggingface…>; `code` is
      <url or "unreleased">
- [ ] **`conference` and the bibtex venue** — <venue, or "undecided">
- [ ] **`contact_ids`** — corresponding author is index <n>; change if that's wrong
- [ ] **Table numbers** read back against the paper (a wrong number here is worse
      than no table)
- [ ] **Teaser and method figures** are the ones you'd have picked
- [ ] **Relevant Projects** — the demo cards at the bottom are still the template's
      placeholders; replace or delete them
- [ ] **Draft caveat** — the numbers came from an unpublished draft and may change
      (drop this line for a camera-ready or an arXiv version)
```

Drop the lines that don't apply — a checklist of things that are already fine
teaches the reader to skim it. Anything you *did* resolve stays out of the list
and goes in the note above it.

## Table conversion notes

Both modes emit the template's `uk-table` markup (overflow wrapper,
small/divider classes, `<thead>`/`<tbody>`, `<b>` for bold cells, `colspan`
preserved, group headers spanning their `\cmidrule`). What to watch for:

- **arXiv**: math comes from the TeX annotation, so `x^{2}` becomes `x<sup>2</sup>`
  instead of duplicated MathML text. Deeply nested multirow headers can still
  come out wrong — compare against the paper's HTML table and fix cells by hand.
- **PDF**: the grid is read from the rules and word positions, which is accurate
  for booktabs-style tables but has no notion of markup. Expect to hand-clean
  citation brackets in row labels (`Retrieval-Full [38]` → `Retrieval-Full`) and
  superscripts that came through flat (`MAT3` → `MAT<sup>3</sup>`). Highlighting
  survives only as bold, so colour-coded best/second-best distinctions collapse.
- A table whose caption was found but whose grid couldn't be read comes back with
  `html: null` and a `note` — transcribe that one by hand, following the HTML
  table example already in `template.yaml`.

Always read the numbers back against the paper before publishing. A wrong number
on a project page is worse than no table.

## Robustness notes

- **Versioned ids**: `2312.02008v1` and `2312.02008` both work.
- **No HTML render**: old or opted-out papers may lack `arxiv.org/html/<id>`
  (the script still returns metadata + bibtex; figures/tables come back empty).
  Fall back to `--pdf https://arxiv.org/pdf/<id>`, which now gets you figures and
  tables too.
- **Unusual PDF layouts**: caption detection keys on `Fig. N:` / `Figure N.` /
  `TABLE N:` at the start of a text block. A paper that captions differently, or
  a scanned/image-only PDF with no text layer, yields no `F*` entries — fall back
  to `P*`/`PAGE1` for images and transcribe tables by hand.
- **`--zoom`** controls PDF clip resolution (default 3 ≈ 216 dpi). Raise it for a
  teaser that will be displayed large; lower it if files get too heavy.
- **Idempotent**: re-running save mode overwrites `teaser.*`/`method.*`.
