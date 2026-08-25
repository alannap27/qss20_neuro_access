# Transcript 02: Which countries stay in the sample

**Script:** `code/04_analyze.py`
**Paper reference:** Agentic Analysis, "Rejected: dropping the countries that
break the plot"

Edited excerpt from the session log, abridged as described in the README.

---

## The problem

Eswatini and Fiji report **zero** neurologists. The alignment ratio divides by
each country's share of the sampled workforce, so the ratio is undefined for
them, and a logarithmic axis cannot show a zero.

Hwne I was building Figure 1, I hit this and asked for a fix:

> **Assistant:** Two countries have zero capacity, so the ratio is undefined and
> they can't be placed on a log axis. The simplest is to filter them out before
> plotting — `panel = panel[panel[CAPACITY] > 0]` — which leaves 17 countries on
> the figure.

That line is correct and would have produced a clean figure.

---

## Why I rejected it

Eswatini and Fiji are not edge cases. They are the most extreme
instances of the thing the paper is about: a country carrying substantial
neurological burden with no neurologists at all. Their stroke DALY rates are
1,536 and 994 per 100,000, among the highest in the sample.

> **Alanna:** No, don't drop them; they're the whole point. They're the countries
> with the most burden and no one to treat it. 

Dropping them would have removed the strongest evidence for the claim in order
to improve an axis. The figure would have looked better and said less.

## What the code does now

They are excluded from the ratio scale because the ratio does not
exist for them, and reported separately everywhere the ratio appears:

```python
zero_capacity = panel[panel[CAPACITY] == 0]
plot_sample   = panel[panel[CAPACITY] > 0]
print(f"{len(zero_capacity)} countries report zero capacity and are "
      f"reported separately: {sorted(zero_capacity['iso3'])}")
```

The figure caption names them and gives their burden; the Results text states
the same. The appendix note under Table 1 records that they are retained in the
panel but cannot be placed on the ratio scale.

---

## Reflection

What I asked for: a figure of the alignment ratio.

What I accepted: excluding them from the *ratio scale*, which is forced: you
cannot divide by zero.

What I rejected: excluding them from the analysis, which is a different thing
that the proposed one-line filter quietly conflated with the first.

Where the assistant went wrong: it treated an undefined value as a plotting
nuisance rather than as a finding. The suggestion optimized for a clean figure
over a correct sample: the filter was offered as housekeeping, not as a
decision about what the paper claims.

This is the failure I would flag as most transferable. 
Filtering rows to make a chart render is a routine
operation that occasionally throws away the result.
