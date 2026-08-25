# Transcript 00: Parsing the Neurology Atlas PDF

**Script:** `code/01_parse_atlas_pdf.py`
**Paper reference:** Agentic Analysis, "Failure: silent truncation in the PDF
parser, and an over-correction"

Edited excerpt from the session log. Prompts and replies are as written; tool
output and code blocks are abridged, with cuts marked `[...]`.

---

## The task

> **Alanna:** The atlas is a PDF; Annex 1 has the country list with WHO region
> and income group. Can u parse it into a CSV

The AI wrote a parser over `pdfplumber`, extracting Annex 1 by matching
each line against the WHO region names and the four World Bank income labels.

> **AI:** Annex 1 parsed. 133 rows, which matches the count of
> participating countries stated on the annex header. Writing
> `data/raw/atlas_countries.csv`.

I accepted this at first. The row count matched the number printed on the page, which is
the check I would normally apply.

---

## What was wrong

Two country names in the Atlas wrap across two lines in the PDF. The parser took
only the first line, so the table contained:

```
The former Yugoslav Republic of
United Republic of Tanzania
```

The first is not a country name. It is the first line of "The former Yugoslav
Republic of Macedonia."

The row count was still 133. Nothing about the parse looked wrong. The
failure was invisible to the only check either of us had applied, because the
count of rows and the correctness of their contents are different properties.

I found it reading the output CSV, not from any error.

> **Alanna:** The country column has "The former Yugoslav Republic of" as a
> country, that's half a name.

---

## The first fix, which over-corrected

The AI's repair appended any short line that followed to the country name.

> **AI:** Fixed: the parser now joins a continuation line when the next
> line is short enough not to be a new record.

Diagnostic output comparing the old parse against the new one:

```
shapes (133, 3) (133, 3)
old-only: ['Austria', 'El Salvador', 'Paraguay',
           'The former Yugoslav Republic of', 'Timor-Leste',
           'United Republic of Tanzania']
new-only: ['Austria Grisold, Regina Katzenschlager',
           'El Salvador Mauricio Ramirez Zamora',
           'Paraguay Sady Galeano',
           'The former Yugoslav Republic of Macedonia',
           'Timor-Leste Guterres',
           'United Republic of Tanzania [...]']
```

The two genuine truncations were repaired. Four correct country names were
corrupted in exchange, because the Atlas prints a *Contributor* column whose
values also wrap, and the rule could not tell a wrapped country name from a
wrapped contributor name. Again the shape stayed `(133, 3)`.

---

## The rule

The distinguishing property is not line length. A wrapped country name is cut
mid-phrase and therefore ends in a function word — "of", "the", "and". A
contributor name never does.

```python
CONTINUES = ("of", "the", "and", "de", "du", "des", "República", "Republic")

def _joins_next(line):
    """A country name wrapped by the typesetter ends mid-phrase."""
    return line.rstrip().split()[-1] in CONTINUES
```

I then asked for assertions so the parse could not fail again:

> **Alanna:** Add checks against actual values I can read off the page so if it
> breaks again I know.

Eight assertions now guard the parse: the participating-country count, the
global median, the four income-group medians, and two per-cadre values. Each
compared against a number read directly off the printed page. All pass.

---

## Reflection

What I asked for: a parser.

What I accepted: the first version, on a row count.

What I rejected: the first fix, once I saw what it did to Austria.

Where the AI went wrong: twice, and in the same way both times. The parse
succeeded, produced the expected number of rows, and put wrong values in a
column. Neither failure would have been caught by a test that the code runs,
because the code did run. Both were caught by looking at what the values meant.

The lasting change is the eight assertions. They encode facts about the source
document rather than about the code, which is the only kind of check that would
have caught either version.
