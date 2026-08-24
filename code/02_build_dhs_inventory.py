"""02_build_dhs_inventory.py

Takes in: data/raw/urlslist.txt: the download manifest DHS emails you once a
          data request is approved. Not in this repository because it is not allowed to be.
          Every line in it is an authenticated download URL tied to my approved
          DHS account, so committing it would hand out my credentials.
Does: parses the DHS filename convention out of each URL to recover which
      country, survey, and recode type is available, then drops the URLs
Outputs: data/raw/dhs_inventory.csv: identifiers only, able to commit

The analysis in 09_paired_and_dhs.py asks which surveys exist, and does not
download them, so the URL column is not needed downstream and is discarded here.

DHS filenames follow a fixed pattern, e.g. AFBR71FL.zip:
    AF   country code (2 letters)
    BR   recode type  (2 letters: BR births, IR women, HH households, ...)
    71   phase number (2 digits)
    FL   flat-file release
"""
import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RAW = "data/raw/"
MANIFEST = RAW + "urlslist.txt"
OUT = RAW + "dhs_inventory.csv"

# Filename=AFBR71FL.zip ... &Ctry_Code=AF&surv_id=471
FILENAME = re.compile(r"Filename=([A-Z]{2})([A-Z]{2})(\d{2})[A-Z]{2}\.zip", re.I)
CTRY = re.compile(r"Ctry_Code=([A-Za-z]{2})")
SURV = re.compile(r"surv_id=(\d+)")

if not os.path.exists(MANIFEST):
    print(f"{MANIFEST} not found.")
    print("This is expected: the manifest is deliberately not in the repository.")
    print("Request the data at dhsprogram.com, save the emailed URL list to that")
    print("path, and rerun. The committed dhs_inventory.csv is the output of a")
    print("previous run and is enough to reproduce every figure.")
    sys.exit(0)

rows = []
with open(MANIFEST) as fh:
    for line in fh:
        line = line.strip()
        if not line:
            continue
        name = FILENAME.search(line)
        if not name:
            continue
        dhs_cc, file_type, phase = name.group(1), name.group(2), name.group(3)
        ctry = CTRY.search(line)
        surv = SURV.search(line)
        rows.append({
            "dhs_cc": dhs_cc.upper(),
            "ctry_code": (ctry.group(1).upper() if ctry else dhs_cc.upper()),
            "surv_id": (int(surv.group(1)) if surv else pd.NA),
            "file_type": file_type.upper(),
            "phase": int(phase),
            # the url is intentionally not stored
        })

inv = pd.DataFrame(rows).drop_duplicates()
print(f"parsed {len(inv)} dataset records")
print(f"countries: {inv['dhs_cc'].nunique()}")
print(f"surveys: {inv['surv_id'].nunique()}")
print(f"recode types: {sorted(inv['file_type'].unique())}")

inv.to_csv(OUT, index=False)
print(f"\nwrote {OUT} ({len(inv)} rows, no URLs)")
