# Dodaj atrakcję / szlak / restaurację

Dodaj nowy element do jednej z sekcji prospektu w pliku `generate_prospekt.py`.

Użytkownik poda: typ sekcji i dane nowego elementu (lub poprosi o sugestię).

## Instrukcja

1. Odczytaj `generate_prospekt.py` i znajdź odpowiednią listę słowników:
   - Szlak → lista `TRAILS` (klucze: `name`, `meta`, `badge`, `desc`, `badge_color`)
   - Atrakcja → lista `ATTRACTIONS` (klucze: `name`, `addr`, `desc`, `qr_url`)
   - Restauracja → lista `RESTAURANTS` (klucze: `name`, `type`, `addr`, `desc`, `qr_url`)
   - Wskazówka → lista `TIPS` (tupla: `("Tytuł", "Opis")`)

2. Zachowaj dokładnie tę samą strukturę kluczy co istniejące elementy w liście.

3. Dla `qr_url` użyj formatu: `https://maps.google.com/?q=NAZWA+MIEJSCA+Karpacz`

4. Po dodaniu uruchom `python3 generate_prospekt.py` żeby zweryfikować brak błędów.

## Żądanie użytkownika

$ARGUMENTS
