"""Shared functions for the QSS 20 country-level project.

Every numbered script imports from here rather than redefining helpers, and
nothing in this file reads or writes a path that is not resolved from the
repository root.
"""

import numpy as np
import pandas as pd
from pathlib import Path

# Paths

def paths():
    """Project directories, resolved from this file so no script hardcodes one."""
    root = Path(__file__).resolve().parent.parent
    d = {"root": root,
         "raw": root / "data" / "raw",
         "processed": root / "data" / "processed",
         "figures": root / "output" / "figures",
         "tables": root / "output" / "tables"}
    for key in ["processed", "figures", "tables"]:
        d[key].mkdir(parents=True, exist_ok=True)
    return d

def savetable(df, name, index=False):
    p = paths()["tables"] / name
    df.to_csv(p, index=index)
    print("  wrote", p.relative_to(paths()["root"]))

def savefig(fig, name):
    """Write the figure as PNG and PDF using the shared style."""
    import figstyle
    p = paths()["figures"] / name
    figstyle.save(fig, p)
    print("  wrote", p.relative_to(paths()["root"]))

# WHO coding

# WHO stores non-response as literal strings inside otherwise numeric fields
MISSING_STRINGS = ["Not available", "Not applicable", "No data", "Not reported", ""]

# The service-reach question is ordered, not just categorical
ACC_SCALE = {"Capital city only": 1,
             "Capital and main cities only": 2,
             "Capital, main cities and rural areas": 3}
ACC_LABELS = {1: "Capital only", 2: "Capital + main cities", 3: "Reaches rural areas"}

REGION_NAMES = {"AFR": "African Region",
                "AMR": "Region of the Americas",
                "EMR": "Eastern Mediterranean Region",
                "EUR": "European Region",
                "SEAR": "South-East Asia Region",
                "WPR": "Western Pacific Region"}

def clean_who(series):
    """Convert a WHO value column to float, mapping placeholder strings to NaN."""
    return pd.to_numeric(series.where(~series.isin(MISSING_STRINGS)), errors="coerce")

# Linear algebra: OLS by the normal equations

def add_intercept(X):
    """Prepend a column of ones so the intercept is estimated with the slopes."""
    X = np.asarray(X, dtype=float)
    n = X.shape[0]
    return np.hstack([np.ones((n, 1)), X])

def ols_fit(X, y):
    """Solve the normal equations for the least squares coefficients.
        betas = (X'X)^{-1} X'y
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    XtX = X.T @ X
    Xty = X.T @ y
    betas = np.linalg.solve(XtX, Xty)
    return betas

def ols_predict(X, betas):
    return np.asarray(X, dtype=float) @ np.asarray(betas, dtype=float)

def mse(y, y_pred):
    """Mean squared error"""
    y = np.asarray(y, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    n = len(y)
    residual = (y_pred - y)
    return (1 / n) * np.sum(residual ** 2)

def r_squared(y, y_pred):
    """One minus the ratio of residual to total sum of squares"""
    y = np.asarray(y, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    ss_res = np.sum((y_pred - y) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    return 1 - ss_res / ss_tot

def ols_standard_errors(X, y, betas):
    """Classical standard errors under homoskedasticity
        var(betas) = sigma^2 (X'X)^{-1},   sigma^2 = RSS / (n - k)
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    n, k = X.shape
    residual = (X @ betas - y)
    sigma2 = np.sum(residual ** 2) / (n - k)
    cov = sigma2 * np.linalg.inv(X.T @ X)
    return np.sqrt(np.diag(cov))

def gradient_descent(X, y, learning_rate=0.05, n_iterations=5000):
    """Least squares by gradient descent, for comparison with the closed form.
    The gradient of the mean squared error with respect to the coefficients is
        dJ/dbetas = (2/n) X' (X betas - y)
    Run on standardized columns so one learning rate suits every feature.
    Returns the coefficients and the cost at each iteration.
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(y)
    betas = np.zeros(X.shape[1])
    cost_history = np.zeros(n_iterations)
    for i in range(n_iterations):
        y_pred = X @ betas
        residual = (y_pred - y)
        gradient = (2 / n) * (X.T @ residual)
        betas = betas - learning_rate * gradient
        cost_history[i] = (1 / n) * np.sum(residual ** 2)
    return betas, cost_history

def standardize(X):
    """Center and scale each column so gradient descent behaves."""
    X = np.asarray(X, dtype=float)
    means = X.mean(axis=0)
    sds = X.std(axis=0)
    sds[sds == 0] = 1.0
    return (X - means) / sds, means, sds

# The gap metric

def share_ratio(burden, capacity):
    """Burden-to-capacity share ratio.
        R_i = (b_i / sum_j b_j) / (c_i / sum_j c_j)
    A value of 1 means the country holds as large a share of the
    sample's burden as of the sample's capacity; 13.1 means the same workforce
    is spread over thirteen times the need. The ratio is scale-free, so it does
    not depend on the units of either input; undefined where capacity is zero.
    """
    burden = np.asarray(burden, dtype=float)
    capacity = np.asarray(capacity, dtype=float)
    burden_share = burden / np.nansum(burden)
    capacity_share = capacity / np.nansum(capacity)
    ratio = np.full(len(burden), np.nan)
    positive = capacity_share > 0
    ratio[positive] = burden_share[positive] / capacity_share[positive]
    return ratio

# Inequality measures

def lorenz_points(x):
    """Cumulative share of units against cumulative share of the total.
    Sorting ascending and taking running sums gives the Lorenz curve.
    A leading zero is there so the curve starts at the origin.
    """
    x = np.sort(np.asarray(x, dtype=float))
    x = x[~np.isnan(x)]
    n = len(x)
    cum_units = np.arange(1, n + 1) / n
    cum_total = np.cumsum(x) / np.sum(x)
    return np.insert(cum_units, 0, 0.0), np.insert(cum_total, 0, 0.0)

def gini(x):
    """Gini coefficient, twice the area between the Lorenz curve and equality.
    With the values sorted ascending this equals
        G = (2 * sum_i i * x_i) / (n * sum_i x_i)  -  (n + 1) / n
    0 means every country holds the same density; 1 means one country holds
    the entire workforce.
    """
    x = np.sort(np.asarray(x, dtype=float))
    x = x[~np.isnan(x)]
    n = len(x)
    if n == 0 or np.sum(x) == 0:
        return np.nan
    index = np.arange(1, n + 1)
    return (2 * np.sum(index * x)) / (n * np.sum(x)) - (n + 1) / n

def gini_from_lorenz(x):
    """Gini by trapezoidal integration under the Lorenz curve.
    An independent check on `gini`.
    """
    cum_units, cum_total = lorenz_points(x)
    area_under = np.trapz(cum_total, cum_units)
    return 1 - 2 * area_under

def urban_concentration_index(pct_capital, pct_rural):
    """Share of countries reaching the capital minus the share reaching rural, / 100.
    Bounded on [0, 1] because capital reach weakly dominates rural reach in
    every income group observed. 0 means specialists are as likely to work
    rurally as in the capital; 1 means every country has capital coverage and
    none has rural coverage.
    """
    return (pct_capital - pct_rural) / 100.0

def effective_rural_density(national_density, pct_rural):
    """National median rescaled by the share of countries with any rural practice.
    Answers what a rural resident faces rather than what the national average
    is; zero when no country in the group reports rural practice.
    """
    return national_density * pct_rural / 100.0

# Resampling

def bootstrap_ci(x, statistic=gini, n_boot=5000, alpha=0.05, seed=20260803):
    """Percentile bootstrap interval for a statistic of a small sample."""
    rng = np.random.default_rng(seed)
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    draws = np.zeros(n_boot)
    for i in range(n_boot):
        draws[i] = statistic(rng.choice(x, size=n, replace=True))
    lower = np.percentile(draws, 100 * alpha / 2)
    upper = np.percentile(draws, 100 * (1 - alpha / 2))
    return statistic(x), lower, upper, draws

def leave_one_out(x, labels, statistic=gini):
    """Recompute a statistic dropping each observation in turn."""
    x = np.asarray(x, dtype=float)
    rows = []
    for i in range(len(x)):
        kept = np.delete(x, i)
        rows.append({"dropped": labels[i], "statistic": statistic(kept)})
    return pd.DataFrame(rows).sort_values("statistic")

def permutation_test(group_a, group_b, n_perm=20000, seed=20260803):
    """Two-sided permutation test on the difference in means.
    Shuffling the group labels builds the null distribution directly, which
    avoids any assumption about the shape of the underlying distributions.
    This ends up mattering at n = 8 versus 7.
    """
    rng = np.random.default_rng(seed)
    group_a = np.asarray(group_a, dtype=float)
    group_b = np.asarray(group_b, dtype=float)
    n_a = len(group_a)
    pooled = np.concatenate([group_a, group_b])
    observed = np.mean(group_a) - np.mean(group_b)
    null = np.zeros(n_perm)
    for i in range(n_perm):
        shuffled = rng.permutation(pooled)
        null[i] = np.mean(shuffled[:n_a]) - np.mean(shuffled[n_a:])
    p_value = (np.sum(np.abs(null) >= np.abs(observed)) + 1) / (n_perm + 1)
    return observed, p_value, null
