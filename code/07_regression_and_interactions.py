"""07_regression_and_interactions.py

Takes in: data/processed/country_panel.csv
Does: fits the country-level regression two ways, once by the normal
      equations and once by gradient descent, as a check that the closed
      form and the iterative solver agree. Then tests whether the gap
      depends on where capacity sits, not only how much of it there is.
Outputs: output/figures/f07_regression_solvers.{png,pdf}
         output/figures/f08_interactions.{png,pdf}
         output/tables/t05_regression.csv
         output/tables/t06_interaction_tests.csv

Note on the interaction result: it is null, and the sample is the reason. Only
13 countries carry both a burden-to-capacity ratio and a service-reach level.
"""

import os
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figstyle
from figstyle import BLUE, ORANGE, GREY, LIGHT, AMBER
from utils import (paths, savefig, savetable, share_ratio, add_intercept, ols_fit,
                   ols_predict, ols_standard_errors, gradient_descent, standardize,
                   r_squared, mse, ACC_LABELS)

figstyle.use_paper_style()
P = paths()
panel = pd.read_csv(P["processed"] / "country_panel.csv")
CAPACITY = "neurologists_per100k"
BURDEN = "stroke_dalys_per100k_agestd_2004"

# Build the regression sample

fit_sample = panel[panel[CAPACITY].notna() & panel[BURDEN].notna()
                   & (panel[CAPACITY] > 0)].copy()
fit_sample["alignment_ratio"] = share_ratio(fit_sample[BURDEN].values,
                                            fit_sample[CAPACITY].values)
fit_sample["log_ratio"] = np.log(fit_sample["alignment_ratio"])
fit_sample["log_capacity"] = np.log(fit_sample[CAPACITY])
fit_sample["high_income"] = (fit_sample["wb_income_group"] == "High-income").astype(float)

print(f"regression sample: {len(fit_sample)} countries")

y = fit_sample["log_ratio"].values
X_raw = fit_sample[["log_capacity", "high_income"]].values
X_std, means, sds = standardize(X_raw)
X = add_intercept(X_std)

# Two solvers for the same problem

betas_closed = ols_fit(X, y)
standard_errors = ols_standard_errors(X, y, betas_closed)
y_pred = ols_predict(X, betas_closed)

betas_gd, cost_history = gradient_descent(X, y, learning_rate=0.05, n_iterations=5000)

print()
print("closed form (normal equations):", np.round(betas_closed, 4))
print("gradient descent, 5000 steps:", np.round(betas_gd, 4))
print("maximum absolute difference:", f"{np.max(np.abs(betas_closed - betas_gd)):.2e}")
print(f"R squared: {r_squared(y, y_pred):.4f}   MSE: {mse(y, y_pred):.4f}")

# statsmodels as a third, independent check
sm_fit = sm.OLS(y, X).fit()
print("statsmodels:", np.round(sm_fit.params, 4))
print("agreement with closed form:", f"{np.max(np.abs(sm_fit.params - betas_closed)):.2e}")

TERMS = ["intercept", "log capacity (standardized)", "high income (standardized)"]
regression_table = pd.DataFrame({
    "term": TERMS,
    "beta_normal_equations": np.round(betas_closed, 4),
    "beta_gradient_descent": np.round(betas_gd, 4),
    "standard_error": np.round(standard_errors, 4),
    "t_statistic": np.round(betas_closed / standard_errors, 3)})
print()
print(regression_table.to_string(index=False))
savetable(regression_table, "t05_regression.csv")

# Figure 7: the two solvers agree

fig, axes = plt.subplots(1, 3, figsize=(15.4, 6.3))

ax = axes[0]
ax.plot(np.arange(1, len(cost_history) + 1), cost_history, color=BLUE, zorder=3)
ax.axhline(mse(y, y_pred), linestyle="--", color=ORANGE, linewidth=1.4, zorder=4)
ax.text(0.97, 0.10, f"closed-form minimum = {mse(y, y_pred):.3f}",
        transform=ax.transAxes, fontsize=8.8, color=ORANGE, ha="right", va="bottom")
ax.set_xscale("log")
ax.set_xlabel("Gradient descent iteration (log scale)")
ax.set_ylabel("Mean squared error")
figstyle.style_axis(ax)
ax.set_title("Descent converges to the closed-form\nminimum, it does not beat it")
figstyle.panel(ax, "A")

ax = axes[1]
ax.scatter(betas_closed, betas_gd, s=90, color=BLUE, zorder=3,
           edgecolor="white", linewidth=0.8)
lim = float(np.max(np.abs(betas_closed))) * 1.25
ax.plot([-lim, lim], [-lim, lim], linestyle="--", color="#333333", linewidth=1.1)
for i in range(len(TERMS)):
    ax.annotate(TERMS[i].replace(" (standardized)", ""),
                (betas_closed[i], betas_gd[i]), textcoords="offset points",
                xytext=(9, -4), fontsize=8.2)
ax.set_xlim(-lim, lim)
ax.set_ylim(-lim, lim)
ax.set_xlabel("Coefficient from the normal equations")
ax.set_ylabel("Coefficient from gradient descent")
figstyle.style_axis(ax, axis="both")
ax.set_title(f"The two solvers agree to\n{np.max(np.abs(betas_closed - betas_gd)):.0e}")
figstyle.panel(ax, "B")

ax = axes[2]
residual = (y_pred - y)
ax.scatter(y_pred, residual, s=80, color=BLUE, zorder=3, edgecolor="white", linewidth=0.8)
ax.axhline(0, linestyle="--", color="#333333", linewidth=1.1)
ax.set_xlabel("Fitted log ratio")
ax.set_ylabel("Residual")
figstyle.style_axis(ax)
ax.set_title("Residuals show no obvious structure\nat this sample size")
figstyle.panel(ax, "C")

figstyle.suptitle(fig, "The country-level regression, solved two ways as a check")
figstyle.caption(fig,
    f"Outcome is the natural log of the burden-to-capacity share ratio for the {len(fit_sample)} countries with both a burden and a positive capacity value. Predictors are standardized so a single learning rate suits both.\n"
    "Panel A: gradient descent minimizes the same mean squared error the normal equations solve exactly, so the curve approaches the dashed line from above and never crosses it. Panel B: coefficients from\n"
    "the two solvers plotted against each other; points on the diagonal mean they agree. Panel C: residuals against fitted values, the standard check for non-constant variance or curvature, neither of which is\n"
    "visible here, though 17 points is too few to see much. Capacity appears in the denominator of the outcome, so its large negative coefficient is mechanical rather than a substantive finding.")
savefig(fig, "f07_regression_solvers.png")

# Interaction tests

tests = []

reach = panel[panel["accessibility_level"].notna() & panel["income_bin3"].notna()].copy()
print()
print(f"service-reach sample: {len(reach)} countries")

reach_sub = reach.dropna(subset=["reaches_rural", "high_income"])
logit_fit = sm.Logit(reach_sub["reaches_rural"].astype(float),
                     sm.add_constant(reach_sub[["high_income"]].astype(float))).fit(disp=0)
odds_ratio = np.exp(logit_fit.params["high_income"])
tests.append(["Rural reach on high income", "Logistic regression",
              f"beta = {logit_fit.params['high_income']:+.3f}",
              f"p = {logit_fit.pvalues['high_income']:.4f}",
              f"odds ratio {odds_ratio:.1f}; n = {int(logit_fit.nobs)}"])

merged = fit_sample.merge(panel[["iso3", "accessibility_level", "reaches_rural"]],
                          on="iso3", how="left", suffixes=("", "_dup"))
merged = merged.dropna(subset=["accessibility_level"])
print(f"countries with BOTH a ratio and a service-reach level: {len(merged)}")

merged["z_log_capacity"] = ((merged["log_capacity"] - merged["log_capacity"].mean())
                            / merged["log_capacity"].std())
merged["rural"] = merged["reaches_rural"].astype(float)
merged["interaction"] = merged["z_log_capacity"] * merged["rural"]

design = sm.add_constant(merged[["z_log_capacity", "rural", "interaction"]])
interaction_fit = sm.OLS(merged["log_ratio"], design).fit()
tests.append(["log ratio on log capacity x reaches rural", "OLS interaction",
              f"beta = {interaction_fit.params['interaction']:+.3f}",
              f"p = {interaction_fit.pvalues['interaction']:.4f}",
              f"n = {int(interaction_fit.nobs)}; main effect of capacity "
              f"{interaction_fit.params['z_log_capacity']:+.3f}"])
print()
print(interaction_fit.summary().tables[1])

groups = [g["accessibility_level"].values for _, g in reach.groupby("income_bin3")
          if len(g) >= 2]
f_stat, f_p = stats.f_oneway(*groups)
tests.append(["Service reach across income bins", "One-way ANOVA",
              f"F = {f_stat:.2f}", f"p = {f_p:.4f}",
              "; ".join(f"{k}: {g['accessibility_level'].mean():.2f} (n = {len(g)})"
                        for k, g in reach.groupby("income_bin3"))])

interaction_table = pd.DataFrame(tests, columns=["comparison", "test", "statistic",
                                                 "p_value", "detail"])
print()
print(interaction_table.to_string(index=False))
savetable(interaction_table, "t06_interaction_tests.csv")

# Figure 8: the interaction, reported as a null

fig, axes = plt.subplots(1, 2, figsize=(13.5, 6.6))

ax = axes[0]
for rural_value, label, color in [(0.0, "Services stay urban", ORANGE),
                                  (1.0, "Services reach rural areas", BLUE)]:
    subset = merged[merged["rural"] == rural_value]
    if len(subset) == 0:
        continue
    ax.scatter(subset[CAPACITY], subset["alignment_ratio"], s=95, color=color,
               label=f"{label} (n = {len(subset)})", edgecolor="white",
               linewidth=0.9, zorder=3)
    if len(subset) >= 3:
        grid = np.linspace(np.log(subset[CAPACITY].min()),
                           np.log(subset[CAPACITY].max()), 40)
        slope = np.polyfit(np.log(subset[CAPACITY]), np.log(subset["alignment_ratio"]), 1)
        ax.plot(np.exp(grid), np.exp(np.polyval(slope, grid)), color=color,
                linewidth=2, zorder=2)
ax.set_xscale("log")
ax.set_yscale("log")
ax.axhline(1.0, linestyle="--", color="#333333", linewidth=1.1)
ax.text(ax.get_xlim()[0] * 1.2, 1.18, "parity", fontsize=8.6)
ax.set_xlabel("Neurologists per 100 000 (log scale)")
ax.set_ylabel("Burden-to-capacity share ratio (log scale)")
ax.legend(loc="upper right", fontsize=8.6)
figstyle.style_axis(ax, axis="both")
ax.set_title(f"Two nearly parallel lines: the interaction\nis {interaction_fit.params['interaction']:+.3f} with p = {interaction_fit.pvalues['interaction']:.2f}")
figstyle.panel(ax, "A")

ax = axes[1]
crosstab = pd.crosstab(reach["income_bin3"], reach["accessibility_level"])
proportions = (crosstab.T / crosstab.sum(axis=1)).T * 100
order = [b for b in ["Low / lower-middle", "Upper-middle", "High-income"]
         if b in proportions.index]
proportions = proportions.loc[order]
counts = crosstab.loc[order]
bottom = np.zeros(len(proportions))
level_colors = [ORANGE, AMBER, BLUE]
for position, level in enumerate([1, 2, 3]):
    if level not in proportions.columns:
        continue
    ax.bar(range(len(proportions)), proportions[level], bottom=bottom,
           color=level_colors[position], label=ACC_LABELS[level], width=0.60, zorder=3)
    for i in range(len(proportions)):
        value = proportions[level].iloc[i]
        if value > 7:
            ax.text(i, bottom[i] + value / 2,
                    f"{value:.0f}%\n(n = {int(counts[level].iloc[i])})",
                    ha="center", va="center", fontsize=8.6, fontweight="semibold",
                    color="white" if position != 1 else "#222222")
    bottom = bottom + proportions[level].values
ax.set_xticks(range(len(proportions)))
ax.set_xticklabels([b.replace(" / ", " /\n") for b in proportions.index])
ax.set_ylim(0, 118)
ax.set_ylabel("% of countries in the income bin")
ax.set_xlabel("World Bank income group")
ax.legend(loc="upper center", ncol=3, fontsize=8.4)
figstyle.style_axis(ax)
ax.set_title(f"What the sample can support: reach by\nincome, odds ratio {odds_ratio:.1f}, p = {logit_fit.pvalues['high_income']:.3f}")
figstyle.panel(ax, "B")

figstyle.suptitle(fig, "The interaction the 13-country sample cannot resolve, and the comparison it can")
figstyle.caption(fig,
    f"Panel A: each point is one of the {len(merged)} countries carrying both a burden-to-capacity ratio and a service-reach level. Both axes are logarithmic. Lines are ordinary least squares fits within each group; if\n"
    "capacity bought less alignment where services stay urban, the orange line would be flatter than the blue one. It is not, and the interaction coefficient is indistinguishable from zero. That is a statement about\n"
    "statistical power at n = 13, not evidence that no interaction exists. Panel B shows the comparison the larger service-reach sample does support: rural reach is far more common in high-income countries.\n"
    "Source: WHO Global Dementia Observatory (2017) and WHO Global Health Estimates. Cell counts are small throughout, so both panels are descriptive.")
savefig(fig, "f08_interactions.png")

print()
print("figures 7 and 8 written")
