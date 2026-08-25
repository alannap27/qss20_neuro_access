# Transcript 01: Choosing the estimators

**Scripts:** `code/04_analyze.py`, `code/07_regression_and_interactions.py`
**Paper reference:** Agentic Analysis, "Rejected: a regression presented as a
main finding"; and the accepted Gini cross-check

Edited excerpt from the session log, abridged as described in the README.

---

## The proposal I rejected

Asked how to quantify the alignment between burden and capacity, the assistant
proposed a country-level regression of the log alignment ratio on neurologist
density and an income indicator, reporting the slope with a standard error as
the paper's headline result.

> **Assistant:** The cleanest headline is the slope on log capacity: each
> one-unit increase in standardized log density is associated with a −2.07
> change in log ratio, SE 0.21, t = −9.7. That gives you a single number with a
> confidence interval to lead the Results section.

The output is real. The estimate is `−2.0715`, and it is reproduced in
`output/tables/t05_regression.csv` and in the paper's appendix table.

**Why I rejected it as a headline:** The sample is 19 countries. A slope with a
standard error carries an implicit claim to precision that 19 observations do
not support, and nothing in a fitted `statsmodels` object flags this: the
standard error is computed the same way whether n is 19 or 19,000. The number
looks identical to a well-identified one.

> **Alanna:** 19 countries isn't enough to fit a slope and report it like that's
> the finding. Can we bin by income group and test the groups against each other
> instead

The headline became binned comparisons: a Welch *t*, a Mann–Whitney *U*, and a
20,000-draw permutation test, all reported together. The regression survives
only as Fig. 12 in the appendix, where its purpose is to show that two solvers
agree. 

I then did this by hand to fulfill my own ask.

---

## The proposal I accepted

The assistant suggested implementing the Gini twice by different routes and
comparing them.

> **Assistant:** Worth computing the Gini two ways — the sorted-index formula
> and trapezoidal integration under the Lorenz curve. They are algebraically
> equivalent, so any disagreement is an implementation bug rather than a
> modeling choice.

I took this; the two agree to `1.1e-16`:

```
gini (sorted index)        0.6070
gini (Lorenz integration)  0.6070
difference                 1.1e-16
```

I accepted it because it costs almost nothing and checks the one quantity the
whole of RQ2 rests on. The same reasoning produced the second solver check in
script 07, where hand-written normal equations are compared against gradient
descent and against `statsmodels`, agreeing to `4.4e-16`.

---

## Reflection

What I asked for: an estimator for the alignment question.

What I accepted: the duplicate Gini implementation, and later the duplicate OLS
implementation, both as mutual checks.

What I rejected: the regression as a headline result.

Where the assistant went wrong: it optimized for a quotable number. The proposal
was not a coding error: the code is correct and is still in the repository. It
was a judgment error about what 19 observations can support, and the assistant
gave no indication that the question was even open. The decision to bin rather
than regress is mine, and it makes a weaker claim, honestly.
