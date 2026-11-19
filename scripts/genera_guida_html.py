#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import re
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GUIDES_DIR = ROOT / "guida-lezioni"
DEFAULT_SOURCE = GUIDES_DIR / "modulo-1.md"
PROGRAMMA = ROOT / "programma.md"

TIPO_LABEL = {"theory": "teoria", "exercise": "esercitazione"}


INLINE_CODE_RE = re.compile(r"`([^`]+)`")
EX_ID_RE = re.compile(r"`\[([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)\]`")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
ANCHOR_RE = re.compile(r'<a id="[^"]+"></a>')
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
DETAILS_OPEN_RE = re.compile(r"^<details>\s*$")
SUMMARY_RE = re.compile(r"^<summary>(.*)</summary>\s*$")
DETAILS_CLOSE_RE = re.compile(r"^</details>\s*$")
AFFIANCATI_OPEN_RE = re.compile(r'^<div class="affiancati">\s*$')
CORRETTA_MARK = "{corretta}"
AFFIANCATI_CLOSE_RE = re.compile(r"^</div>\s*$")


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-") or "section"


def render_inline(text: str) -> str:
    placeholders: dict[str, str] = {}

    def stash(html: str) -> str:
        key = f"@@PLACEHOLDER{len(placeholders)}@@"
        placeholders[key] = html
        return key

    text = IMAGE_RE.sub(
        lambda m: stash(
            f'<img src="{escape(m.group(2), quote=True)}" alt="{escape(m.group(1), quote=True)}"'
            + (f' title="{escape(m.group(3), quote=True)}"' if m.group(3) else "")
            + ">"
        ),
        text,
    )
    text = LINK_RE.sub(lambda m: stash(f'<a href="{escape(m.group(2), quote=True)}">{escape(m.group(1))}</a>'), text)
    text = EX_ID_RE.sub(
        lambda m: stash(
            f'<a id="{m.group(1).lower()}" class="ex-id" href="../soluzioni-esercizi.html#{m.group(1).lower()}">[{escape(m.group(1))}]</a>'
        ),
        text,
    )
    text = INLINE_CODE_RE.sub(lambda m: stash(f"<code>{escape(m.group(1))}</code>"), text)

    escaped = escape(text)
    escaped = BOLD_RE.sub(lambda m: f"<strong>{m.group(1)}</strong>", escaped)
    escaped = ITALIC_RE.sub(lambda m: f"<em>{m.group(1)}</em>", escaped)

    for key, value in placeholders.items():
        escaped = escaped.replace(escape(key), value)

    return escaped


def _list_has_ex_ids(lines: list[str], start: int) -> bool:
    for raw in lines[start:]:
        if not raw.strip():
            break
        m = re.match(r"^(\d+\.)\s+(.*)$", raw)
        if m:
            return bool(EX_ID_RE.match(m.group(2).strip()))
    return False


def parse_list(lines: list[str], start: int) -> tuple[str, int]:
    html_parts: list[str] = []
    stack: list[tuple[str, int]] = []
    exercise_list = _list_has_ex_ids(lines, start)
    i = start

    while i < len(lines):
        raw = lines[i]
        if not raw.strip():
            break

        match = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", raw)
        if not match:
            break

        spaces, marker, content = match.groups()
        level = len(spaces) // 2
        list_tag = "ol" if marker.endswith(".") else "ul"

        while stack and level < stack[-1][1]:
            html_parts.append(f"</li></{stack.pop()[0]}>")

        if not stack or level > stack[-1][1]:
            tag_class = ' class="exercise-list"' if (exercise_list and list_tag == "ol" and level == 0) else ""
            html_parts.append(f"<{list_tag}{tag_class}>")
            stack.append((list_tag, level))
        elif stack[-1][0] != list_tag:
            html_parts.append(f"</li></{stack.pop()[0]}>")
            html_parts.append(f"<{list_tag}>")
            stack.append((list_tag, level))
        else:
            html_parts.append("</li>")

        html_parts.append(f"<li>{render_inline(content.strip())}")
        i += 1

    while stack:
        html_parts.append(f"</li></{stack.pop()[0]}>")

    return "".join(html_parts), i


def parse_blockquote(lines: list[str], start: int) -> tuple[str, int]:
    chunks: list[str] = []
    i = start
    while i < len(lines) and lines[i].lstrip().startswith(">"):
        text = lines[i].lstrip()[1:].lstrip()
        chunks.append(render_inline(text))
        i += 1
    return f"<blockquote><p>{'<br>'.join(chunks)}</p></blockquote>", i


def parse_code_block(lines: list[str], start: int) -> tuple[str, int]:
    opening = lines[start].strip()
    lang = opening.removeprefix("```").strip()
    code_lines: list[str] = []
    i = start + 1
    while i < len(lines) and lines[i].strip() != "```":
        code_lines.append(lines[i])
        i += 1
    class_attr = f' class="language-{escape(lang)}"' if lang else ""
    code = escape("\n".join(code_lines))
    return f"<pre><code{class_attr}>{code}</code></pre>", min(i + 1, len(lines))


def parse_table(lines: list[str], start: int) -> tuple[str, int]:
    rows: list[list[str]] = []
    i = start
    while i < len(lines) and lines[i].strip().startswith("|"):
        row = [cell.strip().replace("\\|", "|") for cell in re.split(r"(?<!\\)\|", lines[i].strip().strip("|"))]
        rows.append(row)
        i += 1

    if len(rows) < 2:
        return f"<p>{render_inline(lines[start].strip())}</p>", start + 1

    header = rows[0]
    body = rows[2:] if re.fullmatch(r"[:\-|\s]+", lines[start + 1].strip()) else rows[1:]

    thead = "".join(f"<th>{render_inline(cell)}</th>" for cell in header)
    tbody_rows = []
    for row in body:
        corretta = bool(row) and row[0].endswith(CORRETTA_MARK)
        if corretta:
            row = [row[0][: -len(CORRETTA_MARK)].rstrip(), *row[1:]]
        cells = "".join(f"<td>{render_inline(cell)}</td>" for cell in row)
        tbody_rows.append(f'<tr class="corretta">{cells}</tr>' if corretta else f"<tr>{cells}</tr>")

    return f"<table><thead><tr>{thead}</tr></thead><tbody>{''.join(tbody_rows)}</tbody></table>", i


def parse_paragraph(lines: list[str], start: int) -> tuple[str, int]:
    parts: list[str] = []
    i = start
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped:
            break
        if (
            stripped == "---"
            or ANCHOR_RE.fullmatch(stripped)
            or stripped.startswith("#")
            or stripped.startswith("```")
            or stripped.startswith(">")
            or stripped.startswith("|")
            or re.match(r"^\s*([-*]|\d+\.)\s+", lines[i])
        ):
            break
        parts.append(stripped)
        i += 1

    return f"<p>{render_inline(' '.join(parts))}</p>", i


def parse_details(lines: list[str], start: int) -> tuple[str, int]:
    i = start + 1
    summary = "Dettagli"
    inner_lines: list[str] = []

    if i < len(lines):
        match = SUMMARY_RE.fullmatch(lines[i].strip())
        if match:
            summary = match.group(1).strip() or summary
            i += 1

    while i < len(lines) and not DETAILS_CLOSE_RE.fullmatch(lines[i].strip()):
        inner_lines.append(lines[i])
        i += 1

    inner_html = render_body("\n".join(inner_lines)) if inner_lines else ""
    return f"<details><summary>{render_inline(summary)}</summary>{inner_html}</details>", min(i + 1, len(lines))


def parse_affiancati(lines: list[str], start: int) -> tuple[str, int]:
    """Blocco `<div class="affiancati"> ... </div>`: colonne separate da una riga `|||`."""
    i = start + 1
    colonne: list[list[str]] = [[]]

    while i < len(lines) and not AFFIANCATI_CLOSE_RE.fullmatch(lines[i].strip()):
        if lines[i].strip() == "|||":
            colonne.append([])
        else:
            colonne[-1].append(lines[i])
        i += 1

    inner = "".join(f'<div class="colonna">{render_body(chr(10).join(c))}</div>' for c in colonne)
    return f'<div class="affiancati">{inner}</div>', min(i + 1, len(lines))


def render_body(text: str) -> str:
    lines = text.splitlines()
    body: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped == "---":
            body.append("<hr>")
            i += 1
            continue

        if ANCHOR_RE.fullmatch(stripped):
            body.append(stripped)
            i += 1
            continue

        if DETAILS_OPEN_RE.fullmatch(stripped):
            html, i = parse_details(lines, i)
            body.append(html)
            continue

        if AFFIANCATI_OPEN_RE.fullmatch(stripped):
            html, i = parse_affiancati(lines, i)
            body.append(html)
            continue

        if stripped.startswith("```"):
            html, i = parse_code_block(lines, i)
            body.append(html)
            continue

        if stripped.startswith("|"):
            html, i = parse_table(lines, i)
            body.append(html)
            continue

        if stripped.startswith(">"):
            html, i = parse_blockquote(lines, i)
            body.append(html)
            continue

        if re.match(r"^\s*([-*]|\d+\.)\s+", line):
            html, i = parse_list(lines, i)
            body.append(html)
            continue

        heading = HEADING_RE.match(stripped)
        if heading:
            level = len(heading.group(1))
            text = heading.group(2).strip()
            heading_id = slugify(text)
            body.append(f'<h{level} id="{heading_id}">{render_inline(text)}</h{level}>')
            i += 1
            continue

        html, i = parse_paragraph(lines, i)
        body.append(html)

    return "".join(body)


def render_document_html(title: str, body: str, asset_prefix: str = "../assets/") -> str:
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<link rel="stylesheet" href="{asset_prefix}documento.css">
</head>
<body>
<main class="page">
{body}
<footer>
<a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" target="_blank" rel="license">
<img src="https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png" alt="CC BY-NC-SA 4.0">
</a>
Ludovica Pannitto - Università di Pisa -
<a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" target="_blank">CC BY-NC-SA 4.0</a>
</footer>
</main>
</body>
</html>
"""


def first_heading(text: str, source: Path) -> str:
    heading = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), None)
    return heading or source.stem.replace("-", " ").title()


def split_slides(text: str) -> list[str]:
    lines = text.splitlines()
    slides: list[list[str]] = []
    intro_lines: list[str] = []
    current: list[str] = []
    pending_anchors: list[str] = []
    seen_first_h2 = False
    in_code_block = False

    for raw in lines:
        stripped = raw.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block

        if not in_code_block and stripped.startswith("# "):
            continue

        if ANCHOR_RE.fullmatch(stripped) and not current:
            pending_anchors.append(raw)
            continue

        if stripped.startswith("## "):
            seen_first_h2 = True
            if current:
                slides.append(current)
            current = [*pending_anchors, raw]
            pending_anchors = []
            continue

        if not seen_first_h2:
            intro_lines.append(raw)
            continue

        if pending_anchors:
            current.extend(pending_anchors)
            pending_anchors = []
        current.append(raw)

    if current:
        slides.append(current)

    rendered_slides: list[str] = []
    if any(line.strip() for line in intro_lines):
        rendered_slides.append(render_body("\n".join(intro_lines)))

    rendered_slides.extend(render_body("\n".join(slide_lines)) for slide_lines in slides)
    return rendered_slides


def load_programma_table_html(module_stem: str) -> str:
    """Return an HTML table for the module extracted from programma.md, or empty string."""
    m = re.search(r"modulo-(\d+)", module_stem)
    if not m or not PROGRAMMA.exists():
        return ""
    num = m.group(1).zfill(2)

    lines = PROGRAMMA.read_text(encoding="utf-8").splitlines()
    in_module = False
    table_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("### "):
            if in_module:
                break
            parts = [p.strip() for p in stripped.removeprefix("### ").split("|")]
            if parts and parts[0] == num:
                in_module = True
        elif in_module:
            if stripped.startswith("|"):
                table_lines.append(line)
            elif table_lines and stripped:
                break

    if not table_lines:
        return ""

    rows: list[list[str]] = []
    for line in table_lines:
        row = [cell.strip() for cell in line.strip().strip("|").split("|")]
        rows.append(row)

    if len(rows) < 2:
        return ""

    header = rows[0]
    body_rows = rows[2:] if re.fullmatch(r"[:\-|\s]+", table_lines[1].strip()) else rows[1:]

    thead = "".join(
        f"<th>{escape(cell)}</th>" for cell in header
    )
    tbody = "".join(
        "<tr>" + "".join(
            f"<td>{escape(TIPO_LABEL.get(cell, cell))}</td>" for cell in row
        ) + "</tr>"
        for row in body_rows
    )
    return f"<table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table>"


_FINE_LEZIONE_RE = re.compile(r"<h2[^>]*>\s*A fine lezione", re.IGNORECASE)


def render_slides_html(text: str, title: str, epilogue_html: str = "", asset_prefix: str = "../assets/") -> str:
    slides = split_slides(text)

    sections = [
        f"""
<section class="slide title-slide active" role="group" aria-roledescription="diapositiva" tabindex="-1">
  <div class="slide-inner">
    <p class="eyebrow">Fondamenti Teorici e Programmazione</p>
    <h1>{escape(title)}</h1>
    <p class="instructions">Freccia destra o spazio per avanzare, freccia sinistra per tornare indietro — oppure i pulsanti "Indietro" e "Avanti" in fondo alla pagina.</p>
  </div>
</section>
"""
    ]

    injected = False
    for body in slides:
        extra = ""
        if epilogue_html and not injected and _FINE_LEZIONE_RE.search(body):
            extra = epilogue_html
            injected = True
        sections.append(
            f"""
<section class="slide" role="group" aria-roledescription="diapositiva" tabindex="-1">
  <div class="slide-inner">
    {body}
    {extra}
  </div>
</section>
"""
        )

    if epilogue_html and not injected:
        sections.append(
            f"""
<section class="slide" role="group" aria-roledescription="diapositiva" tabindex="-1">
  <div class="slide-inner">
    <h2>A fine lezione</h2>
    {epilogue_html}
  </div>
</section>
"""
        )

    slide_count = len(sections)

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)} - Slides</title>
<link rel="stylesheet" href="{asset_prefix}slides.css">
</head>
<body>
<div class="deck" role="region" aria-label="Diapositive">
  {''.join(sections)}
</div>
<div class="sr-only" id="slide-announcer" aria-live="polite" aria-atomic="true"></div>
<div class="controls">
  <div class="nav">
    <button type="button" id="prev">Indietro</button>
    <button type="button" id="next">Avanti</button>
  </div>
  <div class="progress"><div class="progress-bar" id="progress"></div></div>
  <div class="counter" id="counter" aria-hidden="true">1 / {slide_count}</div>
  <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" target="_blank" rel="license" style="display:flex;align-items:center;opacity:0.6;">
    <img src="https://licensebuttons.net/l/by-nc-sa/4.0/80x15.png" alt="CC BY-NC-SA 4.0" style="height:15px;border-radius:0;margin:0;">
  </a>
</div>
<script src="{asset_prefix}slides.js"></script>
</body>
</html>
"""


def asset_prefix_for(output: Path) -> str:
    """Percorso relativo da `output` alla cartella condivisa assets/ (CSS e JS comuni)."""
    return os.path.relpath(ROOT / "assets", output.parent).replace(os.sep, "/") + "/"


def gather_sources(args: argparse.Namespace) -> list[Path]:
    if args.all:
        return sorted(GUIDES_DIR.glob("modulo-*.md"))
    if args.sources:
        return [Path(source).resolve() for source in args.sources]
    return [DEFAULT_SOURCE]


SOLUZIONI_RE = re.compile(r"<details>\s*<summary>Soluzione.*?</summary>.*?</details>[ \t]*\n*", re.DOTALL)


def rimuovi_soluzioni(text: str) -> str:
    return SOLUZIONI_RE.sub("", text)


def generate_outputs(source: Path, slides: bool, document: bool, senza_soluzioni: bool = False) -> list[Path]:
    if not source.exists():
        raise SystemExit(f"File non trovato: {source}")

    text = source.read_text(encoding="utf-8")
    suffix = ""
    if senza_soluzioni:
        text = rimuovi_soluzioni(text)
        suffix = "-senza-soluzioni"
    title = first_heading(text, source)
    outputs: list[Path] = []

    if document:
        output = source.with_name(f"{source.stem}{suffix}.html")
        html = render_document_html(title, render_body(text), asset_prefix_for(output))
        output.write_text(html, encoding="utf-8")
        outputs.append(output)

    if slides:
        epilogue = load_programma_table_html(source.stem)
        output = source.with_name(f"{source.stem}{suffix}.slides.html")
        slides_html = render_slides_html(text, title, epilogue, asset_prefix_for(output))
        output.write_text(slides_html, encoding="utf-8")
        outputs.append(output)

    return outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Genera HTML o slide HTML dai materiali Markdown in guida-lezioni.")
    parser.add_argument("sources", nargs="*", help="File Markdown sorgente. Se omesso usa guida-lezioni/modulo-1.md")
    parser.add_argument("--slides", action="store_true", help="Genera solo la versione slide standalone (.slides.html).")
    parser.add_argument("--both", action="store_true", help="Genera sia la versione documento sia la versione slide.")
    parser.add_argument("--senza-soluzioni", action="store_true", help="Omette i blocchi <details> 'Soluzione' e aggiunge il suffisso -senza-soluzioni ai file generati.")
    parser.add_argument("--all", action="store_true", help="Compila tutti i file guida-lezioni/modulo-*.md.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    document = not args.slides or args.both
    slides = args.slides or args.both

    sources = gather_sources(args)
    if not sources:
        raise SystemExit("Nessun file sorgente trovato.")

    for source in sources:
        outputs = generate_outputs(source, slides=slides, document=document, senza_soluzioni=args.senza_soluzioni)
        for output in outputs:
            print(f"Generato {output.relative_to(ROOT)} da {source.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
