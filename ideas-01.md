# Ideas & Wnioski — fryzjerformen.pl
> Notatki z sesji analitycznej — kwiecień 2026

---

## 1. Analiza obecnej strony (WordPress)

### Krytyczne błędy techniczne
- **URL-e ze zniekształconymi polskimi znakami** — CMS usuwa litery zamiast transliterować
  - `/blog/fryzury-mskie-ktre-rzdz/` zamiast `/blog/fryzury-meskie-ktore-rzadza/`
  - Naprawa: skonfigurować WordPress (Yoast SEO) lub przepisać stronę
- **Duplikaty URL** — ta sama treść pod trzema adresami:
  - `/blog/artykul.html`
  - `/blog/artykul/`
  - `/?url=blog/artykul`
  - Naprawa: canonical tagi + przekierowania 301
- **Niespójne adresy salonu** — dwa różne adresy w wynikach Google (Local SEO problem)
- **Niespójna nazwa marki** — `FORMEN` vs `FOR MEN` — wybrać jedną i trzymać się jej

### Priorytety naprawy WordPress (jeśli zostaje)
1. Skonfigurować transliterację URL (ą→a, ę→e, ó→o, ś→s, ł→l, ź/ż→z, ć→c)
2. Canonical tagi dla duplikatów
3. Ujednolicić adres i nazwę we wszystkich miejscach
4. Zainstalować Yoast SEO lub Rank Math
5. Zgłosić sitemap w Google Search Console

---

## 2. SEO i Google AI Overview

### Jak pisać treści pod AI Overview (2026)
- **Answer First** — pierwsza odpowiedź od razu, bez wstępów
- **Nagłówki jako pytania** (H2/H3) — `"Ile kosztuje fade w Kaliszu?"`
- **Format** — listy punktowane, tabele, definicje na początku akapitu
- **FAQ na końcu każdego artykułu** — AI Overview to cytuje najchętniej
- **Schema Markup** — FAQPage, HowTo, LocalBusiness, Article
- **E-E-A-T** — artykuł podpisany imieniem barbera z doświadczeniem
- **Lokalne dane** — `"U nas w Kaliszu klienci najczęściej proszą o..."`

### Dodatkowe kanały dla AI Overview
- **Google Business Profile** — regularne zdjęcia, odpowiedzi na opinie, Q&A
- **YouTube** — 25% cytowań AI Overview pochodzi z YouTube
  - Pomysły: "Jak wygląda zabieg fade", "3 fryzury do każdego"
- **Opinie Google** — minimum 2-3 nowe miesięcznie (QR kod przy kasie)

### Narzędzia do zbierania pytań
- Google Autocomplete (darmowe, bez klucza API)
- Google "Ludzie pytają też o" (PAA)
- AnswerThePublic, AlsoAsked
- Google Search Console (najlepsze — realne dane)
- **Skrypt `google_questions.py`** — napisany w tej sesji, pobiera pytania automatycznie

---

## 3. Nowa strona — stack technologiczny

### Decyzja: rezygnacja z WordPress na rzecz własnego rozwiązania

#### Stack
```
Astro          → strona publiczna (główna, cennik, galeria, blog)
               → statyczne pliki HTML, błyskawiczne ładowanie, idealne SEO
               → Islands Architecture — JS tylko tam gdzie potrzeba

Node.js/Express → API backend (rezerwacje, statystyki, autoryzacja)

PostgreSQL      → baza danych (wizyty, klienci, statystyki, blog)

PWA             → panel wewnętrzny (dashboard, rezerwacje, karta lojalnościowa)
               → JWT autoryzacja
               → instalacja na telefonie bez App Store

n8n             → automatyzacja (przypomnienia SMS, blog autopilot, opinie)

Hosting: MyDevil.net → wszystko w Polsce
```

#### Dlaczego Astro
- Generuje gotowe pliki HTML przed wdrożeniem (nie w locie jak WordPress)
- 10-20x szybszy od WordPress
- Idealne Core Web Vitals z automatu
- Artykuły bloga w Markdown (plikach tekstowych)
- Każdy komponent ładuje JS tylko gdy potrzeba (Partial Hydration)

---

## 4. Hosting — MyDevil.net

- **n8n działa na MyDevil bez VPS** — przez Node.js + `forever` + proxy domenowe
- Plan ~200 zł/rok wystarczy na stronę statyczną
- Do n8n + PWA + POS lepszy wyższy plan lub VPS (Mikrus ~72 zł/rok)
- Można przejść na wyższy plan w trakcie — dopłata proporcjonalna
- Zmiana planu natychmiastowa, dane bez zmian

### Instalacja n8n na MyDevil
```bash
npm install -g n8n forever
devil www add n8n.domena.pl proxy https://localhost 5678
```

---

## 5. n8n — automatyzacje dla fryzjerformen.pl

### Gotowe do wdrożenia przepływy
1. **Blog autopilot** — google_questions.py → Claude API → szkic artykułu → WordPress/Astro
2. **Przypomnienia SMS** — dzień przed wizytą, przez SMSAPI.pl (~0.09 zł/SMS)
3. **Monitoring opinii Google** — nowa opinia → powiadomienie Telegram → szkic odpowiedzi
4. **Social media** — nowy artykuł → 3 wersje posta → Buffer/Meta
5. **Raport tygodniowy** — pozycje Google, nowe wizyty, przychód → email PDF

---

## 6. Własne statystyki (zamiast Google Analytics)

### Architektura
- Skrypt JS na stronie → `POST /api/track` → PostgreSQL
- Hashowane IP (SHA256) — zgodne z RODO, bez banera cookies
- Filtrowanie botów (Googlebot, AhrefsBot, GPTBot, ClaudeBot...)
- Osobna tabela `bot_visits` — wiadomo kiedy i jak Google skanuje stronę

### Tabele
```sql
visits      -- prawdziwi użytkownicy
bot_visits  -- crawlery i roboty
```

---

## 7. PWA — panel wewnętrzny

### Funkcje
- Dashboard właściciela (wizyty dziś, przychód, wolne terminy)
- System rezerwacji z kalendarzem
- Karta lojalnościowa (10 wizyt = 1 gratis)
- Historia wizyt klienta ze zdjęciami fryzur
- Push notyfikacje (bez SMS, darmowe)
- Autoryzacja JWT z rolami (barber / admin)

### Autoryzacja
- Hasła przez bcrypt (nigdy plain text)
- Token JWT ważny 8 godzin
- Każdy endpoint API sprawdza token
- Role: `barber` i `admin` — różny dostęp do danych

---

## 8. System rezerwacji

### Problem podwójnej rezerwacji (Booksy + własny system)
- **Rozwiązanie:** jeden kalendarz jako źródło prawdy
- Synchronizacja przez webhook Booksy → własna baza
- PostgreSQL `FOR UPDATE` — zabezpieczenie przed race condition

### Strategia fazowa
```
Faza 1 (teraz):
  Booksy z linkiem bezprowizyjnym → zero prowizji Boost
  Przycisk na stronie → link bezprowizyjny → klient rezerwuje w Booksy

Faza 2 (3-6 miesięcy):
  Własny kalendarz w PWA jako główny
  Booksy tylko dla nowych klientów (ograniczone sloty)
  Synchronizacja dwukierunkowa

Faza 3 (docelowo):
  Własny system 100%
  Booksy tylko jako wizytówka/katalog
  Oszczędność: 200-400 zł/mc subskrypcja
```

---

## 9. Booksy — jak minimalizować koszty

### Prowizja Boost — fakty
- **45% netto** od ceny pierwszej wizyty nowego klienta (nie 50%)
- Minimum: 25 zł netto
- Maksimum: 250 zł netto
- Tylko za **pierwszą wizytę** — kolejne bez prowizji
- Boost jest **opcjonalny** — można wyłączyć
- Brak prowizji gdy klient nie przyszedł (no-show)

### 8 bezprowizyjnych metod (oficjalne)
1. Link bezprowizyjny (najważniejszy)
2. Kod QR
3. Przycisk "Zarezerwuj" na Instagramie (przez własny link)
4. Przycisk "Zarezerwuj" na Facebooku (przez własny link)
5. Integracja z Google Business Profile
6. Ręczne dodanie klienta do bazy przed wizytą
7. Import klientów CSV
8. Funkcja polecenia w aplikacji

### Kluczowy wniosek
> Klient który przyszedł przez Twoją stronę / Google / social
> i zarezerwował przez link bezprowizyjny = zero prowizji Boost
> niezależnie czy był w bazie czy nie

### Do zrobienia natychmiast
- [ ] Pobrać link bezprowizyjny z panelu Booksy
- [ ] Wkleić go jako cel przycisku "Umów wizytę" na stronie
- [ ] Ustawić go w Google Business Profile
- [ ] Ustawić w bio Instagram i Facebook
- [ ] Wydrukować QR kod przy kasie
- [ ] Importować bazę stałych klientów (CSV) do Booksy

---

## 10. Booksy API

- API w fazie **alpha** — niestabilne, słaba dokumentacja
- Znane endpointy: GET/POST `/business/{id}/appointment/`
- Brak pewności co do endpointu dodawania klientów
- **Nie budować krytycznej logiki na tym API** — może się zmienić
- Każdy barber ma osobny link profilu — można to wykorzystać zamiast parametrów URL
- Warto sprawdzić empirycznie URL po przejściu na profil konkretnego barbera

---

## 11. Kolejność działań (od najpilniejszego)

### Natychmiast (bez programowania)
1. Pobrać link bezprowizyjny Booksy i wkleić wszędzie
2. Ujednolicić adres i nazwę marki
3. Zaimportować klientów do Booksy (CSV)
4. QR kod przy kasie do opinii Google

### Krótkoterminowo (1-4 tygodnie)
5. Przepisać stronę w Astro (lub naprawić WordPress)
6. Blog w formacie Answer First + FAQ
7. Schema Markup przez Yoast/Rank Math lub własny kod
8. Google Search Console — zgłosić sitemap

### Średnioterminowo (1-3 miesiące)
9. Własne statystyki (PostgreSQL + JS tracker)
10. n8n na MyDevil — automatyzacje
11. PWA z dashboardem właściciela
12. System rezerwacji własny (z SMS przez SMSAPI.pl)

### Długoterminowo (3-6 miesięcy)
13. Karta lojalnościowa w PWA
14. YouTube — pierwsze filmy
15. Wyłączyć Booksy Boost, zostaje tylko jako katalog

---

## 12. Pliki z tej sesji

| Plik | Opis |
|---|---|
| `google_questions.py` | Skrypt pobierający pytania z Google Autocomplete |
| `pytania_fryzjer.csv` | Przykładowe pytania (tryb demo) |
| `pytania_fryzjer.json` | Przykładowe pytania (tryb demo) |
| `ideas-01.md` | Ten plik — wnioski z sesji |
