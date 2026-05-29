---
trigger: always_on
---

# Zasady tworzenia notatek Obsidian dla skryptu obsidian_to_latex

Aby wygenerować jak najbardziej estetyczny, spójny i poprawny technicznie dokument PDF za pomocą skryptu `obsidian_to_latex.py`, stosuj się do poniższych wytycznych podczas pisania notatek w Obsidianie.

---

## 1. Struktura folderów i plików (Hierarchia dokumentu)

Skrypt mapuje strukturę plików bezpośrednio na poziomy sekcji w LaTeX.

* **Sekcje główne (`\section`)**:
  * Wszystkie foldery znajdujące się w katalogu głównym notatek (np. `komendy/`).
  * Wszystkie pliki `.md` znajdujące się bezpośrednio w katalogu głównym notatek.
* **Podsekcje (`\subsection`)**:
  * Pliki `.md` znajdujące się wewnątrz folderów pierwszego poziomu (np. `komendy/ps.md`).
* **Pliki wprowadzające (indeksy)**:
  * Jeśli folder (np. `komendy/`) zawiera plik o takiej samej nazwie jak ten folder (`komendy/komendy.md`) lub o nazwie `index.md`, `main.md` lub `README.md`, plik ten zostanie potraktowany jako wstęp do danej sekcji i umieszczony jako pierwszy. Tytuł tego pliku nie wygeneruje podwójnego nagłówka (skrypt scali go z nagłówkiem folderu).

---

## 2. Nagłówki wewnątrz plików Markdown

Pamiętaj, że nagłówki wewnątrz plików są automatycznie przesuwane w dół o głębokość zagnieżdżenia pliku w folderach:

* **Dla pliku w katalogu głównym** (poziom `\section`):
  * Nagłówek `# Nagłówek` staje się podsekcją (`\subsection`).
  * Nagłówek `## Nagłówek` staje się podpodsekcją (`\subsubsection`).
* **Dla pliku w podfolderze** (poziom `\subsection`):
  * Nagłówek `# Nagłówek` staje się podpodsekcją (`\subsubsection`).
  * Nagłówek `## Nagłówek` staje się akapitem (`\paragraph`).

> [!TIP]
> Najlepszą praktyką jest unikanie nagłówków H1 (`#`) wewnątrz plików w podfolderach. Staraj się zaczynać strukturę wewnątrz notatek od nagłówków `##` lub `###`.

---

## 3. Linki i powiązania między notatkami (`[[Link]]`)

Skrypt automatycznie zamienia wiki-linki z Obsidiana na klikalne odnośniki w pliku PDF.

* **Format standardowy**: `[[Nazwa Pliku]]` (np. `[[kontener]]`).
  * *Warunek*: Plik o nazwie `kontener.md` musi istnieć w strukturze notatek (w dowolnym folderze).
* **Format z własną etykietą**: `[[Nazwa Pliku|Tekst wyświetlany w PDF]]` (np. `[[kontener|kontenerów]]`).
  * Zalecany format, jeśli chcesz odmieniać słowa przez przypadki.
* **Linki zewnętrzne**: Używaj standardowego formatu Markdown: `[tekst](https://...)`.

---

## 4. Wyróżnienia i ramki informacyjne (`>`)

Aby wyróżnić ważną uwagę, wskazówkę lub definicję w estetycznej, kolorowej ramce w PDF:

* Użyj standardowego cytowania Markdown (`>`):
  
  ```markdown
  > **Wskazówka praktyczna**
  > Tutaj wpisz treść wskazówki, która ma się znaleźć w ramce.
  ```

* Skrypt automatycznie przekształci ten blok w dedykowane środowisko `infobox` z niebieskim obramowaniem i lekko błękitnym tłem.

---

## 5. Bloki kodu źródłowego

Używaj standardowych bloków kodu z potrójnymi backtickami i określeniem języka:

```markdown
\`\`\`Dockerfile
FROM node:14
WORKDIR /app
COPY . .
\`\`\`
```

* **Polskie znaki**: Możesz bez obaw używać polskich liter (np. `ą`, `ę`, `ż`) w komentarzach wewnątrz bloków kodu. Skrypt automatycznie konfiguruje LaTeX-owy pakiet `listings`, aby poprawnie je renderował.
* **Obsługiwane języki**: Skrypt najlepiej współpracuje z językami takimi jak `Dockerfile`, `bash`, `python`, `sql` oraz `javascript`.

---

## 6. Listy wypunktowane i numerowane

Tworząc listy, pamiętaj o zachowaniu standardowej składni:

* **Listy punktowane**: Zaczynaj od myślnika (`-`) lub gwiazdki (`*`) ze spacją.
* **Listy numerowane**: Zaczynaj od cyfry z kropką (`1.`, `2.`) ze spacją.

> [!IMPORTANT]
> Zawsze oddzielaj listy od zwykłego tekstu (zarówno przed, jak i po liście) **pustą linią**. Ułatwia to parserowi poprawne wykrycie końca listy i zamknięcie środowisk `\begin{itemize}` oraz `\begin{enumerate}` w LaTeX.

---

## 7. Sortowanie i prefiksy numeryczne w nazwach plików/folderów

Aby zachować logiczną kolejność rozdziałów (sekcji) i podrozdziałów (podsekcji) zarówno w drzewie plików programu Obsidian, jak i w wynikowym pliku PDF:

* **Stosuj prefiksy numeryczne**: Nazywaj foldery i pliki z wiodącym numerem, np. `01_podstawy`, `02_instalacja.md`, `03_uruchamianie.md`.
* **Automatyczne oczyszczanie nagłówków**: Skrypt `obsidian_to_latex.py` automatycznie usuwa wiodące cyfry i znaki rozdzielające (spacje, myślniki, podkreślenia) podczas generowania tytułów sekcji w LaTeX. Na przykład:
  * Katalog `01_podstawy` wygeneruje nagłówek: `\section{Podstawy}`.
  * Plik `02_instalacja.md` wygeneruje nagłówek: `\subsection{Instalacja}`.
* **Linki wewnątrznotatkowe**: Podczas linkowania do plików z prefiksami numerycznymi należy podać pełną nazwę pliku, jednak zaleca się stosowanie aliasów, aby w tekście wyświetlała się czysta nazwa:
  * Przykład: `[[02_instalacja|Instalacja Dockera]]`.
