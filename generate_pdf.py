#!/usr/bin/env python3
"""
Generuje prospekt_karpacz.pdf bezpośrednio z prospekt.html (przez WeasyPrint).
Wygląd identyczny z wydrukiem przeglądarki.
Użycie: python3 generate_pdf.py
"""

import re
import sys
from pathlib import Path

try:
    from weasyprint import HTML, CSS
except ImportError:
    print("Brak weasyprint. Zainstaluj: pip3 install weasyprint")
    sys.exit(1)

src = Path(__file__).parent / "prospekt.html"
dst = Path(__file__).parent / "prospekt_karpacz.pdf"

html_text = src.read_text(encoding="utf-8")

# Usuń Google Fonts (brak internetu) i podmień na lokalne odpowiedniki
html_text = re.sub(
    r'<link[^>]*fonts\.googleapis\.com[^>]*>',
    '',
    html_text
)
html_text = re.sub(
    r'<link[^>]*fonts\.gstatic\.com[^>]*>',
    '',
    html_text
)

# Zastąp czcionki lokalnymi odpowiednikami
font_override = """
<style>
  /* Zastępniki Google Fonts — lokalne fonty systemowe */
  :root {
    --serif: 'Liberation Serif', 'DejaVu Serif', 'Bitstream Charter', Georgia, serif;
    --sans:  'Liberation Sans', 'DejaVu Sans', Arial, sans-serif;
  }
  body { font-family: var(--sans) !important; }
  .hero-name, .section-num, .section-title,
  .trail-name, .attr-name, .rest-name,
  .tips-title, .info-box-title, .footer-left {
    font-family: var(--serif) !important;
  }
</style>
"""

html_text = html_text.replace("</head>", font_override + "</head>")

# WeasyPrint używa @media print automatycznie przy generowaniu PDF
html_obj = HTML(string=html_text, base_url=str(src.parent))
html_obj.write_pdf(str(dst))

print(f"✓ Zapisano: {dst}")
