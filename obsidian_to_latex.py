#!/usr/bin/env python3
import os
import re
import sys
import argparse
import subprocess
from pathlib import Path

# Main LaTeX template
LATEX_TEMPLATE = r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{geometry}
\geometry{a4paper, margin=2.5cm}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{listings}
\usepackage{tabularx}

% Colors
\definecolor{brandblue}{rgb}{0.12, 0.43, 0.73} % Premium blue for headings
\definecolor{bgcode}{rgb}{0.96, 0.96, 0.98}
\definecolor{bordercode}{rgb}{0.88, 0.88, 0.92}
\definecolor{darkgray}{rgb}{0.3, 0.3, 0.3}

\hypersetup{
    colorlinks=true,
    linkcolor=brandblue,
    urlcolor=brandblue,
    citecolor=brandblue
}

% Manual Polish translations of document structure
\renewcommand{\abstractname}{Streszczenie}
\renewcommand{\contentsname}{Spis treści}
\renewcommand{\lstlistingname}{Listing}

% Section styling without titlesec
\makeatletter
\renewcommand\section{\@startsection {section}{1}{\z@}%
                                   {-3.5ex \@plus -1ex \@minus -.2ex}%
                                   {2.3ex \@plus.2ex}%
                                   {\normalfont\Large\bfseries\color{brandblue}}}
\renewcommand\subsection{\@startsection{subsection}{2}{\z@}%
                                     {-3.25ex\@plus -1ex \@minus -.2ex}%
                                     {1.5ex \@plus .2ex}%
                                     {\normalfont\large\bfseries\color{brandblue}}}
\renewcommand\subsubsection{\@startsection{subsubsection}{3}{\z@}%
                                     {-3.25ex\@plus -1ex \@minus -.2ex}%
                                     {1.5ex \@plus .2ex}%
                                     {\normalfont\normalsize\bfseries\color{brandblue}}}
\makeatother

% Listings configuration
\lstdefinelanguage{Dockerfile}{
  morekeywords={FROM, RUN, CMD, LABEL, MAINTAINER, EXPOSE, ENV, ADD, COPY, ENTRYPOINT, VOLUME, USER, WORKDIR, ARG, ONBUILD, STOPSIGNAL, HEALTHCHECK, SHELL},
  morecomment=[l]{\#},
  morestring=[b]"
}

\lstdefinelanguage{JavaScript}{
  morekeywords={break, case, catch, continue, debugger, default, delete, do, else, false, finally, for, function, if, in, instanceof, new, null, return, switch, this, throw, true, try, typeof, var, void, while, with, class, const, let, export, import, extends, implements, interface, package, private, protected, public, static, yield, async, await, readonly},
  morecomment=[l]{//},
  morecomment=[s]{/*}{*/},
  morestring=[b]',
  morestring=[b]"
}


\lstset{
  basicstyle=\ttfamily\small,
  breaklines=true,
  backgroundcolor=\color{bgcode},
  frame=single,
  rulecolor=\color{bordercode},
  keywordstyle=\color{brandblue}\bfseries,
  commentstyle=\color{darkgray}\itshape,
  stringstyle=\color{green!50!black},
  showstringspaces=false,
  numbers=none,
  captionpos=b,
  extendedchars=true,
  literate={ą}{{\k{a}}}1
           {ć}{{\'{c}}}1
           {ę}{{\k{e}}}1
           {ł}{{\l{}}}1
           {ń}{{\'{n}}}1
           {ó}{{\'{o}}}1
           {ś}{{\'{s}}}1
           {ź}{{\'{z}}}1
           {ż}{{\.{z}}}1
           {Ą}{{\k{A}}}1
           {Ć}{{\'{C}}}1
           {Ę}{{\k{E}}}1
           {Ł}{{\L{}}}1
           {Ń}{{\'{N}}}1
           {Ó}{{\'{O}}}1
           {Ś}{{\'{S}}}1
           {Ź}{{\'{Z}}}1
           {Ż}{{\.{Z}}}1
}

% Custom infobox using standard LaTeX, xcolor and lrbox
\newsavebox{\infoboxsavebox}
\newenvironment{infobox}[1]{%
  \def\infoboxtitle{#1}%
  \begin{lrbox}{\infoboxsavebox}%
    \begin{minipage}{\dimexpr\textwidth-2\fboxsep-2\fboxrule\relax}%
      \textbf{\color{brandblue}\infoboxtitle}\vspace{1.5mm}\par\small
}{%
    \end{minipage}%
  \end{lrbox}%
  \medskip\noindent
  \fcolorbox{brandblue}{blue!5}{\usebox{\infoboxsavebox}}%
  \medskip
}

\title{\textbf{\color{brandblue}__TITLE__}}
\author{__AUTHOR__}
\date{__DATE__}

\begin{document}

\maketitle

\begin{abstract}
__ABSTRACT__
\end{abstract}

\tableofcontents
\newpage

__CONTENT__

\end{document}
"""

class ObsidianToLatex:
    def __init__(self, notes_dir: Path, title: str, author: str, abstract: str):
        self.notes_dir = notes_dir
        self.title = title
        self.author = author
        self.abstract = abstract
        self.section_labels = set()
        
    def clean_label_key(self, text: str) -> str:
        t = text.lower()
        t = re.sub(r'[^a-z0-9\s]+', '', t)
        t = re.sub(r'\s+', '-', t)
        return t.strip('-')

    def clean_name(self, name: str) -> str:
        import re
        name = re.sub(r'^\d+[\s_\.-]*', '', name)
        name = name.replace('-', ' ').replace('_', ' ')
        if name:
            name = name[0].upper() + name[1:]
        return name

    def split_row(self, s: str) -> list[str]:
        parts = []
        current = []
        in_link = 0
        i = 0
        while i < len(s):
            if s[i:i+2] == '[[':
                in_link += 1
                current.append('[[')
                i += 2
            elif s[i:i+2] == ']]':
                in_link = max(0, in_link - 1)
                current.append(']]')
                i += 2
            elif s[i] == '|':
                if in_link > 0:
                    current.append('|')
                else:
                    parts.append("".join(current))
                    current = []
                i += 1
            else:
                current.append(s[i])
                i += 1
        parts.append("".join(current))
        return parts

    def collect_section_labels(self):
        # Scan files and folders to build links map
        for p in self.notes_dir.rglob("*.md"):
            self.section_labels.add(self.clean_label_key(p.stem))
        for p in self.notes_dir.rglob("*"):
            if p.is_dir() and not p.name.startswith('.'):
                self.section_labels.add(self.clean_label_key(p.name))

    def escape_latex_plain(self, text: str, is_code=False) -> str:
        if is_code:
            p = text
            p = p.replace('\\', '\\textbackslash{}')
            p = p.replace('&', '\\&')
            p = p.replace('%', '\\%')
            p = p.replace('$', '\\$')
            p = p.replace('#', '\\#')
            p = p.replace('_', '\\_')
            p = p.replace('{', '\\{')
            p = p.replace('}', '\\}')
            p = p.replace('~', '\\textasciitilde{}')
            p = p.replace('^', '\\textasciicircum{}')
            return p
        else:
            p = text
            p = p.replace('\\', '\\textbackslash{}')
            p = p.replace('&', '\\&')
            p = p.replace('%', '\\%')
            p = p.replace('$', '\\$')
            p = p.replace('#', '\\#')
            p = p.replace('_', '\\_')
            p = p.replace('{', '\\{')
            p = p.replace('}', '\\}')
            p = p.replace('~', '\\textasciitilde{}')
            p = p.replace('^', '\\textasciicircum{}')
            return p

    def parse_line_inline(self, line: str) -> str:
        placeholders = {}
        placeholder_counter = 0

        def add_placeholder(val, prefix):
            nonlocal placeholder_counter
            placeholder_counter += 1
            key = f"PLACEHOLDER{prefix}{placeholder_counter}"
            placeholders[key] = val
            return key

        # 1. Inline code (do not parse inner formatting)
        def sub_inline_code(m):
            code_content = m.group(1)
            escaped_code = self.escape_latex_plain(code_content, is_code=True)
            return add_placeholder(f"\\texttt{{{escaped_code}}}", "CODE")
        
        current = re.sub(r'`([^`\n]+)`', sub_inline_code, line)

        # 2. Obsidian links [[Target]] or [[Target|Label]]
        def sub_obsidian_link(m):
            target = m.group(1).strip()
            label = m.group(2).strip() if m.group(2) else target
            
            label_key = self.clean_label_key(target)
            parsed_label = self.parse_line_inline(label)
            
            if label_key in self.section_labels:
                val = f"\\hyperref[sec:{label_key}]{{{parsed_label}}}"
            else:
                val = f"\\textbf{{{parsed_label}}}"
            return add_placeholder(val, "OBSIDIAN")

        current = re.sub(r'\[\[([^\]|\n]+)(?:\|([^\]\n]+))?\]\]', sub_obsidian_link, current)

        # 3. Standard links [Label](URL)
        def sub_std_link(m):
            label = m.group(1)
            url = m.group(2)
            parsed_label = self.parse_line_inline(label)
            escaped_url = url.replace('%', '\\%').replace('#', '\\#')
            val = f"\\href{{{escaped_url}}}{{{parsed_label}}}"
            return add_placeholder(val, "LINK")

        current = re.sub(r'\[([^\]\n]+)\]\(([^)\n]+)\)', sub_std_link, current)

        # 4. Bold **text**
        def sub_bold(m):
            content = m.group(1)
            parsed_content = self.parse_line_inline(content)
            return add_placeholder(f"\\textbf{{{parsed_content}}}", "BOLD")

        current = re.sub(r'\*\*([^*]+)\*\*', sub_bold, current)

        # 5. Italic *text* or _text_
        def sub_italic_star(m):
            content = m.group(1)
            parsed_content = self.parse_line_inline(content)
            return add_placeholder(f"\\textit{{{parsed_content}}}", "ITALIC")

        current = re.sub(r'\*([^*]+)\*', sub_italic_star, current)

        def sub_italic_under(m):
            content = m.group(1)
            parsed_content = self.parse_line_inline(content)
            return add_placeholder(f"\\textit{{{parsed_content}}}", "ITALIC")

        current = re.sub(r'_([^_]+)_', sub_italic_under, current)

        # 6. Escape plain text
        current = self.escape_latex_plain(current)

        # 7. Re-insert placeholders (in loop for nested items)
        changed = True
        while changed:
            changed = False
            for key, val in placeholders.items():
                if key in current:
                    current = current.replace(key, val)
                    changed = True

        return current

    def parse_markdown_file(self, file_path: Path, depth: int) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            return f"\\textbf{{Błąd odczytu pliku: {file_path.name}}} ({str(e)})"
            
        output_lines = []
        in_code_block = False
        in_quote = False
        in_list = None
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # 1. Code blocks
            if stripped.startswith("```"):
                if not in_code_block:
                    in_code_block = True
                    lang = stripped[3:].strip()
                    if not lang:
                        lang = "Dockerfile" if "dockerfile" in file_path.name.lower() else ""
                    
                    lang_lower = lang.lower()
                    # Mapowanie aliasów na nazwy języków znane pakietowi listings
                    LANG_ALIASES = {
                        "sql": "SQL",
                        "ts": "JavaScript", "typescript": "JavaScript",
                        "angular-ts": "JavaScript",
                        "js": "JavaScript", "javascript": "JavaScript",
                        "html": "HTML", "angular-html": "HTML", "xml": "HTML",
                        "bash": "bash", "sh": "bash",
                        "python": "Python", "py": "Python",
                        "java": "Java",
                        "c": "C", "cpp": "C++", "c++": "C++",
                        "dockerfile": "Dockerfile",
                        "php": "PHP",
                        "ruby": "Ruby",
                        "perl": "Perl",
                        "r": "R",
                    }
                    # Obsługa specjalnego przypadku: plik Dockerfile z blokiem ```sql
                    if lang_lower == "sql" and ("dockerfile" in file_path.name.lower() or "docker file" in file_path.name.lower()):
                        resolved_lang = "Dockerfile"
                    else:
                        resolved_lang = LANG_ALIASES.get(lang_lower)
                    
                    if resolved_lang:
                        output_lines.append(f"\\begin{{lstlisting}}[language={resolved_lang}]")
                    else:
                        output_lines.append("\\begin{lstlisting}")
                else:
                    in_code_block = False
                    output_lines.append("\\end{lstlisting}")
                i += 1
                continue
                
            if in_code_block:
                # Sanityzacja: zamiana emoji i problematycznych znaków Unicode
                # na odpowiedniki ASCII (listings nie obsługuje tych znaków)
                sanitized = line.rstrip('\n')
                UNICODE_REPLACEMENTS = {
                    '❌': '[X]',
                    '✅': '[OK]',
                    '✓': '[OK]',
                    '✗': '[X]',
                    '⚠': '[!]',
                    '→': '->',
                    '←': '<-',
                    '⇒': '=>',
                    '──>': '-->',
                    '──': '--',
                    '─': '-',
                    '│': '|',
                    '└': '\\-',
                    '├': '|-',
                    '…': '...',
                }
                for char, replacement in UNICODE_REPLACEMENTS.items():
                    sanitized = sanitized.replace(char, replacement)
                output_lines.append(sanitized)
                i += 1
                continue
                
            # 2. Blockquotes
            if stripped.startswith(">"):
                if in_list:
                    output_lines.append(f"\\end{{{in_list}}}")
                    in_list = None
                if not in_quote:
                    output_lines.append("\\begin{quote}")
                    in_quote = True
                quote_content = line.split(">", 1)[1].strip()
                parsed_inline = self.parse_line_inline(quote_content)
                output_lines.append(parsed_inline)
                i += 1
                continue
            elif in_quote:
                output_lines.append("\\end{quote}")
                in_quote = False
                
            # 3. Lists
            bullet_match = re.match(r'^([-*+])\s+(.*)', stripped)
            numbered_match = re.match(r'^(\d+)\.\s+(.*)', stripped)
            
            if bullet_match:
                content = bullet_match.group(2)
                parsed_inline = self.parse_line_inline(content)
                if in_list == "enumerate":
                    output_lines.append("\\end{enumerate}")
                    in_list = None
                if not in_list:
                    output_lines.append("\\begin{itemize}")
                    in_list = "itemize"
                output_lines.append(f"  \\item {parsed_inline}")
                i += 1
                continue
                
            elif numbered_match:
                content = numbered_match.group(2)
                parsed_inline = self.parse_line_inline(content)
                if in_list == "itemize":
                    output_lines.append("\\end{itemize}")
                    in_list = None
                if not in_list:
                    output_lines.append("\\begin{enumerate}")
                    in_list = "enumerate"
                output_lines.append(f"  \\item {parsed_inline}")
                i += 1
                continue
                
            elif in_list and stripped == "":
                output_lines.append("")
                i += 1
                continue
            elif in_list:
                output_lines.append(f"\\end{{{in_list}}}")
                in_list = None

            # 4. Tables Detection & Processing
            if not in_code_block and not in_quote and not in_list:
                if i + 1 < len(lines):
                    next_stripped = lines[i+1].strip()
                    if '|' in stripped and '|' in next_stripped:
                        # Check if the next line is a markdown table separator row
                        if re.match(r'^\|?\s*(:?-+:?)\s*(\|\s*(:?-+:?)\s*)+\|?$', next_stripped):
                            # Extract header parts
                            header_parts = [p.strip() for p in self.split_row(stripped)]
                            if stripped.startswith('|') or (header_parts and header_parts[0] == ''):
                                header_parts.pop(0)
                            if stripped.endswith('|') or (header_parts and header_parts[-1] == ''):
                                header_parts.pop()
                                
                            # Extract alignment from separator
                            sep_parts = [p.strip() for p in self.split_row(next_stripped)]
                            if next_stripped.startswith('|') or (sep_parts and sep_parts[0] == ''):
                                sep_parts.pop(0)
                            if next_stripped.endswith('|') or (sep_parts and sep_parts[-1] == ''):
                                sep_parts.pop()
                                
                            aligns = []
                            for part in sep_parts:
                                if part.startswith(':') and part.endswith(':'):
                                    aligns.append('c')
                                elif part.endswith(':'):
                                    aligns.append('r')
                                else:
                                    aligns.append('l')
                                    
                            # Parse subsequent rows
                            data_rows = []
                            table_index = i + 2
                            while table_index < len(lines):
                                data_line = lines[table_index]
                                data_stripped = data_line.strip()
                                if '|' not in data_stripped or data_stripped == "":
                                    break
                                if re.match(r'^\|?\s*(:?-+:?)\s*(\|\s*(:?-+:?)\s*)+\|?$', data_stripped):
                                    break
                                    
                                row_parts = [p.strip() for p in self.split_row(data_stripped)]
                                if data_stripped.startswith('|') or (row_parts and row_parts[0] == ''):
                                    row_parts.pop(0)
                                if data_stripped.endswith('|') or (row_parts and row_parts[-1] == ''):
                                    row_parts.pop()
                                    
                                data_rows.append(row_parts)
                                table_index += 1
                                
                            num_cols = len(aligns)
                            if num_cols > 0:
                                # Ostatnia kolumna dostaje typ X (zawijanie tekstu)
                                # żeby tabelka mieściła się w szerokości strony
                                tabularx_aligns = list(aligns)
                                tabularx_aligns[-1] = 'X'
                                col_spec = "|" + "|".join(tabularx_aligns) + "|"
                                output_lines.append("\\begin{center}")
                                output_lines.append(f"\\begin{{tabularx}}{{\\textwidth}}{{{col_spec}}}")
                                output_lines.append("\\hline")
                                
                                # Header
                                while len(header_parts) < num_cols:
                                    header_parts.append("")
                                header_parts = header_parts[:num_cols]
                                parsed_header = [f"\\textbf{{{self.parse_line_inline(h)}}}" for h in header_parts]
                                output_lines.append(" & ".join(parsed_header) + " \\\\ \\hline")
                                
                                # Data rows
                                for row_parts in data_rows:
                                    while len(row_parts) < num_cols:
                                        row_parts.append("")
                                    row_parts = row_parts[:num_cols]
                                    parsed_row = [self.parse_line_inline(cell) for cell in row_parts]
                                    output_lines.append(" & ".join(parsed_row) + " \\\\ \\hline")
                                    
                                output_lines.append("\\end{tabularx}")
                                output_lines.append("\\end{center}")
                                
                                i = table_index
                                continue
                
            # 5. Headers
            header_match = re.match(r'^(#+)\s+(.*)', stripped)
            if header_match:
                hashes = header_match.group(1)
                header_title = header_match.group(2).strip()
                h_level = len(hashes)
                
                # Offset level based on folder nesting
                latex_level = depth + h_level
                if latex_level == 1:
                    level_name = "subsection"
                elif latex_level == 2:
                    level_name = "subsubsection"
                else:
                    level_name = "paragraph"
                    
                parsed_title = self.parse_line_inline(header_title)
                label_key = self.clean_label_key(header_title)
                output_lines.append(f"\\{level_name}{{{parsed_title}}}\\label{{sec:{label_key}}}")
                i += 1
                continue
                
            # 6. Regular Lines
            parsed_inline = self.parse_line_inline(line.rstrip('\n'))
            output_lines.append(parsed_inline)
            i += 1
            
        # Cleanups
        if in_code_block:
            output_lines.append("\\end{lstlisting}")
        if in_quote:
            output_lines.append("\\end{quote}")
        if in_list:
            output_lines.append(f"\\end{{{in_list}}}")
            
        return "\n".join(output_lines)

    def sort_dir_contents(self, path: Path):
        items = []
        for p in path.iterdir():
            if p.name.startswith('.'):
                continue
            if p.is_dir() or p.suffix == '.md':
                items.append(p)
                
        parent_name = path.name.lower()
        
        def sort_key(item: Path):
            stem_lower = item.stem.lower()
            
            is_index = (
                stem_lower == parent_name or
                stem_lower == "index" or
                stem_lower == "readme" or
                stem_lower == "main" or
                stem_lower == self.notes_dir.name.lower() or
                stem_lower == self.notes_dir.parent.name.lower()
            )
            
            if is_index and item.is_file():
                return (0, stem_lower)
            elif item.is_file():
                return (1, stem_lower)
            else:
                return (2, stem_lower)
                
        return sorted(items, key=sort_key)

    def process_node(self, path: Path, depth: int, is_root: bool = False) -> str:
        output = []
        
        if path.is_file():
            # Process single markdown file
            # Write a heading for the file unless it's the index file of the root
            is_root_index = is_root or (depth == 0 and path.stem.lower() in [self.notes_dir.name.lower(), "docker", "index"])
            
            if is_root_index:
                return ""  # Skip root index file content in LaTeX document
                
            title_level = "section" if depth == 0 else ("subsection" if depth == 1 else "subsubsection")
            clean_title = self.clean_name(path.stem)
            label_key = self.clean_label_key(path.stem)
            
            output.append(f"\\{title_level}{{{clean_title}}}\\label{{sec:{label_key}}}\n")
            file_content = self.parse_markdown_file(path, depth)
            output.append(file_content)
            output.append("\n\\newpage\n" if depth == 0 else "\n\\medskip\n")
            
        elif path.is_dir():
            # Process directory
            # 1. Check if there is an index file matching the directory name
            contents = self.sort_dir_contents(path)
            index_file = None
            for item in contents:
                if item.is_file() and item.stem.lower() in [path.name.lower(), "index", "main"]:
                    index_file = item
                    break
            
            # If no index file, output a section/subsection header for directory
            if not index_file and not is_root:
                dir_level = "section" if depth == 0 else ("subsection" if depth == 1 else "subsubsection")
                clean_title = self.clean_name(path.name)
                label_key = self.clean_label_key(path.name)
                output.append(f"\\{dir_level}{{{clean_title}}}\\label{{sec:{label_key}}}\n")
                
            # If we are root, children start at depth 0
            # If directory has index file, it will represent the directory itself at current depth,
            # and other items inside will be nested.
            next_depth = depth if is_root else (depth + 1 if not index_file else depth)
            
            # Process children
            for item in contents:
                # If this item is the index file, process it at the parent's level
                item_is_index = (item == index_file)
                item_depth = depth if item_is_index else next_depth
                
                output.append(self.process_node(item, item_depth, is_root=False))
                
        return "\n".join(output)

    def generate(self) -> str:
        self.collect_section_labels()
        # Start processing from root directory
        content = self.process_node(self.notes_dir, depth=0, is_root=True)
        
        # Format the main template
        full_doc = LATEX_TEMPLATE.replace("__TITLE__", self.title)\
                                 .replace("__AUTHOR__", self.author)\
                                 .replace("__DATE__", "\\today")\
                                 .replace("__ABSTRACT__", self.abstract)\
                                 .replace("__CONTENT__", content)
        return full_doc

def main():
    parser = argparse.ArgumentParser(description="Konwersja Obsidian Vault na LaTeX i PDF")
    parser.add_argument("notes_dir", nargs="?", default="notatkiObsidian", help="Katalog z notatkami Obsidian")
    parser.add_argument("--output-tex", default="latex/output.tex", help="Nazwa wyjsciowego pliku LaTeX (.tex)")
    parser.add_argument("--output-pdf", default="latex/output.pdf", help="Nazwa wyjsciowego pliku PDF (.pdf)")
    parser.add_argument("--title", default=None, help="Tytul dokumentu (domyslnie wywnioskowany z nazwy katalogu)")
    parser.add_argument("--author", default="Opracowane na podstawie notatek Obsidian", help="Autor")
    parser.add_argument("--abstract", default="Automatycznie wygenerowany dokument z notatek programu Obsidian.", help="Streszczenie")
    parser.add_argument("--no-pdf", action="store_true", help="Nie kompiluj do PDF")
    
    args = parser.parse_args()
    
    notes_path = Path(args.notes_dir).resolve()
    if not notes_path.exists() or not notes_path.is_dir():
        print(f"Blad: Katalog '{args.notes_dir}' nie istnieje.", file=sys.stderr)
        sys.exit(1)
        
    # Deduce title if not provided
    title = args.title
    if not title:
        folder_name = notes_path.parent.name if notes_path.name.lower() == "notatkiobsidian" else notes_path.name
        title = "Kompendium Wiedzy - " + folder_name.replace('-', ' ').replace('_', ' ').title()

    print(f"Rozpoczynanie parsowania notatek z: {notes_path}")
    converter = ObsidianToLatex(notes_path, title, args.author, args.abstract)
    latex_content = converter.generate()
    
    output_tex_path = Path(args.output_tex).resolve()
    output_tex_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_tex_path, 'w', encoding='utf-8') as f:
        f.write(latex_content)
    print(f"Zapisano plik LaTeX do: {output_tex_path}")
    
    if args.no_pdf:
        print("Pominieto kompilacje do PDF (flaga --no-pdf).")
        return
        
    # Attempt compilation
    print("Rozpoczynanie kompilacji PDF...")
    try:
        # We need to compile from the directory of the tex file to keep aux files localized
        tex_dir = output_tex_path.parent
        tex_name = output_tex_path.name
        
        # Compile twice for TOC and links
        for i in range(2):
            print(f"Kompilacja pdflatex (przebieg {i+1}/2)...")
            cmd = ["pdflatex", "-interaction=nonstopmode", tex_name]
            result = subprocess.run(cmd, cwd=tex_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
            if result.returncode != 0:
                print(f"Blad pdflatex (kod wyjsciowy {result.returncode}):")
                # Print last 20 lines of stdout for context
                lines = result.stdout.splitlines()
                for l in lines[-20:]:
                    print(l)
                sys.exit(1)
                
        # Move generated pdf if name differs from default
        default_pdf_path = output_tex_path.with_suffix(".pdf")
        final_pdf_path = Path(args.output_pdf).resolve()
        if default_pdf_path != final_pdf_path:
            final_pdf_path.parent.mkdir(parents=True, exist_ok=True)
            os.replace(default_pdf_path, final_pdf_path)
            
        print(f"Sukces! PDF zostal zapisany do: {final_pdf_path}")
        
        # Clean up LaTeX helper files
        for suffix in [".aux", ".log", ".toc", ".out"]:
            aux_file = output_tex_path.with_suffix(suffix)
            if aux_file.exists():
                aux_file.unlink()
        print("Uporzadkowano pliki pomocnicze.")
        
    except FileNotFoundError:
        print("Blad: Nie znaleziono kompilatora 'pdflatex' w systemie. Plik LaTeX zostal wygenerowany, ale kompilacja PDF sie nie powiodla.", file=sys.stderr)
    except Exception as e:
        print(f"Wystapil blad podczas kompilacji PDF: {str(e)}", file=sys.stderr)

if __name__ == "__main__":
    main()
