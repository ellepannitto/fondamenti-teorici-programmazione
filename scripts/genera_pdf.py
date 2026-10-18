#!/usr/bin/env python3
"""Genera i PDF del testo delle esercitazioni a partire dagli HTML (richiede Google Chrome)."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


# Stile per la stampa: sfondo bianco, codice chiaro con testo scuro, poco inchiostro
CSS_STAMPA = """
@page { margin: 15mm; }
@media print {
  body { background: #fff; color: #000; font-size: 11pt; line-height: 1.45; }
  .page { max-width: none; padding: 0; }
  h1, h2, h3, h4 { color: #000; break-after: avoid; }
  h2 { border-top: 1px solid #999; }
  pre { background: #fff; color: #000; border: 1px solid #999; border-radius: 4px;
        padding: 0.5rem 0.7rem; font-size: 9.5pt; white-space: pre-wrap; word-break: break-word;
        break-inside: avoid; }
  pre code { color: #000; background: none; }
  p code, li code, td code, th code, blockquote code { background: #eee; color: #000; }
  table { background: #fff; border-radius: 0; break-inside: avoid; }
  th, td { border-color: #999; }
  th { background: #eee; }
  blockquote { background: #fff; color: #000; border-color: #999; }
  details { background: #fff; border-color: #999; border-radius: 4px; }
  summary { background: #eee; }
  a, a.ex-id { color: #000; text-decoration: none; background: none; border: 0; }
  img { border-radius: 0; break-inside: avoid; }
}
"""


def stampa(html: Path, pdf: Path, apri_soluzioni: bool) -> None:
    # copia temporanea (nella stessa cartella, per le immagini relative) con lo stile di stampa
    testo = html.read_text().replace("</style>", CSS_STAMPA + "</style>", 1)
    # la sezione "Come si lavora" riguarda la lezione in aula: non serve nel PDF
    testo = re.sub(r'<h2 id="come-si-lavora">.*?(?=<h2 )', "", testo, count=1, flags=re.S)
    if apri_soluzioni:
        # le soluzioni sono in <details> chiusi: in stampa resterebbero nascoste
        testo = testo.replace("<details>", "<details open>")
    tmp = html.with_name(html.stem + ".tmp-print.html")
    tmp.write_text(testo)
    sorgente = tmp
    try:
        subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
             f"--print-to-pdf={pdf}", sorgente.resolve().as_uri()],
            check=True, capture_output=True,
        )
    finally:
        tmp.unlink(missing_ok=True)
    print(f"Generato {pdf.relative_to(ROOT)}")


def main() -> None:
    for html in sorted(ROOT.glob("esercitazione-*/esercitazione-*.html")):
        if html.name.endswith(".slides.html") or ".tmp-print" in html.name:
            continue
        # esercitazione 4: per ora solo la versione senza soluzioni
        if html.stem == "esercitazione-4":
            continue
        stampa(html, html.with_suffix(".pdf"), apri_soluzioni="senza-soluzioni" not in html.name)


if __name__ == "__main__":
    sys.exit(main())
