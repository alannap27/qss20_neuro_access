"""04_analyze.py

Takes in: data/processed/country_panel.csv
Does: answers the three research questions. RQ1 measures the gap between
      burden and capacity with a scale-free share ratio; RQ2 measures how
      unequally capacity is distributed with a Lorenz curve and Gini;
      RQ3 tests whether the gap differs between binned country types.
Outputs: output/figures/f01_alignment_ratio.{png,pdf}
         output/figures/f02_lorenz_gini.{png,pdf}
         output/figures/f03_service_reach_by_income.{png,pdf}
         output/tables/t01_analysis_sample.csv
         output/tables/t02_hypothesis_tests.csv
"""

import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle
from figstyle import BLUE, ORANGE, GREY, LIGHT, INCOME_COLORS
from utils import (paths, savefig, savetable, share_ratio, gini, gini_from_lorenz,
                   lorenz_points, permutation_test, ACC_LABELS)

figstyle.use_paper_style()
P = paths()
panel = pd.read_csv(P["processed"] / "country_panel.csv")

CAPACITY = "neurologists_per100k"
BURDEN = "stroke_dalys_per100k_agestd_2004"

# Sample description

sample = pd.DataFrame({
    "measure": ["Countries in panel",
                "With neurologist density (WHO GDO, 2017)",
                "With service-reach level (WHO GDO, 2017)",
                "With stroke DALY rate (WHO GHE, 2004)",
                "With World Bank income group (WHO Atlas, 2017)",
                "RQ1 sample: capacity and burden",
                "RQ3 sample: service reach and income group"],
    "n": [len(panel),
          panel[CAPACITY].notna().sum(),
          panel["accessibility_level"].notna().sum(),
          panel[BURDEN].notna().sum(),
          panel["wb_income_group"].notna().sum(),
          (panel[CAPACITY].notna() & panel[BURDEN].notna()).sum(),
          (panel["accessibility_level"].notna() & panel["wb_income_group"].notna()).sum()]})
print(sample.to_string(index=False))
savetable(sample, "t01_analysis_sample.csv")


# RQ1. Is capacity aligned with burden?

rq1 = panel[panel[CAPACITY].notna() & panel[BURDEN].notna()].copy()
zero_capacity = rq1[rq1[CAPACITY] == 0]
rq1 = rq1[rq1[CAPACITY] > 0].copy()
rq1["alignment_ratio"] = share_ratio(rq1[BURDEN].values, rq1[CAPACITY].values)
rq1 = rq1.sort_values("alignment_ratio")

print()
print("RQ1: countries on the ratio scale:", len(rq1))
print("zero-capacity countries:", list(zero_capacity["iso3"]),
      "with stroke DALY rates", list(zero_capacity[BURDEN]))

median_high = rq1.loc[rq1["income_bin2"] == "High-income", "alignment_ratio"].median()
median_low = rq1.loc[rq1["income_bin2"] == "Low / middle", "alignment_ratio"].median()
print(f"median ratio  high-income {median_high:.2f}   "
      f"low/middle {median_low:.2f}   factor {median_low / median_high:.1f}")

GROUP_LABEL = {"High-income": "High-income", "Low / middle": "Low / middle-income"}
rq1["group"] = rq1["income_bin2"].map(GROUP_LABEL).fillna("Not in WHO Atlas")
PALETTE = {"High-income": BLUE, "Low / middle-income": ORANGE, "Not in WHO Atlas": GREY}

fig, ax = plt.subplots(figsize=(10.6, 6.4))
ax.barh(rq1["iso3"], rq1["alignment_ratio"],
        color=rq1["group"].map(PALETTE), height=0.70, zorder=3)
ax.set_xscale("log")
ax.set_xlim(0.045, 190)
ax.set_xticks([0.1, 1, 10, 100])
ax.set_xticklabels(["0.1x", "1x", "10x", "100x"])
ax.axvline(1.0, linestyle="--", color="#333333", linewidth=1.3, zorder=4)

for row_index in range(len(rq1)):
    value = rq1["alignment_ratio"].iloc[row_index]
    text = f"{value:.2f}" if value < 1 else f"{value:.1f}"
    if 0.4 < value < 1.0:
        ax.text(value * 0.92, row_index, text, va="center", ha="right",
                fontsize=8.6, color="white", fontweight="semibold", zorder=6)
    else:
        ax.text(value * 1.16, row_index, text, va="center",
                fontsize=8.6, fontweight="semibold", zorder=6)

ax.text(0.052, len(rq1) - 0.2, "more workforce than burden",
        fontsize=8.6, style="italic", color=BLUE, va="center")
ax.text(1.42, len(rq1) - 0.2, "more burden than workforce",
        fontsize=8.6, style="italic", color=ORANGE, va="center")
ax.annotate("parity: share of burden equals\nshare of workforce",
            xy=(1.0, 2.6), xytext=(3.4, 1.1), fontsize=8.4,
            arrowprops=dict(arrowstyle="->", linewidth=0.9, color="#333333"))
ax.set_ylim(-1.0, len(rq1) + 0.2)
ax.set_xlabel("Share of sample stroke burden ÷ share of sample neurologists (log scale)")
figstyle.style_axis(ax, axis="x")
ax.set_title(f"Countries carrying the largest share of stroke burden hold the\n"
             f"smallest share of the neurological workforce (n = {len(rq1)} countries)")

handles = [plt.Rectangle((0, 0), 1, 1, color=PALETTE[k])
           for k in ["High-income", "Low / middle-income", "Not in WHO Atlas"]]
ax.legend(handles, ["High-income", "Low / middle-income", "Income group unavailable"],
          loc="lower right", fontsize=8.4)

figstyle.caption(fig,
    "A ratio above 1.0 means the country holds a larger share of the sample's stroke burden than of its neurologists; below 1.0 the reverse. The axis is logarithmic because the ratio spans three orders of\n"
    "magnitude, which also places parity at the center. Capacity is WHO Global Dementia Observatory neurologist density per 100 000 (2017); burden is WHO Global Health Estimates age-standardized stroke\n"
    f"DALYs per 100 000 (2004). Eswatini and Fiji report zero neurologists and cannot be placed on a ratio scale at all; their stroke DALY rates are {int(zero_capacity[BURDEN].max())} and {int(zero_capacity[BURDEN].min())} per 100 000.")
savefig(fig, "f01_alignment_ratio.png")

# RQ2. How unequally is capacity distributed?

capacity = panel.loc[panel[CAPACITY].notna(), CAPACITY].values
gini_value = gini(capacity)
gini_check = gini_from_lorenz(capacity)

print()
print(f"RQ2: Gini {gini_value:.4f} across {len(capacity)} countries")
print(f"independent check by Lorenz integration: {gini_check:.4f} "
      f"(difference {abs(gini_value - gini_check):.2e})")

for label in ["High-income", "Low / middle"]:
    subset = panel.loc[panel[CAPACITY].notna() & (panel["income_bin2"] == label), CAPACITY].values
    if len(subset) >= 3:
        print(f"within {label:14} (n = {len(subset)}): Gini {gini(subset):.3f}")

top = panel.loc[panel[CAPACITY].notna()].nlargest(1, CAPACITY).iloc[0]
bottom = panel.loc[panel[CAPACITY].notna() & (panel[CAPACITY] > 0)].nsmallest(1, CAPACITY).iloc[0]
print(f"focal contrast: {top['iso3']} {top[CAPACITY]:.2f} vs "
      f"{bottom['iso3']} {bottom[CAPACITY]:.2f} = {top[CAPACITY] / bottom[CAPACITY]:.0f}-fold")

cum_units, cum_total = lorenz_points(capacity)
half_share = float(np.interp(0.5, cum_units, cum_total))

fig, ax = plt.subplots(figsize=(9.8, 6.0))
ax.plot([0, 1], [0, 1], linestyle="--", color="#333333", linewidth=1.2)
ax.plot(cum_units, cum_total, marker="o", markersize=4.5, color=BLUE, zorder=3)
ax.fill_between(cum_units, cum_total, cum_units, alpha=0.16, color=BLUE, zorder=2)
ax.text(0.545, 0.315, f"Gini = {gini_value:.2f}", fontsize=15, fontweight="bold")
ax.text(0.285, 0.735, "line of perfect equality\n(every country the same density)",
        fontsize=8.4, rotation=31, color="#4b5563")
ax.annotate(f"the poorer half of countries\nholds {100 * half_share:.0f}% of the workforce",
            xy=(0.5, half_share), xytext=(0.70, 0.14), fontsize=8.8,
            arrowprops=dict(arrowstyle="->", linewidth=0.9, color=GREY,
                            connectionstyle="arc3,rad=0.25"))
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.set_xlabel("Cumulative share of countries, ranked from lowest density")
ax.set_ylabel("Cumulative share of neurologists per 100 000")
figstyle.style_axis(ax, axis="both")
ax.set_title(f"The poorer half of countries holds {100 * half_share:.0f}% of the sampled\n"
             f"neurological workforce (Gini = {gini_value:.2f}, n = {len(capacity)} countries)")
figstyle.caption(fig,
    "Lorenz curve of WHO Global Dementia Observatory neurologist density per 100 000 population (2017). Countries are ranked from lowest to highest density along the horizontal axis; the vertical axis is the\n"
    "cumulative share of the sampled workforce they hold. A Gini of 0 would place the curve on the dashed diagonal, a Gini of 1 in the bottom-right corner. The shaded area is half the Gini by construction.\n"
    f"Highest density: {top['iso3']} at {top[CAPACITY]:.1f} per 100 000. Lowest non-zero: {bottom['iso3']} at {bottom[CAPACITY]:.2f}. Two further countries report exactly zero and sit on the flat segment at the left.")
savefig(fig, "f02_lorenz_gini.png")

# RQ3. Does the gap differ between country types?

rq3 = panel[panel["accessibility_level"].notna() & panel["wb_income_group"].notna()].copy()
crosstab = pd.crosstab(rq3["income_bin3"], rq3["accessibility_level"])
print()
print(f"RQ3: {len(rq3)} countries with both service reach and an income group")
print(crosstab.rename(columns=ACC_LABELS).to_string())

tests = []

high = panel.loc[panel[CAPACITY].notna() & (panel["income_bin2"] == "High-income"), CAPACITY].values
low = panel.loc[panel[CAPACITY].notna() & (panel["income_bin2"] == "Low / middle"), CAPACITY].values

t_stat, t_p = stats.ttest_ind(high, low, equal_var=False)
u_stat, u_p = stats.mannwhitneyu(high, low, alternative="two-sided")
observed_diff, perm_p, _ = permutation_test(high, low, n_perm=20000)

tests.append(["Neurologist density, high vs low/middle income", "Welch t-test",
              f"t = {t_stat:.2f}", f"p = {t_p:.4f}",
              f"n = {len(high)} vs {len(low)}; means {np.mean(high):.2f} vs {np.mean(low):.2f}"])
tests.append(["Neurologist density, high vs low/middle income", "Mann-Whitney U",
              f"U = {u_stat:.1f}", f"p = {u_p:.4f}",
              f"medians {np.median(high):.2f} vs {np.median(low):.2f}"])
tests.append(["Neurologist density, high vs low/middle income", "Permutation test",
              f"diff = {observed_diff:.2f}", f"p = {perm_p:.4f}",
              "20 000 label shuffles; makes no distributional assumption"])

groups = [g["accessibility_level"].values for _, g in rq3.groupby("income_bin3") if len(g) >= 2]
f_stat, f_p = stats.f_oneway(*groups)
h_stat, h_p = stats.kruskal(*groups)
tests.append(["Service reach across three income bins", "One-way ANOVA",
              f"F = {f_stat:.2f}", f"p = {f_p:.4f}",
              "; ".join(f"{k}: mean {g['accessibility_level'].mean():.2f} (n = {len(g)})"
                        for k, g in rq3.groupby("income_bin3"))])
tests.append(["Service reach across three income bins", "Kruskal-Wallis",
              f"H = {h_stat:.2f}", f"p = {h_p:.4f}",
              "rank-based check on the ANOVA"])

chi2, chi_p, dof, expected = stats.chi2_contingency(crosstab.values)
tests.append(["Service reach by income bin", "Chi-square",
              f"chi2 = {chi2:.2f}, df = {dof}", f"p = {chi_p:.4f}",
              f"expected count below 5 in {(expected < 5).sum()} of {crosstab.size} cells"])

test_table = pd.DataFrame(tests, columns=["comparison", "test", "statistic", "p_value", "detail"])
print()
print(test_table.to_string(index=False))
savetable(test_table, "t02_hypothesis_tests.csv")

proportions = (crosstab.T / crosstab.sum(axis=1)).T * 100
bin_order = [b for b in ["Low / lower-middle", "Upper-middle", "High-income"]
             if b in proportions.index]
proportions = proportions.loc[bin_order]
counts_ordered = crosstab.loc[bin_order]

fig, ax = plt.subplots(figsize=(9.2, 6.0))
bottom = np.zeros(len(proportions))
level_colors = [ORANGE, "#dd9a4e", BLUE]
for position, level in enumerate([1, 2, 3]):
    if level not in proportions.columns:
        continue
    ax.bar(range(len(proportions)), proportions[level], bottom=bottom,
           color=level_colors[position], label=ACC_LABELS[level], width=0.60, zorder=3)
    for i in range(len(proportions)):
        value = proportions[level].iloc[i]
        if value > 6:
            ax.text(i, bottom[i] + value / 2,
                    f"{value:.0f}%\n(n = {int(counts_ordered[level].iloc[i])})",
                    ha="center", va="center", fontsize=8.8, fontweight="semibold",
                    color="white" if position != 1 else "#222222")
    bottom = bottom + proportions[level].values

ax.set_xticks(range(len(proportions)))
ax.set_xticklabels([b.replace(" / ", " /\n") for b in proportions.index])
ax.set_ylim(0, 118)
ax.set_ylabel("% of countries in the income bin")
ax.set_xlabel("World Bank income group")
ax.legend(loc="upper center", ncol=3, fontsize=8.6)
figstyle.style_axis(ax)
ax.set_title("Dementia diagnostic services reach rural areas in 77% of high-income\n"
             "countries and in none of the low or lower-middle income countries")
figstyle.caption(fig,
    f"WHO Global Dementia Observatory (2017) indicator GDO_q8x3_1, cross-tabulated with World Bank income group taken from Annex 1 of the WHO Neurology Atlas. n = {len(rq3)} countries reporting both fields.\n"
    f"Bars sum to 100% within each income group because the question is single-choice. Chi-square = {chi2:.2f}, df = {dof}, p = {chi_p:.4f}, but {(expected < 5).sum()} of {crosstab.size} cells have an expected count below 5, so the rank-based and\n"
    "permutation tests reported in table t02 are the ones to rely on. Low and lower-middle income countries are pooled because only four low-income countries answered this item.")
savefig(fig, "f03_service_reach_by_income.png")

print()
print("figures 1 to 3 written")
