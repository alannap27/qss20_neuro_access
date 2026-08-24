"""03_clean_merge.py

Takes in: the four files in data/raw/
Does: cleans WHO placeholder strings, puts the service-reach question on an
      ordered scale, builds the urban-rural indices, joins burden and
      income group, and prints row counts before and after every join
Outputs: data/processed/country_panel.csv
"""
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import ACC_SCALE, MISSING_STRINGS as MISSING

RAW, OUT = "data/raw/", "data/processed/"
os.makedirs(OUT, exist_ok=True)

def clean(s):
    return pd.to_numeric(s.where(~s.isin(MISSING)), errors="coerce")

def report(left, right, on, how, label):
    before = len(left)
    out = left.merge(right, on=on, how=how)
    print(f"merge [{label}]: {before} rows in -> {len(out)} rows out ({how} join on {on})")
    return out

neuro = pd.read_csv(RAW + "who_gho_neurologists_per100k.csv")
print(f"neurologist records: {len(neuro)}")
neuro["neurologists_per100k"] = clean(neuro["value_raw"])
print(f"usable numeric values: {neuro['neurologists_per100k'].notna().sum()}")
neuro = neuro[neuro["neurologists_per100k"].notna()]

acc = pd.read_csv(RAW + "who_gho_dx_accessibility.csv")
print(f"\naccessibility records: {len(acc)}")
acc["accessibility_level"] = acc["accessibility_raw"].map(ACC_SCALE)
print(f"usable ordered values: {acc['accessibility_level'].notna().sum()}")
acc = acc[acc["accessibility_level"].notna()]
# reaches beyond the capital at all, and reaches rural specifically
acc["beyond_capital"] = (acc["accessibility_level"] >= 2).astype(int)
acc["reaches_rural"] = (acc["accessibility_level"] == 3).astype(int)

burden = pd.read_csv(RAW + "who_ghe_stroke_dalys_2004.csv")
cross = pd.read_csv(RAW + "atlas_country_crosswalk.csv")
print(f"\nburden records: {len(burden)}   crosswalk records: {len(cross)}")

panel = pd.merge(neuro[["iso3", "who_region", "neurologists_per100k"]],
                 acc[["iso3", "accessibility_level", "accessibility_raw",
                      "beyond_capital", "reaches_rural"]],
                 on="iso3", how="outer")
print(f"\nouter join of capacity and accessibility: {len(panel)} rows")
panel = report(panel, burden, "iso3", "left", "burden")
panel = report(panel, cross[["iso3", "country", "wb_income_group"]], "iso3", "left", "crosswalk")

THREE = {"Low-income": "Low / lower-middle", "Lower-middle income": "Low / lower-middle",
         "Upper-middle income": "Upper-middle", "High-income": "High-income"}
panel["income_bin3"] = panel["wb_income_group"].map(THREE)
panel["income_bin2"] = panel["wb_income_group"].map(
    lambda x: "High-income" if x == "High-income" else ("Low / middle" if pd.notna(x) else None))
panel["high_income"] = (panel["wb_income_group"] == "High-income").astype("Int64")

panel = panel.sort_values("iso3")
panel.to_csv(OUT + "country_panel.csv", index=False)
print(f"\ncountry_panel.csv: {len(panel)} rows")
print(f"with capacity: {panel['neurologists_per100k'].notna().sum()}")
print(f"with reach: {panel['accessibility_level'].notna().sum()}")
print(f"with income: {panel['wb_income_group'].notna().sum()}")
