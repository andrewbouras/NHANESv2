# NHANES CHD Prevalence Trends Study: Technical Report

**Prepared for:** Principal Investigator  
**Date:** December 23, 2024  
**GitHub Repository:** https://github.com/andrewbouras/NHANESv2

---

## Executive Summary

We completed a comprehensive analysis of 35-year trends in coronary heart disease (CHD) prevalence using NHANES data from 1988-2023, covering **73,598 adults** across five eras.

### Key Finding
**No statistically significant secular trend in CHD prevalence** (p=0.62) was observed over the 35-year period. Prevalence ranged from 5.5% to 6.3% across eras.

---

## 1. Study Design

### 1.1 Era Definitions (Per PI Approval)

| Era | Period | Rationale |
|-----|--------|-----------|
| Era 1 | 1988-1994 | NHANES III baseline |
| Era 2 | 1999-2006 | Early continuous NHANES |
| Era 3 | 2007-2014 | Mid continuous NHANES |
| Era 4a | 2015-March 2020 | Pre-pandemic |
| Era 4b | 2021-2023 | Post-pandemic |

**Decision:** Era 4 was split per PI guidance to isolate potential pandemic effects.

### 1.2 Study Population

- **Inclusion:** Adults ≥20 years with valid MEC exam weights
- **Exclusion:** Missing CHD outcome data, invalid survey weights
- **Final sample:** 73,598 adults

---

## 2. Data Sources

### 2.1 NHANES Cycles Included

| Cycle | Sample Size | Data Format |
|-------|-------------|-------------|
| NHANES III (1988-94) | 16,552 | ASCII fixed-width |
| 1999-2000 | ~5,000 | SAS transport (XPT) |
| 2001-2002 | ~5,000 | XPT |
| 2003-2004 | ~5,000 | XPT |
| 2005-2006 | ~5,000 | XPT |
| 2007-2008 | ~5,000 | XPT |
| 2009-2010 | ~5,000 | XPT |
| 2011-2012 | ~5,000 | XPT |
| 2013-2014 | ~5,000 | XPT |
| 2015-2016 | ~5,000 | XPT |
| 2017-March 2020 | ~5,700 | XPT |
| Aug 2021-Aug 2023 | ~7,700 | XPT |

### 2.2 Data Components Used

- **Demographics (DEMO):** Age, sex, race/ethnicity, poverty income ratio, survey weights
- **Medical Conditions (MCQ):** CHD, angina, heart attack self-report
- **Blood Pressure (BPX):** Systolic/diastolic measurements
- **Body Measures (BMX):** BMI
- **Diabetes (DIQ):** Self-reported diabetes
- **Laboratory (GHB, GLU, TCHOL, HDL, TRIGLY):** HbA1c, glucose, lipid panel

---

## 3. Variable Definitions

### 3.1 Primary Outcome: CHD Composite

CHD was defined as an affirmative response (=1) to ANY of the following:

| Variable | Continuous NHANES | NHANES III | Question |
|----------|-------------------|------------|----------|
| CHD | MCQ160C | HAD1 | "Ever told you had coronary heart disease?" |
| Angina | MCQ160D | HAD2 | "Ever told you had angina?" |
| Heart Attack | MCQ160E | HAD3 | "Ever told you had a heart attack?" |

**Coding:** 1 = Yes, 2 = No (standard NHANES)

### 3.2 Covariates

| Variable | Definition | Source |
|----------|------------|--------|
| Age | Years at MEC exam | RIDAGEYR |
| Sex | 1=Male, 2=Female | RIAGENDR |
| Race/Ethnicity | 5 categories | RIDRETH1 |
| Education | Adults 20+ education | DMDEDUC2 |
| Poverty Income Ratio | Family PIR | INDFMPIR |

### 3.3 Risk Factors (For Future Analysis)

| Factor | Definition |
|--------|------------|
| Hypertension | SBP≥130 OR DBP≥80 OR BP medication |
| Diabetes | HbA1c≥6.5% OR FPG≥126 OR DM medication |
| Hyperlipidemia | TC≥200 OR LDL≥130 mg/dL |
| Obesity | BMI ≥30 kg/m² |
| LDL Cholesterol | Friedewald: TC - HDL - TG/5 (excluded if TG>400) |

---

## 4. Statistical Methods

### 4.1 Survey Design

NHANES uses a complex, multistage probability sampling design. All analyses accounted for:

- **Stratification:** SDMVSTRA
- **Primary Sampling Units:** SDMVPSU
- **Sample Weights:** WTMEC2YR (MEC examined weights)

### 4.2 Software

- **Primary analysis:** R 4.4.1 with `survey` package
- **Variance estimation:** Taylor series linearization
- **Lonely PSU handling:** Certainty adjustment

### 4.3 Age Standardization

Used 2000 U.S. Standard Population weights:

| Age Group | Weight |
|-----------|--------|
| 20-29 | 0.1318 |
| 30-39 | 0.1342 |
| 40-49 | 0.1354 |
| 50-59 | 0.0933 |
| 60-69 | 0.0640 |
| 70-79 | 0.0463 |
| 80+ | 0.0229 |

### 4.4 Trend Analysis

Linear trend tested via survey-weighted logistic regression:
```
logit(CHD) ~ era_num
```
Where era_num = 1, 2, 3, 4, 5 for the five eras.

---

## 5. Results

### 5.1 CHD Prevalence by Era (Survey-Weighted)

| Era | Period | Prevalence | 95% CI | n |
|-----|--------|------------|--------|---|
| Era 1 | 1988-1994 | **5.45%** | 4.95-5.96% | 16,552 |
| Era 2 | 1999-2006 | **6.19%** | 5.62-6.75% | 20,196 |
| Era 3 | 2007-2014 | **5.65%** | 5.24-6.06% | 23,390 |
| Era 4a | 2015-2020 | **6.09%** | 5.03-7.15% | 5,688 |
| Era 4b | 2021-2023 | **6.26%** | 5.49-7.04% | 7,772 |

### 5.2 Trend Test

| Parameter | Estimate | Std. Error | p-value |
|-----------|----------|------------|---------|
| Intercept | -2.80 | 0.066 | <0.001 |
| Era (linear) | 0.011 | 0.022 | **0.62** |

**Interpretation:** No statistically significant linear trend in CHD prevalence over 35 years.

### 5.3 CHD Prevalence by Sex

| Era | Males | Females |
|-----|-------|---------|
| 1988-1994 | 4.8% | 6.1% |
| 1999-2006 | 7.4% | 5.1% |
| 2007-2014 | 7.1% | 4.3% |
| 2015-2020 | 7.1% | 5.2% |
| 2021-2023 | 8.1% | 4.6% |

**Note:** Era 1 shows reversed sex pattern (F>M), which may reflect differences in NHANES III methodology or sampling.

### 5.4 CHD Prevalence by Race/Ethnicity (1999-2023 Only)

| Race/Ethnicity | Range Across Eras |
|----------------|-------------------|
| Non-Hispanic White | 6.4-7.6% |
| Non-Hispanic Black | 4.1-5.2% |
| Mexican American | 2.5-3.3% |
| Other Hispanic | 3.5-4.6% |
| Other/Multiracial | 4.4-6.5% |

---

## 6. Limitations

1. **Self-reported CHD:** NHANES relies on participant recall of physician diagnosis
2. **NHANES III methodology:** Era 1 used different questionnaire administration
3. **Pre-pandemic disruption:** NHANES 2019-2020 was truncated; combined with 2017-2018
4. **Cross-sectional design:** Cannot establish incidence or causation
5. **Weight harmonization:** Different weight schemes across cycles partially addressed by era-specific analyses

---

## 7. Technical Implementation

### 7.1 Data Pipeline

```
01_download_data_fixed.py    → Downloads Continuous NHANES (1999-2023)
05_nhanes_iii_processor.py   → Downloads NHANES III (1988-1994)
06_nhanes_iii_harmonize.py   → Harmonizes NHANES III variables
02_harmonize_variables.py    → Creates unified dataset
04_R_survey_analysis.R       → Survey-weighted analysis
```

### 7.2 Output Files

| File | Description |
|------|-------------|
| `nhanes_chd_full_35year.parquet` | Complete harmonized dataset (139,605 participants) |
| `R_survey_prevalence_by_era.csv` | Main results with CIs |
| `R_survey_prevalence_by_sex.csv` | Sex-stratified results |

### 7.3 GitHub Repository

All code is available at: **https://github.com/andrewbouras/NHANESv2**

---

## 8. Next Steps (For Consideration)

1. **Age-standardized prevalence table** by era
2. **Risk factor analysis:** Prevalence of HTN, DM, obesity among CHD cases
3. **Mortality linkage:** NHANES Linked Mortality Files (follow-up through 2019)
4. **Subgroup analyses:** Age-stratified, education/SES-stratified
5. **Joinpoint regression:** Alternative trend analysis approach

---

## 9. Appendix: Key Decisions Made

| Question | Decision | Rationale |
|----------|----------|-----------|
| Era 4 pandemic split? | Yes, split into 4a/4b | Per PI - isolate pandemic effect |
| Mortality linkage? | Deferred | Focus on prevalence first |
| Physical activity? | Not included | Questionnaire changed too much |
| LDL calculation? | Friedewald equation | Standard practice; noted TG>400 exclusion |
| Age standardization? | 2000 US Standard | NCHS convention |
| Missing data? | Complete case | Standard NHANES approach |

---

**Prepared by:** Biostatistics Team  
**Analysis Date:** December 23, 2024  
**Software:** R 4.4.1 (survey 4.2), Python 3.11
