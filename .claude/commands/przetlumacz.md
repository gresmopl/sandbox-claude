# Przetłumacz prospekt

Przetłumacz wszystkie teksty w sekcjach danych (`TRAILS`, `ATTRACTIONS`, `RESTAURANTS`, `TIPS`, `HOTEL_ADDR`, nagłówki sekcji) na wskazany język.

## Instrukcja

1. Odczytaj `generate_prospekt.py`
2. Przetłumacz tylko wartości tekstowe w listach danych i stałych – **nie modyfikuj** logiki, nazw zmiennych, nazw kluczy słowników ani nazw własnych (np. "Śnieżka", "Karpacz", "Wang")
3. Przetłumacz też:
   - stałą `HOTEL_ADDR` (ulica, miasto)
   - argumenty tekstowe w wywołaniach `add_heading_bar(...)` (tytuły sekcji)
   - tekst w stopce (argument `r_f.add_run(...)`)
4. Zachowaj wszystkie emoji
5. Zapisz zmiany i uruchom `python3 generate_prospekt.py` żeby potwierdzić brak błędów

## Docelowy język

$ARGUMENTS
