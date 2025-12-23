# NHANES CHD Trends (1988–2023)

Analyzing 35 years of coronary heart disease prevalence in US adults using NHANES.

## What We Found

| Era | Period | Sample | Age-Std Prevalence |
|-----|--------|--------|-------------------|
| 1 | 1988–1994 | 16,552 | 5.5% |
| 2 | 1999–2006 | 20,196 | 6.0% |
| 3 | 2007–2014 | 23,390 | 5.0% |
| 4a | 2015–Mar 2020 | 5,688 | 5.0% |
| 4b | 2021–2023 | 7,772 | 4.8% |

**73,598 adults total**

The short version: CHD prevalence is actually going *down*, but you have to age-standardize to see it. The crude numbers look flat because the US population has gotten older—more old people means more CHD, which offsets the underlying decline in age-specific rates.

- Age-adjusted trend: **p < 0.001** (declining)
- Crude trend: p = 0.62 (looks flat)
- Persistent disparities: NH White ~7%, Mexican American ~3%

## Repo Structure

```
├── data/
│   ├── raw/           # NHANES XPT files
│   └── processed/     # Harmonized parquet
├── docs/
│   └── PI_Technical_Report.md
├── scripts/
│   ├── 01_download_data_fixed.py
│   ├── 02_harmonize_variables.py
│   ├── 04_R_survey_analysis.R      # Main analysis
│   ├── 05_nhanes_iii_processor.py
│   └── 06_nhanes_iii_harmonize.py
└── output/tables/
```

## Running It

You'll need Python 3.8+ and R 4.0+.

```bash
# Python deps
pip install pandas numpy pyarrow requests beautifulsoup4

# R deps
R -e "install.packages(c('survey', 'arrow'))"
```

Then run the pipeline:

```bash
python scripts/01_download_data_fixed.py     # Get continuous NHANES
python scripts/05_nhanes_iii_processor.py    # Get NHANES III
python scripts/06_nhanes_iii_harmonize.py    # Process III
python scripts/02_harmonize_variables.py     # Combine
Rscript scripts/04_R_survey_analysis.R       # Analyze
```

## Methods Notes

**CHD definition**: Composite of self-reported CHD, angina, or MI (MCQ160C/D/E in continuous NHANES, HAD1/2/3 in III).

**Weighting**: We followed NCHS guidance for combining cycles—divide WTMEC2YR by number of 2-year cycles when pooling. Taylor series linearization for variance.

**Age standardization**: Direct to 2000 US Standard Population (adults 20+, renormalized).

**Trend model**: `logit(CHD) ~ era + age_cat` using survey-weighted logistic regression.

## Output

Main results in `output/tables/`:
- `R_age_standardized_prevalence_by_era.csv` — the key table
- `R_survey_prevalence_by_era.csv` — crude numbers
- `R_survey_prevalence_by_sex.csv`
- `R_survey_prevalence_by_race.csv`
- `R_trend_test_results.csv`

Full writeup in `docs/PI_Technical_Report.md`.

## Data

Public NHANES data from CDC/NCHS:
- [Continuous NHANES](https://wwwn.cdc.gov/nchs/nhanes/Default.aspx)
- [NHANES III](https://wwwn.cdc.gov/nchs/nhanes/nhanes3/default.aspx)
