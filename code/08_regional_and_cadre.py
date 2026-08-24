"""08_regional_and_cadre.py

Takes in: data/raw/atlas_workforce_by_region.csv, atlas_workforce_by_income.csv,
          data/processed/country_panel.csv
Does: two cuts the income-group analysis cannot make. The gradient by WHO
      region with the country-level values overlaid, and the gradient by
      cadre on a logarithmic axis.
Outputs: output/figures/f09_regional_gradient.{png,pdf}
         output/figures/f10_cadre_gradient.{png,pdf}
         output/tables/t07_regional_comparison.csv
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
from figstyle import BLUE, ORANGE, GREY, LIGHT, AMBER
from utils import paths, savefig, savetable, REGION_NAMES

figstyle.use_paper_style()
P = paths()
by_region = pd.read_csv(P["raw"] / "atlas_workforce_by_region.csv")
by_income = pd.read_csv(P["raw"] / "atlas_workforce_by_income.csv")
panel = pd.read_csv(P["processed"] / "country_panel.csv")
CAPACITY = "neurologists_per100k"

regions = by_region[by_region["region_code"] != "Global"].sort_values("total_workforce_per100k")
global_median = by_region.loc[by_region["region_code"] == "Global",
                              "total_workforce_per100k"].values[0]
gdo = panel[panel[CAPACITY].notna() & panel["who_region"].notna()]

# Figure 9: regional gradient with individual countries overlaid

fig, ax = plt.subplots(figsize=(11.4, 6.6))
positions = np.arange(len(regions))
ax.bar(positions, regions["total_workforce_per100k"], width=0.60, color="#b7c9de",
       edgecolor="#7aa6cf", zorder=2, label="WHO Atlas regional median, all cadres")

for i in range(len(regions)):
    value = regions["total_workforce_per100k"].iloc[i]
    ax.text(i - 0.31, value + 0.24, f"{value:.1f}", ha="left", fontsize=10,
            fontweight="bold")
    ax.text(i, -0.78, f"Atlas n = {int(regions['n_total'].iloc[i])}", ha="center",
            fontsize=8, color="#4b5563")

rng = np.random.default_rng(20260803)
plotted = False
for i in range(len(regions)):
    code = regions["region_code"].iloc[i]
    subset = gdo[gdo["who_region"] == code]
    if len(subset) == 0:
        continue
    jitter = i + rng.uniform(-0.15, 0.15, len(subset))
    ax.scatter(jitter, subset[CAPACITY], s=58, color=ORANGE, zorder=4, alpha=0.92,
               edgecolor="white", linewidth=0.8,
               label="Individual country, WHO GDO, neurologists only" if not plotted else None)
    plotted = True
    ax.text(i, -1.34, f"GDO n = {len(subset)}", ha="center", fontsize=8, color=ORANGE)

ax.axhline(global_median, linestyle="--", color="#333333", linewidth=1.1, zorder=3)
ax.text(-0.45, global_median + 0.22, f"global median {global_median:.1f}", fontsize=8.6)
ax.set_xticks(positions)
ax.set_xticklabels([f"{c}\n{REGION_NAMES[c].replace(' Region', '').replace('Region of the ', '')}"
                    for c in regions["region_code"]], fontsize=8.8)
ax.set_ylim(-1.9, 15)
ax.set_ylabel("Workforce per 100 000 population")
ax.set_xlabel("WHO region")
ax.legend(loc="upper left", fontsize=8.6)
figstyle.style_axis(ax)
ax.set_title("The African and South-East Asia Regions sit an order of magnitude\n"
             "below the global median neurological workforce density")
figstyle.caption(fig,
    "Bars are the WHO and World Federation of Neurology Atlas median of the total neurological workforce per 100 000 population within each WHO region (2017, Figure 11); the count under each bar is the\n"
    "number of countries answering that item. Orange dots are individual countries from the WHO Global Dementia Observatory (2017), which counts adult neurologists only and therefore sits systematically below\n"
    "the Atlas bar for the same region. Dots are jittered horizontally to avoid overplotting. Regions are ordered by Atlas median rather than alphabetically. The two instruments track each other closely: the GDO\n"
    "median for the European Region is 6.01 against the Atlas adult-neurologist median of 6.60, and for South-East Asia 0.08 against 0.10.")
savefig(fig, "f09_regional_gradient.png")

# Figure 10: the gradient by cadre

groups = by_income[by_income["income_group"] != "Global"].copy()
CADRES = [("adult_neurologists_per100k", "Adult neurologists", BLUE),
          ("neurosurgeons_per100k", "Neurosurgeons", AMBER),
          ("child_neurologists_per100k", "Child neurologists", ORANGE)]

fig, ax = plt.subplots(figsize=(10.8, 6.4))
width = 0.26
ratios = []
for position in range(len(CADRES)):
    column, label, color = CADRES[position]
    offset = (position - 1) * width
    ax.bar(np.arange(len(groups)) + offset, groups[column], width=width,
           color=color, label=label, zorder=3)
    for i in range(len(groups)):
        ax.text(i + offset, groups[column].iloc[i] * 1.18,
                f"{groups[column].iloc[i]:.3g}", ha="center", fontsize=8.4)
    low = by_income.loc[by_income["income_group"] == "Low-income", column].values[0]
    high = by_income.loc[by_income["income_group"] == "High-income", column].values[0]
    ratios.append((label, high / low))

ax.set_yscale("log")
ax.set_ylim(0.001, 22)
ax.set_xticks(range(len(groups)))
ax.set_xticklabels(["Low", "Lower-middle", "Upper-middle", "High"], fontsize=9.2)
ax.set_ylabel("Median per 100 000 population (log scale)")
ax.set_xlabel("World Bank income group")
ax.legend(loc="upper left", fontsize=9)

summary = "\n".join(f"{label:<20}{ratio:5.0f}x" for label, ratio in ratios)
ax.text(0.325, 0.975, "high- vs low-income ratio\n" + summary, transform=ax.transAxes,
        fontsize=8.6, family="monospace", va="top", ha="left",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#f4f5f7", edgecolor="#cfd3d8"))
figstyle.style_axis(ax)
ax.set_title("The income gradient is steepest for the rarest cadre: 62-fold for\n"
             "neurosurgeons, 158-fold for adult neurologists, 195-fold for child")
figstyle.caption(fig,
    "Median number of each cadre per 100 000 population by World Bank income group, on a logarithmic vertical axis because the values span four orders of magnitude, from 0.002 to 4.75. A logarithmic axis\n"
    "makes equal ratios equal distances, so the widening vertical spacing between the three series from left to right is itself the finding rather than an artifact of the scale. Source: WHO and World Federation of\n"
    "Neurology Atlas, 2nd edition (2017), Table 3. Response counts differ by cadre, from 93 countries for child neurologists to 114 for adult neurologists, and are reported in table t03.")
savefig(fig, "f10_cadre_gradient.png")

# Regional comparison table

rows = []
for i in range(len(by_region)):
    row = by_region.iloc[i]
    subset = gdo[gdo["who_region"] == row["region_code"]]
    rows.append({"region_code": row["region_code"],
                 "region": REGION_NAMES.get(row["region_code"], "Global"),
                 "atlas_total_per100k": row["total_workforce_per100k"],
                 "atlas_n": row["n_total"],
                 "atlas_adult_neuro_per100k": row["adult_neurologists_per100k"],
                 "gdo_n": len(subset),
                 "gdo_median": round(subset[CAPACITY].median(), 3) if len(subset) else np.nan,
                 "gdo_min": round(subset[CAPACITY].min(), 3) if len(subset) else np.nan,
                 "gdo_max": round(subset[CAPACITY].max(), 3) if len(subset) else np.nan})
regional = pd.DataFrame(rows)
print(regional.to_string(index=False))
savetable(regional, "t07_regional_comparison.csv")

print()
print("figures 9 and 10 written")
