#!/usr/bin/env python3
"""
Generuje prospekt_karpacz.pdf bezpośrednio z prospekt.html (przez WeasyPrint).
Wygląd identyczny z wydrukiem przeglądarki. Kody QR generowane lokalnie.
Użycie: python3 generate_pdf.py
"""

import re
import sys
import io
import base64
import urllib.parse
from pathlib import Path

try:
    from weasyprint import HTML
except ImportError:
    print("Brak weasyprint. Zainstaluj: pip3 install weasyprint")
    sys.exit(1)

try:
    import qrcode
    from PIL import Image
except ImportError:
    print("Brak qrcode. Zainstaluj: pip3 install 'qrcode[pil]'")
    sys.exit(1)

src = Path(__file__).parent / "prospekt.html"
dst = Path(__file__).parent / "prospekt_karpacz.pdf"

html_text = src.read_text(encoding="utf-8")

# ── Usuń Google Fonts (brak internetu) ───────────────────────────────────────
html_text = re.sub(r'<link[^>]*fonts\.googleapis\.com[^>]*>', '', html_text)
html_text = re.sub(r'<link[^>]*fonts\.gstatic\.com[^>]*>', '', html_text)

# ── Zastąp czcionki lokalnymi odpowiednikami ─────────────────────────────────
font_override = """
<style>
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

# ── Generuj kody QR lokalnie i osadź jako base64 ─────────────────────────────
def make_qr_base64(url: str, size: int = 168) -> str:
    qr = qrcode.QRCode(box_size=4, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    img = img.resize((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

def replace_qr_src(m: re.Match) -> str:
    full_tag = m.group(0)
    src_match = re.search(r'src="([^"]*api\.qrserver\.com[^"]*)"', full_tag)
    if not src_match:
        return full_tag
    api_url = src_match.group(1)
    # Wyciągnij parametr data= z URL-a API
    parsed = urllib.parse.urlparse(api_url)
    params = urllib.parse.parse_qs(parsed.query)
    data_url = params.get("data", [None])[0]
    size_str = params.get("size", ["168x168"])[0]
    size = int(size_str.split("x")[0])
    if not data_url:
        return full_tag
    print(f"  QR: {data_url[:60]}...")
    b64 = make_qr_base64(data_url, size)
    return full_tag.replace(src_match.group(0), f'src="{b64}"')

print("Generowanie kodów QR...")
html_text = re.sub(r'<img[^>]*api\.qrserver\.com[^>]*>', replace_qr_src, html_text)

# ── Generuj PDF ───────────────────────────────────────────────────────────────
print("Generowanie PDF...")
HTML(string=html_text, base_url=str(src.parent)).write_pdf(str(dst))
print(f"✓ Zapisano: {dst}")
