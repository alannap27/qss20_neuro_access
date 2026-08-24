"""06_urban_rural.py

Takes in: data/raw/atlas_workforce_by_income.csv
Does: builds the two urban-rural indices. National density answers how many
      specialists a country has, not how many a given resident can reach;
      these separate the two.
Outputs: output/figures/f06_urban_rural_indices.{png,pdf}
         output/tables/t04_urban_rural_indices.csv
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
from figstyle import BLUE, ORANGE, GREY, LIGHT, INCOME_COLORS
from utils import (paths, savefig, savetable, urban_concentration_index,
                   effective_rural_density)

figstyle.use_paper_style()
P = paths()
income = pd.read_csv(P["raw"] / "atlas_workforce_by_income.csv")

ORDER = ["Low-income", "Lower-middle-income", "Upper-middle-income", "High-income"]
groups = income[income["income_group"] != "Global"].copy()
groups = groups.set_index("income_group").loc[ORDER].reset_index()
SHORT = ["Low", "Lower-\nmiddle", "Upper-\nmiddle", "High"]

groups["uci"] = urban_concentration_index(groups["pct_countries_capital"],
                                          groups["pct_countries_rural"])
groups["rural_access_deficit"] = (groups["pct_countries_capital"]
                                  - groups["pct_countries_rural"])
groups["effective_rural_density"] = effective_rural_density(
    groups["total_workforce_per100k"], groups["pct_countries_rural"])

print("Urban-rural indices by income group")
print(groups[["income_group", "total_workforce_per100k", "pct_countries_capital",
              "pct_countries_rural", "uci", "effective_rural_density"]]
      .round(3).to_string(index=False))
savetable(groups[["income_group", "n_total", "total_workforce_per100k",
                  "pct_countries_capital", "pct_countries_other_urban",
                  "pct_countries_rural", "uci", "rural_access_deficit",
                  "effective_rural_density"]],
          "t04_urban_rural_indices.csv")

low = groups.iloc[0]
high = groups.iloc[3]
national_ratio = high["total_workforce_per100k"] / low["total_workforce_per100k"]
print()
print(f"UCI: {low['uci']:.2f} in low-income vs {high['uci']:.2f} in high-income")
print(f"national density ratio, high over low: {national_ratio:.0f}-fold")
if low["effective_rural_density"] > 0:
    print(f"effective rural density ratio: "
          f"{high['effective_rural_density'] / low['effective_rural_density']:.0f}-fold")
else:
    print("effective rural density ratio: undefined, the low-income denominator is")
    print("exactly zero. The gap is not a ratio because the quantity is absent, not small.")

# Figure 6

fig, axes = plt.subplots(1, 3, figsize=(15.6, 6.4))

ax = axes[0]
ax.bar(SHORT, groups["uci"], color=INCOME_COLORS, zorder=3, width=0.62)
for i in range(len(groups)):
    ax.text(i, groups["uci"].iloc[i] + 0.022, f"{groups['uci'].iloc[i]:.2f}",
            ha="center", fontsize=10.5, fontweight="bold")
ax.set_ylim(0, 1.14)
ax.set_ylabel("Urban Concentration Index")
ax.set_xlabel("World Bank income group")
ax.text(0.97, 0.97, "1.00 = every country has capital\ncoverage and none has rural",
        transform=ax.transAxes, fontsize=8.2, va="top", ha="right", color="#4b5563",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="#dcdfe3"))
figstyle.style_axis(ax)
ax.set_title("Specialists are more completely urban\nin poorer countries")
figstyle.panel(ax, "A")

ax = axes[1]
ax.bar(SHORT, groups["effective_rural_density"], color=INCOME_COLORS, zorder=3, width=0.62)
for i in range(len(groups)):
    ax.text(i, groups["effective_rural_density"].iloc[i] + 0.07,
            f"{groups['effective_rural_density'].iloc[i]:.2f}", ha="center",
            fontsize=10.5, fontweight="bold")
ax.set_ylim(0, 3.85)
ax.set_ylabel("Effective rural density per 100 000")
ax.set_xlabel("World Bank income group")
# The arrow tip stops short of the bar-value label sitting at zero; landing on
# it put the two pieces of text on top of each other.
ax.annotate("exactly zero", xy=(0.06, 0.22), xytext=(0.75, 1.45), fontsize=10.5,
            color=ORANGE, fontweight="semibold",
            arrowprops=dict(arrowstyle="->", linewidth=1.2, color=ORANGE,
                            shrinkA=3, shrinkB=6))
figstyle.style_axis(ax)
ax.set_title("What a rural resident actually faces")
figstyle.panel(ax, "B")

ax = axes[2]
x = np.arange(len(groups))
ax.plot(x, groups["total_workforce_per100k"], marker="o", color=BLUE,
        label="National median density", zorder=4)
ax.plot(x, groups["effective_rural_density"], marker="s", color=ORANGE,
        label="Effective rural density", zorder=4)
ax.fill_between(x, groups["effective_rural_density"], groups["total_workforce_per100k"],
                color=LIGHT, alpha=0.55, zorder=2, label="Gap due to urban concentration")
ax.set_xticks(x)
ax.set_xticklabels(SHORT)
ax.set_ylim(-0.3, 8.3)
ax.set_ylabel("Per 100 000 population")
ax.set_xlabel("World Bank income group")
ax.legend(loc="upper left", fontsize=8.6)
figstyle.style_axis(ax)
ax.set_title("The shaded area is the access\nthat national figures imply but do not deliver")
figstyle.panel(ax, "C")

figstyle.suptitle(fig, "National density overstates access wherever specialists stay urban")
figstyle.caption(fig,
    "WHO and World Federation of Neurology Atlas, 2nd edition (2017), Figures 12 and 16; 114 responding countries. Panel A: the Urban Concentration Index is the share of countries reporting specialists in the\n"
    "capital minus the share reporting any rural practice, divided by 100. It is bounded on [0, 1] because capital reach weakly dominates rural reach in every group observed. Panel B: effective rural density\n"
    "multiplies the national median by the share of countries with any rural practice, so it answers what a rural resident faces rather than what the national average is. It is exactly zero for low-income countries\n"
    "because no low-income country in the Atlas reports a neurologist practicing rurally, which makes the high-to-low gap undefined rather than merely large. Panel C plots both series on one axis.")
savefig(fig, "f06_urban_rural_indices.png")

print()
print("figure 6 written")
