# Neurological care capacity vs. neurological disease burden

QSS 20 final project; Alanna Polyak, Dartmouth College.

Are the countries carrying the heaviest neurological disease burden the ones
with the workforce to treat it? No, and national figures understate the gap,
because the poorer a country is, the more completely its specialists are
confined to its capital.

National income drives both workforce capacity and measured burden, 
and measured burden depends on the diagnostic capacity that is 
the exposure of interest; no causal effect is estimated. 
See [Bounding the confounder](#bounding-the-confounder).

---

## Three research questions

### RQ1. Is capacity aligned with burden?
No, by a factor of about 34; on a scale-free burden-to-capacity share ratio,
the median high-income country sits at **0.38** and the median low- or
middle-income country at **13.12**. Myanmar reaches 69.7. Eswatini and Fiji
report **zero** neurologists and cannot be placed on a ratio scale at all.
→ `output/figures/f01_alignment_ratio.png`

### RQ2. How unequally is capacity distributed?
Gini of **0.61** across the 19 reporting countries, 95% bootstrap CI
**[0.43, 0.73]**. The poorer half of countries holds about 6% of the sampled
workforce; Switzerland has 13.10 per 100,000 against Myanmar's 0.07, which is a **187-fold**
difference. Dropping any single country moves the Gini by at most 0.06.
→ `output/figures/f02_lorenz_gini.png`, `f14_robustness.png`

### RQ3. Does the gap differ between country types?
Yes, on every test: dementia diagnostic services reach rural areas in
77% of high-income countries and in none of the low or lower-middle income
countries sampled.

| Comparison | Test | Result |
|---|---|---|
| Density, high-income vs low/middle | Welch *t* | *t* = 4.29, **P = 0.0031** |
| Same | Mann-Whitney *U* | **P = 0.0003** |
| Same | 20,000-draw permutation | **P = 0.0003** |
| Service reach across three income bins | One-way ANOVA | *F* = 5.74, **P = 0.0074** |
| Same | Kruskal-Wallis | *H* = 9.44, **P = 0.0089** |
| Service reach × income bin | Chi-square | χ² = 11.81, df = 4, **P = 0.0188** |
| Rural reach ~ high income | Logistic | OR = 7.6, **P = 0.0098** |

Country-level regressions on 19-35 observations would be underpowered, so no
slope is fitted; countries are binned and group differences tested directly.

---

## The two urban–rural indices

National density answers how many specialists does this country have, not
how many can a given resident reach.

Urban Concentration Index: the share of countries where specialists reach
the capital, minus the share where they reach rural areas, divided by 100.
Bounded [0, 1]. A value of 1 means every country has capital coverage and none
has rural coverage.

| Income group | UCI | Effective rural density per 100,000 |
|---|---|---|
| Low | 0.95 | 0.00 |
| Lower-middle | 0.83 | 0.24 |
| Upper-middle | 0.78 | 0.59 |
| High | 0.52 | 3.19 |

Effective rural density rescales the national median by the share of
countries with any rural practice; for low-income countries it is exactly
zero because no low-income country in the Atlas reports a neurologist practicing 
rurally. The national gap is 71-fold, and the rural gap has no denominator.
→ `output/figures/f06_urban_rural_indices.png`

---

## The gap metric

```
(country's share of the sample's total stroke DALY rate)
--------------------------------------------------------
(country's share of the sample's total neurologist density)
```

- **1.0**: holds exactly as large a share of the burden as of the workforce
- **1.2**: carries 20% more of the burden than its share of the workforce
- **13.1**: the same workforce stretched over thirteen times the need
- **below 1.0**: holds more of the workforce than of the burden

Scale-free, so it does not depend on the units of either input. Undefined at
zero capacity; those countries are reported separately rather than dropped.

---

## Bounding the confounder

For the high-income and low/middle-income median ratios to level, burden in
low- and middle-income countries would have to be **overstated by a factor of
34**, or their capacity understated by the same factor. Measurement error of
that size is not plausible, and under-diagnosis in low-capacity settings pushes
measured burden down, not up, which widens the true gap.

---

## Scripts

`code/utils.py` holds every shared function: the three metrics (`share_ratio`,
`gini`, `bootstrap_ci`), the urban–rural indices, WHO placeholder cleaning, the
two OLS solvers, and the permutation test. `code/figstyle.py` holds the figure
layout rules.

| Script | Takes in | Does | Outputs |
|---|---|---|---|
| [`01_parse_atlas_pdf.py`](code/01_parse_atlas_pdf.py) | the Atlas PDF (not committed, need access) | parses Annex 1, Tables 2–3 and Figs 11/12/16, asserting each against a value off the page | `data/raw/atlas_*.csv` |
| [`02_build_dhs_inventory.py`](code/02_build_dhs_inventory.py) | the DHS manifest (not committed, need access) | recovers country, survey, and recode type from the filename convention, then discards the URLs | `data/raw/dhs_inventory.csv` |
| [`03_clean_merge.py`](code/03_clean_merge.py) | `data/raw/*.csv` | cleans placeholders, orders the service-reach scale, builds the reach indicators, joins burden and income group, prints row counts around every join | `data/processed/country_panel.csv` |
| [`04_analyze.py`](code/04_analyze.py) | country panel | the three RQs: share ratio, Gini and Lorenz, binned tests | `f01`–`f03`, `t01`–`t02` |
| [`05_atlas_descriptives.py`](code/05_atlas_descriptives.py) | Atlas aggregate tables | the two 114-country gradients and per-cadre ratios | `f04`–`f05`, `t03` |
| [`06_urban_rural.py`](code/06_urban_rural.py) | panel + Atlas | the two urban–rural indices | `f06`, `t04` |
| [`07_regression_and_interactions.py`](code/07_regression_and_interactions.py) | country panel | normal equations against gradient descent, then the interaction tests | `f07`–`f08`, `t05`–`t06` |
| [`08_regional_and_cadre.py`](code/08_regional_and_cadre.py) | Atlas regional + panel | regional gradient with countries overlaid; cadre gradient on a log axis | `f09`–`f10`, `t07` |
| [`09_paired_and_dhs.py`](code/09_paired_and_dhs.py) | panel + Atlas + DHS inventory | pairs each aggregate descriptive with its country-level counterpart; DHS coverage | `f11`–`f13`, `t08`–`t09` |
| [`10_robustness.py`](code/10_robustness.py) | country panel | bootstrap CI, leave-one-out, permutation test, confounding bound | `f14`, `t10` |

```bash
pip install -r requirements.txt
bash run_all.sh
```

`run_all.sh` runs scripts 03 through 10, all offline from the committed raw
files. Scripts 01 and 02 are excluded because their inputs are deliberately not
in the repository; both write files that are already committed, and both print an
explanation and exit rather than failing if their input is absent. They require
access to datasets that must be approved.

### Checks the pipeline performs on itself

| Check | Where | Result |
|---|---|---|
| OLS against `statsmodels` | `07` | max abs difference 4.4e-16 |
| Gini by sorted index against Lorenz integration | `04` | difference 1.1e-16 |
| Welch *t* against a 20,000-draw permutation test | `04` | *P* = 0.0031 against 0.0003 |
| Atlas parse against values read off page | `01` | 8 assertions, all pass |

---

## Data

| Source | Gives | Coverage | Year |
|---|---|---|---|
| WHO GDO `GDO_q6x1_2` | neurologists per 100,000 | 21 records, 19 usable | 2017 |
| WHO GDO `GDO_q8x3_1` | where dementia diagnostic services reach | 61 records, 47 usable | 2017 |
| WHO GHE `SA_0000001689` | age-standardized stroke DALYs per 100,000 | 62 countries | 2004 |
| WHO/WFN Atlas, Annex 1 | WHO region, World Bank income group | 133 countries; 45 matched to ISO3 | 2017 |
| WHO/WFN Atlas, Figs 12, 16 | median density and practice location by income group | 114 responding countries | 2017 |
| DHS Program manifest | survey and GPS coverage inventory | 106 countries, 443 surveys, 62 with GPS | various |

The Atlas PDF and the DHS manifest are gitignored: the first is a copyrighted
publication, the second contains authenticated URLs tied to an approved DHS
account. The derived DHS inventory contains no survey responses and is included.

---

## Limitations

1. **Temporal mismatch:** Capacity is 2017, burden 2004: the only round of the
   WHO stroke series available through this API. Rankings are likely more stable
   than levels, but this is the weakest joint in the analysis and the reason RQ1
   describes a gap rather than estimating one.
2. **Small, self-selected samples:** 19 countries report density; 35 have both
   reach and an income group. Respondents plausibly have stronger health
   information systems, biasing toward better-resourced countries and
   understating the true gap.
3. **Stroke stands in for neurological burden** generally.
4. **Small cell counts:** Six of nine cells in the RQ3 table have expected counts
   below 5, which is why rank-based and permutation tests are reported alongside.
5. **Self-reported and unaudited:** Both WHO instruments are ministry
   questionnaires with no FTE adjustment.
6. **Interactions are underpowered:** Only 13 countries have both a ratio and a
   service-reach level; the interaction term is null (*P* = 0.99).

---
## The full figure set

All fourteen are in the paper: three in the body, eleven in Appendix A.
**Paper** is the number LaTeX assigns by order of appearance, which is what a
reader cites; **Site** is what the website calls the same image.

| | Figure | Script | Paper | Site |
|---|---|---|---|---|
| f01 | Burden-to-capacity share ratio by country | 04 | Fig. 1 | Figure 1 |
| f02 | Lorenz curve and Gini of neurologist density | 04 | Fig. 2 | Figure 2 |
| f03 | Dementia service reach by income group | 04 | Fig. 4 | gallery |
| f04 | Atlas workforce density by income group | 05 | Fig. 5 | gallery |
| f05 | Where neurologists practice | 05 | Fig. 6 | gallery |
| f06 | Urban concentration and effective rural density | 06 | Fig. 3 | Figure 3 |
| f07 | Normal equations against gradient descent | 07 | Fig. 12 | gallery |
| f08 | Capacity by reach, and reach by income | 07 | Fig. 13 | Figure 4 |
| f09 | Regional gradient in capacity | 08 | Fig. 8 | gallery |
| f10 | Gradient by clinical cadre | 08 | Fig. 7 | gallery |
| f11 | Paired workforce comparison | 09 | Fig. 9 | gallery |
| f12 | Paired rural access comparison | 09 | Fig. 10 | gallery |
| f13 | DHS survey coverage | 09 | Fig. 11 | gallery |
| f14 | Bounding exercise and leave-one-out | 10 | Fig. 14 | gallery |

The columns disagree because each document orders figures for its own reader:
the file index is production order, the paper puts body figures first and holds
the rest for the appendix, and the site follows its argument. 

Every figure carries a self-contained caption naming its source and sample size,
so it can be read without the surrounding text (as required). Titles state 
what the figure shows, including when the answer is that the sample 
cannot resolve it (f08).

---

## Paper and website

- `paper/qss20_paper.tex` — the manuscript, written against the PNAS
  `pnasmathematics` template and 6 pages maximum. 
- Project website source lives in a different `website/` folder, not in this repo.
