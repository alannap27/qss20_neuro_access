"""05_atlas_descriptives.py

Takes in: data/raw/atlas_workforce_by_income.csv
Does: the two aggregate gradients from the WHO Neurology Atlas. These rest
      on 114 responding countries, roughly six times the country-level
      sample, so they establish the gradient far more securely than the
      country-level analysis can, at the cost of not identifying countries.
Outputs: output/figures/f04_atlas_workforce_by_income.{png,pdf}
         output/figures/f05_atlas_where_neurologists_practice.{png,pdf}
         output/tables/t03_atlas_gradients.csv
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
from figstyle import BLUE, ORANGE, GREY, AMBER, INCOME_COLORS
from utils import paths, savefig, savetable

figstyle.use_paper_style()
P = paths()
income = pd.read_csv(P["raw"] / "atlas_workforce_by_income.csv")

groups = income[income["income_group"] != "Global"].copy()
global_median = income.loc[income["income_group"] == "Global", "total_workforce_per100k"].values[0]
SHORT = ["Low", "Lower-\nmiddle", "Upper-\nmiddle", "High"]

# Per-cadre gradients, reported in absolute and ratio terms

CADRES = [("total_workforce_per100k", "Total neurological workforce"),
          ("adult_neurologists_per100k", "Adult neurologists"),
          ("neurosurgeons_per100k", "Neurosurgeons"),
          ("child_neurologists_per100k", "Child neurologists")]

rows = []
for column, label in CADRES:
    low = income.loc[income["income_group"] == "Low-income", column].values[0]
    high = income.loc[income["income_group"] == "High-income", column].values[0]
    rows.append([label, low, high, round(high - low, 3), round(high / low, 1)])

gradients = pd.DataFrame(rows, columns=["cadre", "low_income_per100k",
                                        "high_income_per100k", "absolute_gap",
                                        "ratio_high_to_low"])
print(gradients.to_string(index=False))
savetable(gradients, "t03_atlas_gradients.csv")

total_ratio = gradients.loc[gradients["cadre"] == "Total neurological workforce",
                            "ratio_high_to_low"].values[0]

# Figure 4: the aggregate scarcity gradient

fig, ax = plt.subplots(figsize=(8.8, 6.0))
bars = ax.bar(SHORT, groups["total_workforce_per100k"], color=INCOME_COLORS,
              zorder=3, width=0.62)
for i in range(len(groups)):
    value = groups["total_workforce_per100k"].iloc[i]
    count = int(groups["n_total"].iloc[i])
    ax.text(i, value + 0.14, f"{value:.1f}", ha="center", fontsize=11,
            fontweight="bold", zorder=6)
    ax.text(i, value + 0.52, f"n = {count} countries", ha="center", fontsize=8,
            color="#4b5563", zorder=6)

ax.axhline(global_median, linestyle="--", color="#333333", linewidth=1.2, zorder=4)
ax.text(-0.46, global_median + 0.16, f"global median {global_median:.1f} per 100 000",
        fontsize=8.6, va="bottom")
ax.text(0.52, 6.45,
        f"{total_ratio:.0f}x\nhigh-income median ({groups['total_workforce_per100k'].iloc[3]:.1f})\n"
        f"vs low-income median ({groups['total_workforce_per100k'].iloc[0]:.1f})",
        fontsize=9.6, ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#f4f5f7", edgecolor="#cfd3d8"))
ax.set_ylim(0, 8.5)
ax.set_ylabel("Median neurological workforce per 100 000 population")
ax.set_xlabel("World Bank income group")
figstyle.style_axis(ax)
ax.set_title(f"Median neurological workforce density rises {total_ratio:.0f}-fold from low-\n"
             f"to high-income countries (WHO Neurology Atlas, 114 countries)")
figstyle.caption(fig,
    "Median of the total neurological workforce, defined by the Atlas as adult neurologists plus neurosurgeons plus child neurologists, per 100 000 population within each World Bank income group. Source:\n"
    "WHO and World Federation of Neurology, Atlas: Country Resources for Neurological Disorders, 2nd edition (2017), Figure 12. The count under each bar is the number of countries answering that item.\n"
    "These are medians of country values and are not weighted by population, so a group median describes the typical country in the group rather than the experience of the typical person in it.")
savefig(fig, "f04_atlas_workforce_by_income.png")

# Figure 5: where those staff actually work

SETTINGS = [("pct_countries_capital", "Capital city", BLUE),
            ("pct_countries_other_urban", "Other urban areas", AMBER),
            ("pct_countries_rural", "Rural areas", ORANGE)]

fig, ax = plt.subplots(figsize=(10.2, 6.4))
width = 0.26
for position in range(len(SETTINGS)):
    column, label, color = SETTINGS[position]
    offset = (position - 1) * width
    ax.bar([i + offset for i in range(len(groups))], groups[column],
           width=width, color=color, label=label, zorder=3)
    for i in range(len(groups)):
        ax.text(i + offset, groups[column].iloc[i] + 2.4,
                f"{int(groups[column].iloc[i])}%", ha="center", fontsize=10)

# Parked in the empty upper right and pointed back at the zero bar. Sitting it
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
ax.set_ylim(0, 152)
ax.set_ylabel("% of responding countries")
ax.set_xlabel("World Bank income group")
ax.legend(loc="upper right", ncol=1, fontsize=10)
figstyle.style_axis(ax)
ax.set_title("Capital-city coverage is near-universal at every income level while\n"
             "rural coverage falls from 45% to 0% (WHO Neurology Atlas, n = 114)")
figstyle.caption(fig,
    "Share of responding countries reporting that neurologists practice in each setting, by World Bank income group. A country can report more than one setting, so bars within a group do not sum to 100%.\n"
    "Source: WHO and World Federation of Neurology Atlas, 2nd edition (2017), Figure 16; 114 responding countries. This is the aggregate counterpart to Figure 3, which measures the same gradient country by\n"
    "country in the smaller Global Dementia Observatory extract. The two instruments use different questions and different country sets and produce the same ordering.")
savefig(fig, "f05_atlas_where_neurologists_practice.png")

print()
print("figures 4 and 5 written")
