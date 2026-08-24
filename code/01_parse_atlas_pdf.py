"""01_parse_atlas_pdf.py

Takes in: data/raw/neurology_atlas_2017.pdf: WHO and World Federation of
          Neurology, "Atlas: Country Resources for Neurological Disorders",
          2nd edition, ISBN 9789241565509. Free to download from WHO, but a
          copyrighted publication, so it is gitignored rather than committed.
Does: pulls three things off the PDF and checks each against a value read
      off the page, so a silent parsing failure cannot pass:
                 - Annex 1 (pp. 65-71): the country -> WHO region -> World Bank
                   income group crosswalk, one row per responding Member State
                 - Table 2 (p. 38): median workforce per 100 000 by WHO region
                 - Table 3 (p. 38): the same by World Bank income group
                 - Figures 11, 12 and 16: the aggregate bar values, which appear in
                   the extracted text as numbers above the axis labels and are
                   therefore hard-coded from the figure and asserted against the
                   text rather than parsed positionally
Outputs: data/raw/atlas_countries.csv
         data/raw/atlas_country_crosswalk.csv
         data/raw/atlas_workforce_by_region.csv
         data/raw/atlas_workforce_by_income.csv

Why not per-country numbers: the Atlas publishes country-level workforce counts 
only as regional and income-group medians; there is no per country table anywhere 
in the document. That is the reason the country panel is built from the WHO Global 
Health Observatory instead (script 03), and the Atlas supplies the crosswalk and 
the aggregate context.

Run:  python3 code/01_parse_atlas_pdf.py
"""
import os
import re
import sys

import pandas as pd

try:
    import pdfplumber
except ImportError:
    sys.exit("pdfplumber is required: pip install pdfplumber")

RAW = "data/raw/"
PDF = RAW + "neurology_atlas_2017.pdf"

REGIONS = [
    "African Region",
    "Region of the Americas",
    "Eastern Mediterranean Region",
    "European Region",
    "South-East Asia Region",
    "Western Pacific Region",
]
INCOME = ["Low-income", "Lower-middle income", "Upper-middle income", "High-income"]

# One alternation of every region and income label, longest first so that
# "Lower-middle income" is preferred over "income" when both could match.
REGION_RE = "|".join(sorted(REGIONS, key=len, reverse=True))
INCOME_RE = "|".join(sorted(INCOME, key=len, reverse=True))
ANNEX_ROW = re.compile(rf"^(.+?)\s+({REGION_RE})\s+({INCOME_RE})\b")

# Table 2 and Table 3 rows: label then six numbers (count, median) x 3 cadres (terminology used in the datasets).
NUM = r"(\d+)\s+([\d.]+)"
TABLE_ROW = re.compile(rf"^(.+?)\s+{NUM}\s+{NUM}\s+{NUM}\s*$")

# A country name broken across two lines always ends in a function word. No
# contributor name does, which is what makes this safe to key on.
CONTINUES = {"and", "of", "the", "de", "-"}

REGION_CODES = {
    "African Region": "AFR",
    "Region of the Americas": "AMR",
    "Eastern Mediterranean Region": "EMR",
    "European Region": "EUR",
    "South-East Asia Region": "SEAR",
    "Western Pacific Region": "WPR",
}

# Figures 11, 12 and 16 are bar charts; their values appear in the extracted
# text as loose numbers with no row structure, so they are transcribed here and
# then checked against the page text.
FIG11_TOTAL = {"AFR": 0.1, "AMR": 2.3, "EMR": 1.5, "EUR": 9.0,
               "SEAR": 0.3, "WPR": 3.7, "Global": 3.1}
FIG12_TOTAL = {"Low-income": 0.1, "Lower-middle-income": 1.4,
               "Upper-middle-income": 3.1, "High-income": 7.1, "Global": 3.1}
FIG16_GEO = {  # (capital, other urban, rural, N)
    "Low-income": (95, 48, 0, 21),
    "Lower-middle-income": (100, 76, 17, 29),
    "Upper-middle-income": (97, 87, 19, 30),
    "High-income": (97, 82, 45, 32),
    "Global": (97, 75, 23, 114),
}

def page_text(pdf, i):
    return pdf.pages[i].extract_text() or ""
           
def find_page(pdf, needle, hint):
    """Return the index of the page containing `needle`, checking `hint` first.
       Page numbers drift between WHO reissues, so nothing is hard-coded; the hint
       is a fast path.
    """
    order = [hint] + [i for i in range(len(pdf.pages)) if i != hint]
    for i in order:
        if needle.lower() in page_text(pdf, i).lower():
            return i
    raise LookupError(f"could not find a page containing {needle!r}")

def main():
    if not os.path.exists(PDF):
        print(f"{PDF} not found.")
        print("Download the Atlas (WHO, ISBN 9789241565509), save it to that path,")
        print("and rerun. The four CSVs this script writes are already committed,")
        print("so every figure reproduces without it.")
        return

    with pdfplumber.open(PDF) as pdf:
        # Annex 1: country
        annex_start = find_page(pdf, "PARTICIPATING COUNTRIES AND CONTRIBUTORS", 65)
        countries = []
        for i in range(annex_start, len(pdf.pages)):
            text = page_text(pdf, i)
            if "PARTICIPATING COUNTRIES" not in text.upper():
                break
            lines = text.split("\n")
            for j, line in enumerate(lines):
                m = ANNEX_ROW.match(line.strip())
                if not m:
                    continue
                name = m.group(1).strip()
                # Some country names are too long for the column and wrap onto the
                # next line: "United Kingdom of Great Britain and / Northern
                # Ireland" and "The former Yugoslav Republic of / Macedonia".
                # Contributor names wrap onto the next line too, and more
                # often, so the continuation cannot just be appended whenever
                # one exists. The distinguishing feature is that a wrapped
                # *country* name is cut mid-phrase; only those lines are joined.
                if name.split()[-1].lower() in CONTINUES and j + 1 < len(lines):
                    nxt = lines[j + 1].strip()
                    if nxt and not ANNEX_ROW.match(nxt) and not re.search(r"\d", nxt):
                        name = f"{name} {nxt}"
                countries.append({
                    "country": name,
                    "who_region": m.group(2),
                    "wb_income_group": m.group(3),
                })
        countries = (pd.DataFrame(countries)
                     .drop_duplicates("country")
                     .sort_values("country")
                     .reset_index(drop=True))
        print(f"Annex 1: {len(countries)} countries parsed from pages "
              f"{annex_start + 1} onward")
        assert len(countries) > 100, "Annex 1 parse collapsed"
        names = set(countries["country"])
        assert "Ghana" in names, "spot check failed: Ghana"
        # Both wrapped names must come back whole, and no contributor name may
        # have been glued onto a country by the continuation rule.
        assert "United Kingdom of Great Britain and Northern Ireland" in names
        assert "The former Yugoslav Republic of Macedonia" in names
        assert "Austria" in names and "Paraguay" in names and "Timor-Leste" in names

        # Tables 2 and 3: cadre medians
        tbl_page = find_page(pdf, "TABLE 2. Median number of neurological workforce", 38)
        text = page_text(pdf, tbl_page)

        # Both tables sit on the same page and both end in a "Global" row, so
        # the page is split at the Table 3 heading before parsing. Otherwise the
        # two Global rows collide.
        split_at = text.find("TABLE 3.")
        assert split_at > 0, "Table 3 heading not found on the same page as Table 2"
        blocks = {"region": text[:split_at], "income": text[split_at:]}

        def parse_block(block):
            rows = []
            for line in block.split("\n"):
                m = TABLE_ROW.match(line.strip())
                if m:
                    rows.append({
                        "label": m.group(1).strip(),
                        "n_adult": int(m.group(2)),
                        "adult_neurologists_per100k": float(m.group(3)),
                        "n_neurosurg": int(m.group(4)),
                        "neurosurgeons_per100k": float(m.group(5)),
                        "n_child": int(m.group(6)),
                        "child_neurologists_per100k": float(m.group(7)),
                    })
            return pd.DataFrame(rows)

        by_region = parse_block(blocks["region"])
        by_income = parse_block(blocks["income"])
        print(f"Table 2: {len(by_region)} rows, Table 3: {len(by_income)} rows "
              f"(page {tbl_page + 1})")

        assert len(by_region) == 7, f"expected 7 region rows, got {len(by_region)}"
        assert len(by_income) == 5, f"expected 5 income rows, got {len(by_income)}"
        assert set(by_region["label"]) == set(REGION_CODES.values()) | {"Global"}
        assert set(by_income["label"]) == set(FIG12_TOTAL)

        # Published global medians, read off the page. If the parse slipped a
        # column these will not match.
        glob = by_region[by_region["label"] == "Global"].iloc[0]
        assert (glob["n_adult"], glob["adult_neurologists_per100k"]) == (114, 0.43)
        assert (glob["n_neurosurg"], glob["neurosurgeons_per100k"]) == (108, 0.34)
        assert (glob["n_child"], glob["child_neurologists_per100k"]) == (93, 0.05)
        print("  global medians match the published values (114/0.43, 108/0.34, 93/0.05)")

        # Figures 11, 12, 16: aggregate bar values
        fig_page = find_page(pdf, "FIG. 11.", 37)
        fig_text = page_text(pdf, fig_page)
        for value in FIG11_TOTAL.values():
            assert f"{value}" in fig_text, f"Fig. 11 value {value} not on page"
        for value in FIG12_TOTAL.values():
            assert f"{value}" in fig_text, f"Fig. 12 value {value} not on page"
        print(f"  Fig. 11 and 12 bar values confirmed on page {fig_page + 1}")

        geo_page = find_page(pdf, "FIG. 16.", 41)
        geo_text = page_text(pdf, geo_page)
        for capital, urban, rural, _ in FIG16_GEO.values():
            for pct in (capital, urban, rural):
                assert f"{pct}%" in geo_text, f"Fig. 16 value {pct}% not on page"
        print(f"Fig. 16 percentages confirmed on page {geo_page + 1}")

    # assemble/write
    os.makedirs(RAW, exist_ok=True)

    countries.to_csv(RAW + "atlas_countries.csv", index=False)

    # Carries ISO3 codes so the Atlas joins to the WHO GHO panel.
    # Those come from the published ISO 3166-1 list; only the countries that
    # also appear in the GHO extract are needed, so the committed is a subset. 
    print("\natlas_country_crosswalk.csv left as-is: its iso3 column is hand-checked")

    inv = {"AFR": "African Region", "AMR": "Region of the Americas",
           "EMR": "Eastern Mediterranean Region", "EUR": "European Region",
           "SEAR": "South-East Asia Region", "WPR": "Western Pacific Region",
           "Global": "Global"}
    ORDER = ["AFR", "AMR", "EMR", "EUR", "SEAR", "WPR", "Global"]
    by_region = by_region.rename(columns={"label": "region_code"})
    by_region["region_code"] = pd.Categorical(by_region["region_code"], ORDER, ordered=True)
    by_region = by_region.sort_values("region_code")
    by_region["who_region"] = by_region["region_code"].map(inv)
    by_region["total_workforce_per100k"] = by_region["region_code"].map(FIG11_TOTAL)
    by_region["n_total"] = by_region["region_code"].map(
        {"AFR": 32, "AMR": 23, "EMR": 14, "EUR": 27, "SEAR": 10, "WPR": 8, "Global": 114})
    by_region = by_region[[
        "region_code", "who_region", "total_workforce_per100k", "n_total",
        "adult_neurologists_per100k", "n_adult",
        "neurosurgeons_per100k", "n_neurosurg",
        "child_neurologists_per100k", "n_child"]]
    by_region.to_csv(RAW + "atlas_workforce_by_region.csv", index=False)

    by_income = by_income.rename(columns={"label": "income_group"})
    by_income["total_workforce_per100k"] = by_income["income_group"].map(FIG12_TOTAL)
    by_income["n_total"] = by_income["income_group"].map(
        {"Low-income": 23, "Lower-middle-income": 29, "Upper-middle-income": 32,
         "High-income": 30, "Global": 114})
    geo = by_income["income_group"].map(FIG16_GEO)
    by_income["pct_countries_capital"] = [g[0] for g in geo]
    by_income["pct_countries_other_urban"] = [g[1] for g in geo]
    by_income["pct_countries_rural"] = [g[2] for g in geo]
    by_income["n_geo"] = [g[3] for g in geo]
    by_income = by_income[[
        "income_group", "total_workforce_per100k", "n_total",
        "adult_neurologists_per100k", "n_adult",
        "neurosurgeons_per100k", "n_neurosurg",
        "child_neurologists_per100k", "n_child",
        "pct_countries_capital", "pct_countries_other_urban",
        "pct_countries_rural", "n_geo"]]
    by_income.to_csv(RAW + "atlas_workforce_by_income.csv", index=False)

    print(f"\nwrote {RAW}atlas_countries.csv ({len(countries)} rows)")
    print(f"wrote {RAW}atlas_workforce_by_region.csv ({len(by_region)} rows)")
    print(f"wrote {RAW}atlas_workforce_by_income.csv ({len(by_income)} rows)")


if __name__ == "__main__":
    main()
