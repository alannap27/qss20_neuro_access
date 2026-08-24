"""Regenerate preview/preview.tex from qss20_paper.tex and build it.

The submitted paper uses the PNAS document class (pnas-new.cls), which is not in
a plain TeX Live install; it lives in the PNAS Overleaf template. The body is
therefore written once, in qss20_paper.tex, and this script wraps that same body
in a plain `article` preamble so it compiles locally. That catches LaTeX errors,
undefined references, missing figures and broken citations without Overleaf.

Run with --build to compile as well, which is the only way to know the
bibliography actually resolves:

    python3 make_preview.py --build

The preview is one-column 10pt against PNAS's one-column 9pt, so it runs roughly
a fifth longer. Treat the page count as indicative and confirm it on Overleaf.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BIB = "qss20"
PAPER = HERE / f"{BIB}_paper.tex"
PREVIEW_DIR = HERE / "preview"

PREAMBLE = r"""\documentclass[10pt]{article}
\usepackage[margin=0.95in]{geometry}
\usepackage{graphicx,booktabs,amsmath,amssymb,url,parskip,float}
\usepackage[hidelinks]{hyperref}

%% PNAS-class macros that plain article does not define. Declared here so the
%% preview compiles against exactly the same body text as the real manuscript.
\newcommand{\numberthis}{\refstepcounter{equation}\tag{\theequation}}
\newcommand{\addtabletext}[1]{\par\vspace{4pt}\footnotesize #1\par}
\newcommand{\dropcap}[1]{#1}

\title{\vspace{-2.2em}%(title)s\\[0.4em]
\large PREVIEW BUILD --- paste into the PNAS Overleaf template for the real layout}
\author{Alanna Polyak \\ \small Department of Quantitative Social Science, Dartmouth College}
\date{\today}
\begin{document}\maketitle
"""


def brace_body(text, command):
    """Return the argument of \\command{...}, matching braces properly."""
    start = text.find("\\" + command + "{")
    if start < 0:
        return ""
    i = start + len(command) + 2
    depth, out = 1, []
    while i < len(text) and depth:
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
        out.append(ch)
        i += 1
    return "".join(out).strip()


def write_preview():
    src = PAPER.read_text()
    title = brace_body(src, "title")
    abstract = brace_body(src, "abstract")
    significance = brace_body(src, "significancestatement")

    body = src[src.find("\\dropcap"):]
    for stop in ("\\acknow{", "\\showacknow", "\\bibliography{"):
        cut = body.find(stop)
        if cut > 0:
            body = body[:cut]

    # PNAS-only markup that plain article does not understand.
    body = body.replace("\\SI{", "{")
    body = body.replace("\\Endparasplit", "").replace("\\Parasplit", "")
    body = re.sub(r"\\dataavail\{.*?\}\s*$", "", body, flags=re.S)

    out = [PREAMBLE % {"title": title}]
    if abstract:
        out.append("\\begin{abstract}\n" + abstract + "\n\\end{abstract}\n")
    if significance:
        out.append("\\begin{quote}\\small\\textbf{Significance statement.} "
                   + significance + "\\end{quote}\n")
    out.append(body.rstrip())
    out.append("\n\\bibliographystyle{plain}\n\\bibliography{%s}\n\\end{document}\n" % BIB)

    PREVIEW_DIR.mkdir(exist_ok=True)
    (PREVIEW_DIR / "preview.tex").write_text("\n".join(out))

    (PREVIEW_DIR / "figures").mkdir(exist_ok=True)
    for png in (HERE / "figures").glob("*.png"):
        dst = PREVIEW_DIR / "figures" / png.name
        if dst.resolve() != png.resolve():
            shutil.copyfile(png, dst)
    for bib in HERE.glob("*.bib"):
        dst = PREVIEW_DIR / bib.name
        if dst.resolve() != bib.resolve():
            shutil.copyfile(bib, dst)
    print(f"wrote {PREVIEW_DIR / 'preview.tex'}")


def build():
    """Two LaTeX passes either side of BibTeX, then one more to settle refs."""
    def run(cmd):
        return subprocess.run(cmd, cwd=PREVIEW_DIR, capture_output=True, text=True)

    for _ in range(2):
        run(["pdflatex", "-interaction=nonstopmode", "preview.tex"])
        run(["bibtex", "preview"])
    run(["pdflatex", "-interaction=nonstopmode", "preview.tex"])

    log = (PREVIEW_DIR / "preview.log").read_text(errors="ignore")
    errors = log.count("\n! ")
    undefined = len(re.findall(r"Citation .* undefined|Reference .* undefined", log))
    print(f"latex errors: {errors}   undefined citations or references: {undefined}")
    if undefined:
        for line in log.splitlines():
            if "undefined" in line.lower():
                print("   ", line.strip())


if __name__ == "__main__":
    write_preview()
    if "--build" in sys.argv:
        build()
