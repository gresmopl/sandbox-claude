# Projekt: Generator Prospektu Pensjonatu (Karpacz)

## Co robi ten projekt
Generuje jednostronicowy prospekt PDF/DOCX dla pensjonatu w Karpaczu.
Zawiera: szlaki górskie, atrakcje turystyczne, restauracje, praktyczne wskazówki.

## Jak uruchomić

```bash
# Generuj prospekt (domyślna nazwa: "Pensjonat")
python3 generate_prospekt.py

# Generuj z nazwą hotelu
python3 generate_prospekt.py "Nazwa Pensjonatu"
```

Wynik zapisywany do: `prospekt_karpacz.docx`

## Zależności

```bash
pip install python-docx
```

Zewnętrzne API (online): `api.qrserver.com` – generowanie kodów QR do Google Maps.

## Architektura pliku generate_prospekt.py

```
Stałe kolorów (NAVY, GOLD, SLATE, WHITE, LIGHT)
    ↓
Helpery (set_cell_bg, set_cell_borders, fetch_qr, add_heading_bar, ...)
    ↓
Dane treści (TRAILS, ATTRACTIONS, RESTAURANTS, TIPS)
    ↓
Budowa dokumentu sekcja po sekcji:
  HEADER → SZLAKI → ATRAKCJE → RESTAURACJE → WSKAZÓWKI → FOOTER
    ↓
doc.save("prospekt_karpacz.docx")
```

## Konwencje kodowania

- Kolory definiuj jako stałe RGBColor na górze pliku
- Każda sekcja dokumentu oddzielona komentarzem `# ─── NAZWA ───`
- Dane treści trzymaj w listach słowników (TRAILS, ATTRACTIONS, itp.) – nie hardcoduj w logice
- QR kody generowane live przez `fetch_qr()` – timeout 8s, przy błędzie zwraca None
- Marginesy i czcionki: strona A4, marginesy 1.8/2.0 cm, font Calibri 10pt

## Pliki projektu

| Plik | Opis |
|------|------|
| `generate_prospekt.py` | Główny skrypt generatora |
| `prospekt_karpacz.docx` | Wygenerowany prospekt (output) |
| `prospekt_karpacz.pdf` | Wersja PDF (konwertowana ręcznie) |
| `prospekt.html` | Wersja HTML prospektu |
| `qr.html` | Strona z kodami QR |
| `Informacja.docx` | Dokument informacyjny źródłowy |

## Ważne

<important if="modyfikujesz dane treści">
Dane sekcji (TRAILS, ATTRACTIONS, RESTAURANTS, TIPS) to listy słowników.
Dodając nowy element zachowaj tę samą strukturę kluczy co pozostałe elementy w liście.
</important>

<important if="dodajesz nową sekcję dokumentu">
Każda sekcja powinna używać `add_heading_bar(doc, "TYTUŁ", "emoji")` jako nagłówka.
Po sekcji zawsze dodaj `doc.add_paragraph().paragraph_format.space_after = Pt(4)`.
</important>
