"""09_paired_and_dhs.py

Takes in: data/processed/country_panel.csv, data/raw/atlas_workforce_by_income.csv,
          data/raw/dhs_inventory.csv
Does: sets each aggregate Atlas descriptive beside its country-level
      counterpart, so the two instruments can be read against each other,
      and characterizes what the approved DHS holdings can support.
Outputs  : output/figures/f11_paired_workforce.{png,pdf}
           output/figures/f12_paired_rural_access.{png,pdf}
           output/figures/f13_dhs_coverage.{png,pdf}
           output/tables/t08_paired_instruments.csv, t09_dhs_coverage.csv
"""

import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle
from figstyle import BLUE, ORANGE, GREY, LIGHT, AMBER, INCOME_COLORS
from utils import paths, savefig, savetable, ACC_LABELS

figstyle.use_paper_style()
P = paths()
panel = pd.read_csv(P["processed"] / "country_panel.csv")
by_income = pd.read_csv(P["raw"] / "atlas_workforce_by_income.csv")
CAPACITY = "neurologists_per100k"

groups = by_income[by_income["income_group"] != "Global"].copy()
SHORT = ["Low", "Lower-\nmiddle", "Upper-\nmiddle", "High"]
BINS = ["Low / lower-middle", "Upper-middle", "High-income"]
gdo = panel[panel[CAPACITY].notna() & panel["income_bin3"].notna()].copy()

# Figure 11: the workforce gradient

fig, axes = plt.subplots(1, 2, figsize=(13.5, 6.6))

ax = axes[0]
ax.bar(range(len(groups)), groups["total_workforce_per100k"], color=INCOME_COLORS,
       zorder=3, width=0.62)
for i in range(len(groups)):
    value = groups["total_workforce_per100k"].iloc[i]
    ax.text(i, value + 0.14, f"{value:.1f}", ha="center", fontsize=10.5, fontweight="bold")
    ax.text(i, value + 0.58, f"n = {int(groups['n_total'].iloc[i])}", ha="center",
            fontsize=8, color="#4b5563")
ax.axhline(3.1, linestyle="--", color="#333333", linewidth=1.1)
ax.text(-0.46, 3.34, "global median 3.1", fontsize=10)
ax.set_xticks(range(len(groups)))
ax.set_xticklabels(SHORT)
ax.set_ylim(0, 8.6)
ax.set_ylabel("Median workforce per 100 000")
ax.set_xlabel("World Bank income group")
figstyle.style_axis(ax)
ax.set_title("Aggregate instrument: WHO Neurology Atlas\nmedian of country values, 114 countries")
figstyle.panel(ax, "A")

ax = axes[1]
rng = np.random.default_rng(20260803)
x_of_bin = {b: i for i, b in enumerate(BINS)}
bin_colors = {"Low / lower-middle": INCOME_COLORS[0], "Upper-middle": INCOME_COLORS[2],
              "High-income": INCOME_COLORS[3]}
for b in BINS:
    subset = gdo[gdo["income_bin3"] == b]
    if len(subset) == 0:
        continue
    ax.scatter(x_of_bin[b] + rng.uniform(-0.12, 0.12, len(subset)), subset[CAPACITY],
               s=72, zorder=3, alpha=0.92, color=bin_colors[b],
               edgecolor="white", linewidth=0.9)
    median = subset[CAPACITY].median()
    ax.plot([x_of_bin[b] - 0.27, x_of_bin[b] + 0.27], [median, median],
            color="#222222", linewidth=2.2, zorder=4)
    # Above the median rule rather than beside it. To the right it ran into the
    # ISO3 callouts for the lowest-density countries in the same bin.
    ax.text(x_of_bin[b] - 0.34, median, f"median\n{median:.2f}",
            ha="right", va="center", fontsize=10, fontweight="semibold",
            linespacing=1.3)


for i in range(2):
    row = gdo.nlargest(2, CAPACITY).iloc[i]
    ax.annotate(row["iso3"], (x_of_bin[row["income_bin3"]], row[CAPACITY]),
                textcoords="offset points", xytext=(15, 3), fontsize=10)
# The three lowest-density countries sit almost on top of each other just above
# zero. Labeling them in the panel put three callouts into the same square inch
# as the median rule and the neighbouring bin, so they are named in the caption
# instead. The two highest are far apart and keep their labels.
lowest = gdo.nsmallest(3, CAPACITY)
lowest_text = ", ".join(f"{r.iso3} {r[CAPACITY]:.2f}" for _, r in lowest.iterrows())

ax.set_xticks(range(len(BINS)))
ax.set_xticklabels([f"Low /\nlower-middle\nn = {len(gdo[gdo['income_bin3'] == BINS[0]])}",
                    f"Upper-\nmiddle\nn = {len(gdo[gdo['income_bin3'] == BINS[1]])}",
                    f"High\nn = {len(gdo[gdo['income_bin3'] == BINS[2]])}"])
ax.set_xlim(-1.35, 2.9)
ax.set_ylim(-1.2, 17.6)
ax.set_ylabel("Neurologists per 100 000, one dot per country")
ax.set_xlabel("World Bank income group")
figstyle.style_axis(ax)
ax.set_title(f"Country-level instrument: WHO GDO\n{len(gdo)} countries with an income group")
figstyle.panel(ax, "B")

figstyle.suptitle(fig, "The same workforce gradient measured by two independent WHO instruments")
figstyle.caption(fig,
    "Panel A reports the median across countries within each income group and cannot identify individual countries. Panel B reports each country separately but covers far fewer of them. The two disagree on\n"
    "level, because Panel A counts adult neurologists, neurosurgeons and child neurologists while Panel B counts adult neurologists only, and agree on direction and steepness. That agreement is the point:\n"
    f"the country-level finding is not an artifact of the small sample. The three lowest-density countries in Panel B, too close together to label in place, are {lowest_text} per 100 000. Sources: WHO and\n"
    "World Federation of Neurology Atlas 2nd edition (2017) Figure 12; WHO Global Dementia Observatory (2017) GDO_q6x1_2.")
savefig(fig, "f11_paired_workforce.png")

# Figure 12: rural access

reach = panel[panel["accessibility_level"].notna() & panel["income_bin3"].notna()].copy()
crosstab = pd.crosstab(reach["income_bin3"], reach["accessibility_level"])
for level in [1, 2, 3]:
    if level not in crosstab.columns:
        crosstab[level] = 0
crosstab = crosstab[[1, 2, 3]].reindex([b for b in BINS if b in crosstab.index])
proportions = (crosstab.T / crosstab.sum(axis=1)).T * 100

fig, axes = plt.subplots(1, 2, figsize=(13.5, 6.6))

ax = axes[0]
SETTINGS = [("pct_countries_capital", "Capital city", BLUE),
            ("pct_countries_other_urban", "Other urban areas", AMBER),
            ("pct_countries_rural", "Rural areas", ORANGE)]
width = 0.26
for position in range(len(SETTINGS)):
    column, label, color = SETTINGS[position]
    offset = (position - 1) * width
    ax.bar([i + offset for i in range(len(groups))], groups[column], width=width,
           color=color, label=label, zorder=3)
    for i in range(len(groups)):
        ax.text(i + offset, groups[column].iloc[i] + 2.6,
                f"{int(groups[column].iloc[i])}%", ha="center", fontsize=10)
# The rural bar for low income is zero, so the column directly above it is the
# one piece of empty space in the panel. Label sits there and drops straight
# down, which keeps the leader line off every other bar.
ax.annotate("no low-income country reports\na neurologist practicing rurally",
            xy=(width, 2.5), xytext=(width, 138), fontsize=10,
            ha="center", va="top", color=ORANGE,
            arrowprops=dict(arrowstyle="->", linewidth=1.1, color=ORANGE,
                            shrinkA=6, shrinkB=3))
ax.set_xticks(range(len(groups)))
ax.set_xticklabels(SHORT)
ax.set_ylim(0, 150)
ax.set_ylabel("% of responding countries")
ax.set_xlabel("World Bank income group")
ax.legend(loc="upper center", ncol=3, fontsize=8.4)
figstyle.style_axis(ax)
ax.set_title("Where neurologists practice\nWHO Neurology Atlas, 114 countries")
figstyle.panel(ax, "A")

ax = axes[1]
bottom = np.zeros(len(proportions))
level_colors = [ORANGE, AMBER, BLUE]
for position, level in enumerate([1, 2, 3]):
    ax.bar(range(len(proportions)), proportions[level], bottom=bottom,
           color=level_colors[position], label=ACC_LABELS[level], zorder=3, width=0.60)
    for i in range(len(proportions)):
        value = proportions[level].iloc[i]
        if value > 6:
            ax.text(i, bottom[i] + value / 2,
                    f"{value:.0f}%\n(n = {int(crosstab[level].iloc[i])})",
                    ha="center", va="center", fontsize=8.4, fontweight="semibold",
                    color="white" if position != 1 else "#222222")
    bottom = bottom + proportions[level].values
ax.set_xticks(range(len(proportions)))
ax.set_xticklabels([f"Low /\nlower-middle\nn = {len(gdo[gdo['income_bin3'] == BINS[0]])}",
                    f"Upper-\nmiddle\nn = {len(gdo[gdo['income_bin3'] == BINS[1]])}",
                    f"High\nn = {len(gdo[gdo['income_bin3'] == BINS[2]])}"])
ax.set_ylim(0, 126)
ax.set_ylabel("% of countries in the income bin")
ax.set_xlabel("World Bank income group")
ax.legend(loc="upper center", ncol=3, fontsize=8.4)
figstyle.style_axis(ax)
ax.set_title(f"Where dementia diagnostic services reach\nWHO GDO, {len(reach)} countries")
figstyle.panel(ax, "B")

high_rural = proportions[3].get("High-income", 0)
low_rural = proportions[3].get("Low / lower-middle", 0)
figstyle.suptitle(fig, "Two instruments, one finding: specialist care thins out before it reaches rural populations")
figstyle.caption(fig,
    "Panel A asks whether neurologists practice in a given setting at all, and a country may report several. Panel B asks how far dementia diagnostic services extend, and the answer is single-choice. These are\n"
    f"different questions about the same underlying constraint, asked of overlapping but not identical country sets, and they produce the same ordering: rural coverage falls from 45% to 0% across income groups\n"
    f"in Panel A, and the share of countries whose services reach rural areas falls from {high_rural:.0f}% to {low_rural:.0f}% in Panel B. Sources: WHO Atlas 2nd edition (2017) Figure 16; WHO Global Dementia Observatory (2017) GDO_q8x3_1.")
savefig(fig, "f12_paired_rural_access.png")

paired = pd.DataFrame([
    ["Workforce gradient", "WHO Neurology Atlas, aggregate", 114,
     "median per income group", "0.1 to 7.1 per 100 000, 71-fold",
     "cannot identify countries and cannot be linked to burden"],
    ["Workforce gradient", "WHO GDO, country level", int(gdo[CAPACITY].notna().sum()),
     "one value per country",
     f"median {gdo.loc[gdo['income_bin3'] == 'Low / lower-middle', CAPACITY].median():.2f} to "
     f"{gdo.loc[gdo['income_bin3'] == 'High-income', CAPACITY].median():.2f} per 100 000",
     "small sample; counts adult neurologists only"],
    ["Rural access", "WHO Neurology Atlas, aggregate", 114,
     "% of countries reporting rural practice", "45% to 0% across income groups",
     "records presence, not intensity"],
    ["Rural access", "WHO GDO, country level", len(reach),
     "ordered service-reach level",
     f"{high_rural:.0f}% to {low_rural:.0f}% of countries reach rural areas",
     "dementia services specifically, not all neurology"]],
    columns=["construct", "instrument", "n_countries", "unit", "finding", "limitation"])
print(paired.to_string(index=False))
savetable(paired, "t08_paired_instruments.csv")

# Figure 13: DHS coverage

dhs = pd.read_csv(P["raw"] / "dhs_inventory.csv")
FILE_TYPES = {"IR": "Individual recode, women 15-49", "KR": "Children's recode",
              "HR": "Household recode", "BR": "Births recode",
              "PR": "Household member recode", "GE": "Geographic, GPS clusters",
              "MR": "Men's recode", "CR": "Couples recode", "HW": "Height and weight",
              "WI": "Wealth index", "HH": "Household, legacy", "SQ": "Service provision",
              "IQ": "Interview questionnaire", "VR": "Verbatim responses",
              "OD": "Other documentation", "VA": "Verbal autopsy", "ML": "Malaria"}

n_countries = dhs["dhs_cc"].nunique()
n_surveys = dhs.groupby(["dhs_cc", "surv_id"]).ngroups
gps_countries = set(dhs.loc[dhs["file_type"] == "GE", "dhs_cc"])
per_country = dhs.groupby("dhs_cc").agg(n_surveys=("surv_id", "nunique")).reset_index()
per_country["has_gps"] = per_country["dhs_cc"].isin(gps_countries)

print()
print(f"DHS manifest: {len(dhs)} datasets, {n_countries} countries, "
      f"{n_surveys} surveys, {len(gps_countries)} with GPS")

fig, axes = plt.subplots(1, 3, figsize=(16.0, 6.5))

ax = axes[0]
counts = dhs["file_type"].value_counts()
counts = counts[counts >= 10].sort_values()
ax.barh([FILE_TYPES.get(k, k) for k in counts.index], counts.values,
        color=[ORANGE if k == "GE" else "#b7c9de" for k in counts.index], zorder=3)
for i in range(len(counts)):
    ax.text(counts.values[i] + 6, i, str(counts.values[i]), va="center", fontsize=8.4)
ax.set_xlim(0, counts.max() * 1.20)
ax.set_xlabel("Datasets in the approved manifest")
ax.tick_params(axis="y", labelsize=8)
figstyle.style_axis(ax, axis="x")
ax.set_title(f"What the manifest contains\n{len(dhs):,} datasets across {n_surveys} surveys")
figstyle.panel(ax, "A")

ax = axes[1]
bins = np.arange(0.5, per_country["n_surveys"].max() + 1.5, 1)
ax.hist([per_country.loc[per_country["has_gps"], "n_surveys"],
         per_country.loc[~per_country["has_gps"], "n_surveys"]],
        bins=bins, stacked=True, color=[ORANGE, "#b7c9de"],
        label=["GPS files available", "No GPS files"], zorder=3)
ax.set_xlabel("DHS surveys held for the country")
ax.set_ylabel("Number of countries")
ax.legend(fontsize=8.6)
figstyle.style_axis(ax)
ax.set_title(f"Repeat coverage by country\n{len(gps_countries)} of {n_countries} have GPS clusters")
figstyle.panel(ax, "B")

ax = axes[2]
overlap = pd.Series({"DHS\nany survey": n_countries,
                     "DHS\nwith GPS": len(gps_countries),
                     "WHO\nservice reach": int(panel["accessibility_level"].notna().sum()),
                     "WHO\nneurologist\ndensity": int(panel[CAPACITY].notna().sum())})
ax.bar(range(len(overlap)), overlap.values,
       color=["#b7c9de", ORANGE, "#7aa6cf", BLUE], zorder=3, width=0.60)
for i in range(len(overlap)):
    ax.text(i, overlap.values[i] + 1.8, str(overlap.values[i]), ha="center",
            fontsize=10.5, fontweight="bold")
ax.set_xticks(range(len(overlap)))
ax.set_xticklabels(overlap.index, fontsize=8.6)
ax.set_ylim(0, max(overlap.values) * 1.22)
ax.set_ylabel("Number of countries")
figstyle.style_axis(ax)
ax.set_title("The binding constraint is WHO, not DHS")
figstyle.panel(ax, "C")

figstyle.suptitle(fig, "The approved DHS holdings are broad; the WHO capacity data are the limiting factor")
figstyle.caption(fig,
    "Derived from the filenames in the approved DHS Program download manifest. No survey data were downloaded or read: the DHS filename convention CCTTVVFL.zip encodes country, file type and survey\n"
    "phase, which is enough to build a coverage inventory. GE files carry displaced GPS cluster coordinates and are the input for the distance-to-care measure planned as the next step. Panel C is the reason the\n"
    f"country-level analysis in Figures 1 to 3 is small: DHS covers {n_countries} countries, but only {int(panel[CAPACITY].notna().sum())} of them have a WHO neurologist-density value to link them to.")
savefig(fig, "f13_dhs_coverage.png")

coverage = pd.DataFrame({
    "metric": ["Datasets in manifest", "Distinct countries", "Distinct surveys",
               "Countries with GPS files", "Countries with one survey only",
               "Countries with five or more surveys", "Median surveys per country"],
    "value": [len(dhs), n_countries, n_surveys, len(gps_countries),
              int((per_country["n_surveys"] == 1).sum()),
              int((per_country["n_surveys"] >= 5).sum()),
              float(per_country["n_surveys"].median())]})
print(coverage.to_string(index=False))
savetable(coverage, "t09_dhs_coverage.csv")

print()
print("figures 11 to 13 written")
