#!/usr/bin/env python3
"""
Google Questions Scraper dla fryzjerformen.pl
Pobiera pytania z Google Autocomplete dla tematów fryzjerskich.
Eksportuje wyniki do CSV i JSON.

Użycie:
    python3 google_questions.py           # tryb normalny
    python3 google_questions.py --demo    # tryb demo (bez internetu)
"""

import requests
import json
import csv
import time
import sys

# ── Konfiguracja ──────────────────────────────────────────────────────────────

TEMATY = [
    "fryzura fade",
    "fryzura undercut",
    "fryzura taper",
    "fryzura mullet",
    "fryzura french crop",
    "fryzura slick back",
    "fryzura buzz cut",
    "strzyżenie brody",
    "pielęgnacja brody",
    "barber kalisz",
    "fryzjer męski kalisz",
    "fryzura do okrągłej twarzy",
    "fryzura do kwadratowej twarzy",
    "fryzura do podłużnej twarzy",
    "jak stylizować włosy mężczyzna",
    "pomada do włosów męskich",
    "włosy przetłuszczające się mężczyzna",
]

MODYFIKATORY = [
    "jak",
    "ile kosztuje",
    "co to",
    "czy",
    "kiedy",
    "dla kogo",
    "jak długo",
    "jak zrobić",
    "jak pielęgnować",
]

DELAY_SECONDS = 0.8  # przerwa między zapytaniami (nie bombarduj Google)

DEMO_DATA = {
    "fryzura fade": [
        "fryzura fade jak zrobić",
        "fryzura fade ile kosztuje",
        "fryzura fade co to jest",
        "fryzura fade do jakiej twarzy",
        "fryzura fade jak długo rośnie",
        "fryzura fade skin fade różnica",
    ],
    "strzyżenie brody": [
        "strzyżenie brody jak zrobić samemu",
        "strzyżenie brody krok po kroku",
        "strzyżenie brody nożyczkami",
        "strzyżenie brody ile kosztuje",
        "strzyżenie brody maszynką",
    ],
    "barber kalisz": [
        "barber kalisz ceny",
        "barber kalisz opinie",
        "barber kalisz podmiejska",
        "barber shop kalisz",
        "barber kalisz al wojska polskiego",
    ],
    "fryzura do okrągłej twarzy": [
        "fryzura do okrągłej twarzy mężczyzna",
        "fryzura do okrągłej twarzy kobieta",
        "fryzura do okrągłej twarzy co wyszczupla",
        "jaka fryzura do okrągłej twarzy",
    ],
    "pielęgnacja brody": [
        "pielęgnacja brody olejek",
        "pielęgnacja brody krok po kroku",
        "pielęgnacja brody produkty",
        "pielęgnacja brody jak często",
        "pielęgnacja brody w domu",
        "pielęgnacja brody balsam",
    ],
}

# ── Funkcje ───────────────────────────────────────────────────────────────────

def autocomplete(query: str, lang: str = "pl") -> list[str]:
    """Pobiera podpowiedzi z Google Autocomplete."""
    url = "https://suggestqueries.google.com/complete/search"
    params = {
        "client": "firefox",
        "hl": lang,
        "gl": "pl",
        "q": query,
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data[1] if len(data) > 1 else []
    except Exception as e:
        print(f"  [BŁĄD] {query}: {e}")
        return []


def zbierz_pytania(tematy: list[str], modyfikatory: list[str]) -> list[dict]:
    """
    Dla każdego tematu odpytuje Google z każdym modyfikatorem
    oraz bez modyfikatora. Zwraca listę unikalnych pytań z metadanymi.
    """
    wyniki = []
    seen = set()

    # zapytania: temat bez modyfikatora + temat + każdy modyfikator
    zapytania = []
    for temat in tematy:
        zapytania.append((temat, temat, ""))
        for mod in modyfikatory:
            zapytania.append((temat, f"{temat} {mod}", mod))

    total = len(zapytania)
    print(f"Łącznie zapytań do wysłania: {total}\n")

    for i, (temat, query, mod) in enumerate(zapytania, 1):
        print(f"[{i}/{total}] {query}")
        podpowiedzi = autocomplete(query)

        for p in podpowiedzi:
            if p not in seen:
                seen.add(p)
                wyniki.append({
                    "pytanie": p,
                    "temat": temat,
                    "modyfikator": mod,
                    "zrodlo": "google_autocomplete",
                })

        time.sleep(DELAY_SECONDS)

    return wyniki


def zapisz_csv(wyniki: list[dict], plik: str) -> None:
    """Zapisuje wyniki do pliku CSV."""
    if not wyniki:
        return
    with open(plik, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=wyniki[0].keys())
        writer.writeheader()
        writer.writerows(wyniki)
    print(f"\n✓ CSV zapisany: {plik} ({len(wyniki)} pytań)")


def zapisz_json(wyniki: list[dict], plik: str) -> None:
    """Zapisuje wyniki do pliku JSON."""
    with open(plik, "w", encoding="utf-8") as f:
        json.dump(wyniki, f, ensure_ascii=False, indent=2)
    print(f"✓ JSON zapisany: {plik}")


def pogrupuj_po_temacie(wyniki: list[dict]) -> dict:
    """Grupuje pytania według tematu — przydatne do podglądu."""
    grupy = {}
    for w in wyniki:
        temat = w["temat"]
        grupy.setdefault(temat, []).append(w["pytanie"])
    return grupy


def drukuj_podsumowanie(wyniki: list[dict]) -> None:
    """Wyświetla podsumowanie w konsoli."""
    grupy = pogrupuj_po_temacie(wyniki)
    print("\n" + "═" * 60)
    print(f"PODSUMOWANIE — {len(wyniki)} unikalnych pytań")
    print("═" * 60)
    for temat, pytania in grupy.items():
        print(f"\n▸ {temat.upper()} ({len(pytania)})")
        for p in pytania[:5]:  # pokaż max 5 przykładów
            print(f"   • {p}")
        if len(pytania) > 5:
            print(f"   ... i {len(pytania) - 5} więcej")


# ── Main ──────────────────────────────────────────────────────────────────────

def tryb_demo() -> list[dict]:
    """Generuje wyniki z wbudowanych danych testowych — bez internetu."""
    print("[TRYB DEMO] Używam przykładowych danych zamiast odpytywać Google.\n")
    wyniki = []
    for temat, pytania in DEMO_DATA.items():
        for p in pytania:
            wyniki.append({
                "pytanie": p,
                "temat": temat,
                "modyfikator": "",
                "zrodlo": "demo",
            })
    return wyniki


if __name__ == "__main__":
    print("=" * 60)
    print("Google Questions Scraper — fryzjerformen.pl")
    print("=" * 60 + "\n")

    demo = "--demo" in sys.argv

    if demo:
        wyniki = tryb_demo()
    else:
        wyniki = zbierz_pytania(TEMATY, MODYFIKATORY)

    zapisz_csv(wyniki, "pytania_fryzjer.csv")
    zapisz_json(wyniki, "pytania_fryzjer.json")
    drukuj_podsumowanie(wyniki)

    print("\nGotowe! Otwórz pytania_fryzjer.csv w Excelu lub Arkuszach Google.")
