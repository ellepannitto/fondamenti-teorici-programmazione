#!/usr/bin/env python3

from __future__ import annotations

import argparse
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
        row = [cell.strip() for cell in lines[i].strip().strip("|").split("|")]
        rows.append(row)
        i += 1

    if len(rows) < 2:
        return f"<p>{render_inline(lines[start].strip())}</p>", start + 1

    header = rows[0]
    body = rows[2:] if re.fullmatch(r"[:\-|\s]+", lines[start + 1].strip()) else rows[1:]

    thead = "".join(f"<th>{render_inline(cell)}</th>" for cell in header)
    tbody_rows = []
    for row in body:
        cells = "".join(f"<td>{render_inline(cell)}</td>" for cell in row)
        tbody_rows.append(f"<tr>{cells}</tr>")

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


def render_document_html(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<style>
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{ margin: 0; font-family: Georgia, "Times New Roman", serif; background: #f6f3ee; color: #1f1f1f; line-height: 1.65; }}
.page {{ max-width: 900px; margin: 0 auto; padding: 40px 20px 72px; }}
h1, h2, h3, h4 {{ font-family: "Avenir Next", "Segoe UI", Arial, sans-serif; line-height: 1.2; color: #1c2a39; }}
h1 {{ font-size: 2.1rem; margin: 0 0 1.5rem; }}
h2 {{ font-size: 1.5rem; margin: 2.5rem 0 1rem; padding-top: 0.25rem; border-top: 1px solid #d8d1c7; }}
h3 {{ font-size: 1.2rem; margin: 2rem 0 0.8rem; }}
p, ul, ol, blockquote, table, pre {{ margin: 0 0 1rem; }}
img {{ max-width: 100%; height: auto; display: block; margin: 1rem auto; border-radius: 12px; }}
ul, ol {{ padding-left: 1.4rem; }}
li {{ margin: 0.3rem 0; }}
blockquote {{ border-top: 3px solid #c97f31; border-bottom: 3px solid #c97f31; padding: 0.75rem 1.5rem; background: #fff8ef; color: #503521; text-align: center; max-width: 82%; margin-left: auto; margin-right: auto; }}
details {{ margin: 0 0 1rem; border: 1px solid #ddd5ca; border-radius: 10px; background: #fffdfa; overflow: hidden; }}
summary {{ cursor: pointer; font-weight: 600; padding: 0.8rem 1rem; background: #f3ece2; }}
details > :not(summary) {{ padding-left: 1rem; padding-right: 1rem; }}
pre {{ background: #1f2430; color: #f3f4f6; padding: 1rem; border-radius: 10px; overflow-x: auto; }}
code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.95em; }}
p code, li code, td code, th code, blockquote code {{ background: rgba(28, 42, 57, 0.08); padding: 0.08rem 0.35rem; border-radius: 4px; color: #18212d; }}
table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; }}
th, td {{ border: 1px solid #ddd5ca; padding: 0.55rem 0.7rem; vertical-align: top; text-align: left; }}
th {{ background: #efe7db; }}
hr {{ border: 0; border-top: 1px solid #d8d1c7; margin: 2rem 0; }}
a {{ color: #8b3f1d; }}
[id] {{ scroll-margin-top: 20px; }}
ol.exercise-list {{ list-style: none; padding-left: 0; }}
ol.exercise-list > li {{ display: flex; align-items: baseline; gap: 0.5em; flex-wrap: wrap; }}
a.ex-id {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.82em; font-weight: 600; background: #f3ece2; border: 1px solid #ddd5ca; color: #8b3f1d; padding: 0.05rem 0.4rem; border-radius: 5px; text-decoration: none; white-space: nowrap; flex-shrink: 0; }}
a.ex-id:hover {{ background: #e8d9c5; border-color: #c9b89e; }}
footer {{ margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #d8d1c7; font-size: 0.82rem; color: #595959; display: flex; align-items: center; gap: 0.6rem; }}
footer img {{ margin: 0; border-radius: 0; height: 22px; width: auto; display: inline; }}
@media (max-width: 700px) {{
  .page {{ padding: 24px 14px 56px; }}
  table {{ display: block; overflow-x: auto; }}
}}
</style>
</head>
<body>
<main class="page">
{body}
<footer>
<a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" target="_blank" rel="license">
<img src="https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png" alt="CC BY-NC-SA 4.0">
</a>
Ludovica Pannitto — Università degli Studi di Salerno —
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


def render_slides_html(text: str, title: str, epilogue_html: str = "") -> str:
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
<style>
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; height: 100%; overflow: hidden; }}
body {{ font-family: "Avenir Next", "Segoe UI", Arial, sans-serif; background:
radial-gradient(circle at top left, #f4ead8 0%, #efe3d0 28%, #d9d7dd 58%, #bcc9d1 100%);
color: #17212b; }}
.deck {{ position: relative; width: 100vw; height: 100vh; }}
.slide {{ display: none; width: 100vw; height: 100vh; padding: 40px; }}
.slide.active {{ display: block; }}
.slide:focus {{ outline: none; }}
.slide:focus-visible {{ outline: 3px solid #7a9aaa; outline-offset: -3px; }}
.sr-only {{
  position: absolute;
  width: 1px; height: 1px;
  padding: 0; margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}}
.slide-inner {{
  width: min(1180px, calc(100vw - 80px));
  height: calc(100vh - 110px);
  margin: 0 auto;
  overflow: auto;
  background: rgba(255,255,255,0.86);
  backdrop-filter: blur(6px);
  border: 1px solid rgba(23, 33, 43, 0.12);
  border-radius: 28px;
  box-shadow: 0 24px 80px rgba(35, 40, 46, 0.16);
  padding: 38px 46px 44px;
}}
.title-slide .slide-inner {{
  display: flex;
  flex-direction: column;
  justify-content: center;
  background:
  linear-gradient(135deg, rgba(255,255,255,0.9), rgba(250,245,238,0.86)),
  radial-gradient(circle at right top, rgba(201,127,49,0.14), transparent 35%);
}}
.eyebrow {{ text-transform: uppercase; letter-spacing: 0.18em; font-size: 0.82rem; color: #8b3f1d; margin: 0 0 1rem; }}
.instructions {{ color: #5d6770; margin-top: 1.5rem; font-size: 1rem; }}
h1, h2, h3, h4 {{ line-height: 1.08; color: #1a2834; margin: 0 0 0.8rem; }}
h1 {{ font-size: clamp(2.4rem, 4.6vw, 4.8rem); max-width: 12ch; }}
h2 {{ font-size: clamp(2rem, 3.4vw, 3.4rem); border-bottom: 2px solid rgba(139,63,29,0.2); padding-bottom: 0.5rem; margin-bottom: 1.4rem; }}
h3 {{ font-size: clamp(1.4rem, 2.2vw, 2.1rem); margin-top: 1.8rem; margin-bottom: 0.6rem; }}
p, ul, ol, blockquote, table, pre {{ margin: 0 0 1.1rem; font-size: clamp(1.08rem, 1.6vw, 1.32rem); line-height: 1.55; }}
img {{ max-width: 100%; height: auto; display: block; margin: 1rem auto; border-radius: 18px; box-shadow: 0 14px 42px rgba(35, 40, 46, 0.18); }}
ul, ol {{ padding-left: 1.35rem; }}
li {{ margin: 0.38rem 0; }}
blockquote {{ border-top: 4px solid #c97f31; border-bottom: 4px solid #c97f31; padding: 0.8rem 1.5rem; background: #fff6ea; border-radius: 14px; text-align: center; max-width: 80%; margin-left: auto; margin-right: auto; }}
details {{ margin: 0 0 1rem; border: 1px solid rgba(23, 33, 43, 0.12); border-radius: 14px; background: rgba(255,255,255,0.72); overflow: hidden; }}
summary {{ cursor: pointer; font-weight: 700; padding: 0.75rem 0.95rem; background: rgba(23, 33, 43, 0.06); }}
details > :not(summary) {{ padding-left: 0.95rem; padding-right: 0.95rem; }}
pre {{ background: #1f2430; color: #f3f4f6; padding: 1rem; border-radius: 16px; overflow-x: auto; }}
code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.92em; }}
p code, li code, td code, th code, blockquote code {{ background: rgba(23, 33, 43, 0.07); padding: 0.08rem 0.35rem; border-radius: 4px; }}
table {{ width: 100%; border-collapse: collapse; background: rgba(255,255,255,0.92); border-radius: 14px; overflow: hidden; }}
th, td {{ border: 1px solid rgba(23, 33, 43, 0.12); padding: 0.55rem 0.7rem; vertical-align: top; text-align: left; }}
th {{ background: #f2e7d7; }}
hr {{ border: 0; border-top: 1px solid rgba(23, 33, 43, 0.12); margin: 1.2rem 0; }}
a {{ color: #8b3f1d; }}
ol.exercise-list {{ list-style: none; padding-left: 0; }}
ol.exercise-list > li {{ display: flex; align-items: baseline; gap: 0.5em; flex-wrap: wrap; }}
a.ex-id {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.78em; font-weight: 600; background: rgba(139,63,29,0.1); border: 1px solid rgba(139,63,29,0.25); color: #8b3f1d; padding: 0.05rem 0.4rem; border-radius: 5px; text-decoration: none; white-space: nowrap; flex-shrink: 0; }}
a.ex-id:hover {{ background: rgba(139,63,29,0.18); }}
.controls {{
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 14px 24px 18px;
  color: #213242;
}}
.progress {{
  flex: 1;
  height: 6px;
  background: rgba(23, 33, 43, 0.12);
  border-radius: 999px;
  overflow: hidden;
}}
.progress-bar {{ height: 100%; width: 0; background: linear-gradient(90deg, #c97f31, #7a9aaa); }}
.counter {{ min-width: 70px; text-align: right; font-size: 0.95rem; }}
.nav button {{
  border: 0;
  background: rgba(255,255,255,0.82);
  color: #213242;
  border-radius: 999px;
  padding: 0.72rem 1rem;
  font-size: 1rem;
  cursor: pointer;
  box-shadow: 0 10px 30px rgba(35, 40, 46, 0.12);
}}
.nav {{ display: flex; gap: 10px; }}
@media (max-width: 820px) {{
  .slide {{ padding: 18px 14px 78px; }}
  .slide-inner {{ width: 100%; height: calc(100vh - 96px); padding: 24px 22px 30px; border-radius: 20px; }}
  p, ul, ol, blockquote, table, pre {{ font-size: 1rem; }}
}}
</style>
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
<script>
const slides = Array.from(document.querySelectorAll(".slide"));
const counter = document.getElementById("counter");
const progress = document.getElementById("progress");
const announcer = document.getElementById("slide-announcer");
let current = 0;

function slideLabel(slide, index) {{
  const heading = slide.querySelector("h1, h2, h3");
  const title = heading ? heading.textContent.trim() : "";
  const position = `Diapositiva ${{index + 1}} di ${{slides.length}}`;
  return title ? `${{position}}: ${{title}}` : position;
}}

function updateSlide(index, options) {{
  const opts = options || {{}};
  current = Math.max(0, Math.min(index, slides.length - 1));
  slides.forEach((slide, i) => slide.classList.toggle("active", i === current));
  counter.textContent = `${{current + 1}} / ${{slides.length}}`;
  progress.style.width = `${{((current + 1) / slides.length) * 100}}%`;

  const activeSlide = slides[current];
  const label = slideLabel(activeSlide, current);
  activeSlide.setAttribute("aria-label", label);
  announcer.textContent = label;

  if (opts.moveFocus) {{
    activeSlide.focus({{ preventScroll: true }});
  }}

  const anchor = activeSlide.querySelector("[id]");
  if (anchor) {{
    history.replaceState(null, "", `#${{anchor.id}}`);
  }}
}}

document.getElementById("prev").addEventListener("click", () => updateSlide(current - 1, {{ moveFocus: true }}));
document.getElementById("next").addEventListener("click", () => updateSlide(current + 1, {{ moveFocus: true }}));

document.addEventListener("keydown", (event) => {{
  if (["ArrowRight", "PageDown", " "].includes(event.key)) {{
    event.preventDefault();
    updateSlide(current + 1, {{ moveFocus: true }});
  }}
  if (["ArrowLeft", "PageUp"].includes(event.key)) {{
    event.preventDefault();
    updateSlide(current - 1, {{ moveFocus: true }});
  }}
  if (event.key === "Home") updateSlide(0, {{ moveFocus: true }});
  if (event.key === "End") updateSlide(slides.length - 1, {{ moveFocus: true }});
}});

updateSlide(0);
</script>
</body>
</html>
"""


def gather_sources(args: argparse.Namespace) -> list[Path]:
    if args.all:
        return sorted(GUIDES_DIR.glob("modulo-*.md"))
    if args.sources:
        return [Path(source).resolve() for source in args.sources]
    return [DEFAULT_SOURCE]


def generate_outputs(source: Path, slides: bool, document: bool) -> list[Path]:
    if not source.exists():
        raise SystemExit(f"File non trovato: {source}")

    text = source.read_text(encoding="utf-8")
    title = first_heading(text, source)
    outputs: list[Path] = []

    if document:
        html = render_document_html(title, render_body(text))
        output = source.with_suffix(".html")
        output.write_text(html, encoding="utf-8")
        outputs.append(output)

    if slides:
        epilogue = load_programma_table_html(source.stem)
        slides_html = render_slides_html(text, title, epilogue)
        output = source.with_name(f"{source.stem}.slides.html")
        output.write_text(slides_html, encoding="utf-8")
        outputs.append(output)

    return outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Genera HTML o slide HTML dai materiali Markdown in guida-lezioni.")
    parser.add_argument("sources", nargs="*", help="File Markdown sorgente. Se omesso usa guida-lezioni/modulo-1.md")
    parser.add_argument("--slides", action="store_true", help="Genera solo la versione slide standalone (.slides.html).")
    parser.add_argument("--both", action="store_true", help="Genera sia la versione documento sia la versione slide.")
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
        outputs = generate_outputs(source, slides=slides, document=document)
        for output in outputs:
            print(f"Generato {output.relative_to(ROOT)} da {source.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
