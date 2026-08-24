"""10_robustness.py

Takes in: data/processed/country_panel.csv
Does: tests every main number. A bootstrap interval and a
      leave-one-out recomputation for the Gini, a permutation test for the
      income difference, and an explicit bound on how large the central
      confounder would have to be to overturn the main result.
Outputs: output/figures/f14_robustness.{png,pdf}
         output/tables/t10_robustness.csv
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
from figstyle import BLUE, ORANGE, GREY, LIGHT
from utils import (paths, savefig, savetable, gini, bootstrap_ci, leave_one_out,
                   permutation_test, share_ratio)

figstyle.use_paper_style()
P = paths()
panel = pd.read_csv(P["processed"] / "country_panel.csv")
CAPACITY = "neurologists_per100k"
BURDEN = "stroke_dalys_per100k_agestd_2004"

capacity_frame = panel[panel[CAPACITY].notna()].copy()
capacity = capacity_frame[CAPACITY].values
rows = []

# How precisely is the Gini known?

point, lower, upper, draws = bootstrap_ci(capacity, statistic=gini, n_boot=5000)
print(f"Gini {point:.3f}, 95% bootstrap CI [{lower:.3f}, {upper:.3f}], n = {len(capacity)}")
rows.append(["Gini of neurologist density", f"{point:.3f}",
             f"[{lower:.3f}, {upper:.3f}]",
             f"5 000-draw percentile bootstrap on n = {len(capacity)}"])

# Can one country carry the result?

loo = leave_one_out(capacity, capacity_frame["iso3"].values, statistic=gini)
swing = loo["statistic"].max() - loo["statistic"].min()
print(f"leave-one-out range {loo['statistic'].min():.3f} to {loo['statistic'].max():.3f}, "
      f"swing {swing:.3f}")
rows.append(["Gini, leave-one-out range",
             f"{loo['statistic'].min():.3f} to {loo['statistic'].max():.3f}",
             f"swing {swing:.3f}",
             f"dropping {loo.iloc[0]['dropped']} lowers it most, "
             f"{loo.iloc[-1]['dropped']} raises it most"])

# Does the income difference survive a distribution-free test?

high = capacity_frame.loc[capacity_frame["income_bin2"] == "High-income", CAPACITY].values
low = capacity_frame.loc[capacity_frame["income_bin2"] == "Low / middle", CAPACITY].values
observed, p_perm, null = permutation_test(high, low, n_perm=20000)
print(f"permutation test: observed difference {observed:.2f}, p = {p_perm:.4f}")
rows.append(["High- vs low/middle-income density",
             f"{np.mean(high):.2f} vs {np.mean(low):.2f} per 100 000",
             f"permutation p = {p_perm:.4f}",
             f"20 000 label shuffles at n = {len(high)} versus {len(low)}"])

# Bounding the central confounder

rq1 = panel[panel[CAPACITY].notna() & panel[BURDEN].notna() & (panel[CAPACITY] > 0)].copy()
rq1["ratio"] = share_ratio(rq1[BURDEN].values, rq1[CAPACITY].values)
median_high = rq1.loc[rq1["income_bin2"] == "High-income", "ratio"].median()
median_low = rq1.loc[rq1["income_bin2"] == "Low / middle", "ratio"].median()
factor = median_low / median_high
print(f"median ratio: high-income {median_high:.2f}, low/middle {median_low:.2f}, "
      f"factor {factor:.1f}")
rows.append(["Confounding needed to erase the RQ1 gap",
             f"median ratio {median_low:.2f} vs {median_high:.2f}",
             f"factor {factor:.1f}",
             "burden would have to be overstated, or capacity understated, this many "
             "times over in low- and middle-income countries"])

robustness = pd.DataFrame(rows, columns=["quantity", "estimate", "uncertainty", "note"])
savetable(robustness, "t10_robustness.csv")

# Figure 14

fig, axes = plt.subplots(1, 3, figsize=(16.0, 6.5))

ax = axes[0]
ax.hist(draws, bins=45, color="#b7c9de", zorder=3)
ax.axvline(point, color=BLUE, linewidth=2.2, zorder=4)
ax.axvline(lower, color="#333333", linestyle="--", linewidth=1.1, zorder=4)
ax.axvline(upper, color="#333333", linestyle="--", linewidth=1.1, zorder=4)
ax.text(point, ax.get_ylim()[1] * 0.95, f" point estimate {point:.2f}",
        fontsize=8.6, color=BLUE)
ax.text(lower, ax.get_ylim()[1] * 0.78, f"95% CI\n{lower:.2f} to {upper:.2f}",
        fontsize=8.6, ha="right")
ax.set_xlabel("Gini of neurologist density")
ax.set_ylabel("Bootstrap draws")
figstyle.style_axis(ax)
ax.set_title(f"The Gini is imprecise\n5 000 resamples of {len(capacity)} countries")
figstyle.panel(ax, "A")

ax = axes[1]
loo_sorted = loo.sort_values("statistic")
ax.barh(loo_sorted["dropped"], loo_sorted["statistic"], color="#b7c9de", zorder=3)
ax.axvline(point, color=BLUE, linewidth=2.2, zorder=4)
ax.text(point, len(loo_sorted) - 0.4, f" full sample {point:.2f}", fontsize=8.6, color=BLUE)
ax.set_xlim(loo_sorted["statistic"].min() - 0.05, loo_sorted["statistic"].max() + 0.035)
ax.set_xlabel("Gini with that country removed")
ax.tick_params(axis="y", labelsize=7.6)
figstyle.style_axis(ax, axis="x")
ax.set_title(f"No single country drives it\nfull swing across all drops is {swing:.3f}")
figstyle.panel(ax, "B")

ax = axes[2]
ax.hist(null, bins=50, color="#b7c9de", zorder=3)
ax.axvline(observed, color=ORANGE, linewidth=2.4, zorder=4)
ax.set_xlim(min(null) * 1.14, observed * 1.34)
ax.text(observed * 0.96, ax.get_ylim()[1] * 0.90,
        f"observed\ndifference\n{observed:.2f}", fontsize=8.6, color=ORANGE,
        ha="right", va="top")
ax.set_xlabel("High minus low/middle mean density, per 100 000")
ax.set_ylabel("Permutations")
figstyle.style_axis(ax)
ax.set_title(f"The income difference is not chance\n20 000 shuffles, p = {p_perm:.4f}")
figstyle.panel(ax, "C")

figstyle.suptitle(fig, "Robustness of the country-level results to their small sample")
figstyle.caption(fig,
    f"Panel A resamples the {len(capacity)} countries with replacement 5 000 times and recomputes the Gini each time. The interval is wide because the sample is small, so the coefficient should be read as evidence of\n"
    f"high inequality rather than as the precise value {point:.2f}. Panel B recomputes the Gini dropping each country in turn, which checks that no single reporter carries the result; the full swing is {swing:.3f}. Panel C shuffles\n"
    f"the income labels 20 000 times to build the null distribution for the difference in means directly, which avoids any normality assumption at n = {len(high)} versus {len(low)}. All three use WHO Global Dementia\n"
    "Observatory neurologist density per 100 000 population (2017).")
savefig(fig, "f14_robustness.png")

print()
print(robustness.to_string(index=False))
print()
print("figure 14 written")
