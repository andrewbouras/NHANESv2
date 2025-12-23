# NHANES CHD Prevalence Trends Study
## Technical Report

**Prepared for:** Principal Investigator  
**Date:** December 23, 2024  
**Repository:** https://github.com/andrewbouras/NHANESv2

---

## Executive Summary

This analysis examines 35 years of coronary heart disease (CHD) trends using NHANES data from 1988 through 2023. We included 73,598 adults across five eras, with an overall crude prevalence of 5.9% (95% CI: 5.7–6.2%).

The main takeaway: **CHD prevalence has actually been declining**, but you wouldn't know it from the crude numbers. After age-standardizing, prevalence dropped from 5.5% in the late 1980s to 4.8% in the most recent cycle (p < 0.001 for trend). The crude estimates look flat because the US population has aged considerably over this period—older adults have higher CHD rates, which masks the underlying decline.

We also found that disparities persist. Non-Hispanic White adults consistently have the highest prevalence (~7%), while Mexican American adults have the lowest (~3%). The male-female gap is consistent across recent eras, though NHANES III shows an unusual reversed pattern that's worth noting but hard to interpret.

---

## 1. Study Design

### Era Definitions

We grouped NHANES cycles into five eras based on methodology and the pandemic disruption:

| Era | Years | What's Included | Why This Grouping |
|-----|-------|-----------------|-------------------|
| 1 | 1988–1994 | NHANES III | Baseline—different design than continuous NHANES |
| 2 | 1999–2006 | Four 2-year cycles | Early continuous NHANES |
| 3 | 2007–2014 | Four 2-year cycles | Mid-period continuous NHANES |
| 4a | 2015–March 2020 | Two cycles, truncated | Pre-pandemic (2019–20 cut short) |
| 4b | Aug 2021–Aug 2023 | Post-pandemic restart | Separate to isolate any pandemic effects |

The PI specifically requested splitting Era 4 to see if COVID had any visible impact on CHD prevalence patterns.

### Who's Included

We started with 139,605 participants in the harmonized dataset. After limiting to adults 20+ with non-missing CHD data and valid MEC weights, we ended up with 73,598—a pretty typical attrition for this kind of NHANES analysis.

---

## 2. Data Sources

### Cycles and Sample Sizes

NHANES III (1988–94) used fixed-width ASCII files that required separate processing. Everything from 1999 onward uses SAS transport format, which is more straightforward.

| Cycle | Approx. n | Format |
|-------|-----------|--------|
| NHANES III | 16,552 | ASCII |
| 1999–2000 through 2015–2016 | ~5,000 each | XPT |
| 2017–March 2020 | ~5,700 | XPT |
| Aug 2021–Aug 2023 | ~7,700 | XPT |

### Variables Used

From demographics: age, sex, race/ethnicity, PIR, and of course the survey design variables (strata, PSU, weights).

From questionnaires: the three CHD questions (MCQ160C/D/E), plus blood pressure, diabetes status, and smoking for future risk factor analyses.

From labs: lipids, HbA1c, fasting glucose where available.

---

## 3. Variable Definitions

### CHD (Primary Outcome)

We used a composite definition: anyone who said "yes" to having been told they have coronary heart disease, angina, OR had a heart attack. Standard NHANES coding (1=Yes, 2=No).

| Component | Continuous NHANES | NHANES III | Question Wording |
|-----------|-------------------|------------|------------------|
| CHD | MCQ160C | HAD1 | "Ever told you had coronary heart disease?" |
| Angina | MCQ160D | HAD2 | "Ever told you had angina?" |
| MI | MCQ160E | HAD3 | "Ever told you had a heart attack?" |

These aren't mutually exclusive—someone can report all three. We counted them as CHD-positive if they endorsed any of them.

### Covariates

Standard demographics from DEMO files: age at exam (RIDAGEYR), sex (RIAGENDR), race/ethnicity (RIDRETH1—the 5-category version), education (DMDEDUC2), and family poverty-income ratio (INDFMPIR).

### Risk Factor Definitions (for later)

We've set up definitions for future analyses:
- Hypertension: SBP ≥130 or DBP ≥80 or on BP meds
- Diabetes: A1c ≥6.5% or FPG ≥126 or on diabetes meds
- Hyperlipidemia: TC ≥200 or LDL ≥130
- Obesity: BMI ≥30
- LDL: Friedewald calculation (excluded if triglycerides >400)

---

## 4. Statistical Methods

### Survey Design

NHANES is complex survey data, so all analyses use the survey package in R with stratification (SDMVSTRA), clustering (SDMVPSU), and MEC exam weights (WTMEC2YR). Variance estimation via Taylor series linearization. For lonely PSUs, we used the certainty adjustment.

### Handling Weights Across Eras

This is always a headache with multi-cycle NHANES analyses. Here's what we did:

| Era | Approach |
|-----|----------|
| Era 1 | NHANES III weights used as-is (designed as 6-year survey) |
| Eras 2 & 3 | Combined four 2-year cycles by dividing WTMEC2YR by 4 |
| Era 4a | Used the NCHS pre-pandemic combined weights |
| Era 4b | Used NCHS weights for the 2021–2023 sample per their guidance for the revised design |

### Age Standardization

Direct standardization to the 2000 US Standard Population, restricted to ages 20+ and renormalized to sum to 1:

| Age Group | Weight |
|-----------|--------|
| 20–29 | 0.190 |
| 30–39 | 0.193 |
| 40–49 | 0.195 |
| 50–59 | 0.134 |
| 60–69 | 0.092 |
| 70–79 | 0.067 |
| 80+ | 0.033 |

For each era, we computed age-specific prevalences and then weighted them by these standard population shares.

### Trend Testing

Our primary model is age-adjusted logistic regression:

```
logit(CHD) ~ era_num + age_cat
```

Here `era_num` is just 1 through 5, and `age_cat` uses the same age groups as the standardization. This tests whether there's a linear trend after accounting for the different age distributions across survey periods.

We think of it this way: the age-standardized prevalence estimates (Table 5.1) tell you *what* the burden looks like if age distributions were the same, while the regression model tells you *whether* there's a statistically significant trend and gives you an odds ratio.

We also ran the unadjusted model for comparison.

### Software

R 4.4.1 with the survey package (v4.2) for all weighted analyses. Python 3.11 for data processing.

---

## 5. Results

### 5.1 Age-Standardized Prevalence

This is the primary table—what prevalence would look like if every era had the same age distribution:

| Era | Period | Prevalence | 95% CI | n |
|-----|--------|------------|--------|---|
| 1 | 1988–1994 | 5.51% | 5.03–5.99% | 16,552 |
| 2 | 1999–2006 | 5.98% | 5.60–6.36% | 20,196 |
| 3 | 2007–2014 | 4.98% | 4.68–5.27% | 23,390 |
| 4a | 2015–March 2020 | 5.04% | 4.42–5.66% | 5,688 |
| 4b | Aug 2021–Aug 2023 | 4.80% | 4.32–5.28% | 7,772 |

The pattern here is clearer than the crude numbers—there's a real decline, especially visible from Era 2 onward.

### 5.2 Crude Prevalence (for reference)

| Era | Period | Prevalence | 95% CI | n |
|-----|--------|------------|--------|---|
| 1 | 1988–1994 | 5.45% | 4.95–5.96% | 16,552 |
| 2 | 1999–2006 | 6.19% | 5.62–6.75% | 20,196 |
| 3 | 2007–2014 | 5.65% | 5.24–6.06% | 23,390 |
| 4a | 2015–March 2020 | 6.09% | 5.03–7.15% | 5,688 |
| 4b | Aug 2021–Aug 2023 | 6.26% | 5.49–7.04% | 7,772 |

These look basically flat—the aging population is masking real declines.

### 5.3 Trend Tests

| Model | Era Coefficient | SE | p-value |
|-------|----------------|-----|---------|
| Age-adjusted | -0.067 | 0.019 | <0.001 |
| Unadjusted | 0.011 | 0.022 | 0.62 |

The age-adjusted coefficient translates to about a 6.5% decrease in odds per era (OR ≈ 0.94). This is testing a strictly linear trend and wouldn't pick up non-monotonic patterns if they exist.

### 5.4 By Sex

| Era | Period | Males | Females |
|-----|--------|-------|---------|
| 1 | 1988–1994 | 4.76% (4.22–5.30%) | 6.09% (5.25–6.92%) |
| 2 | 1999–2006 | 7.39% (6.53–8.24%) | 5.08% (4.45–5.72%) |
| 3 | 2007–2014 | 7.09% (6.47–7.71%) | 4.30% (3.85–4.76%) |
| 4a | 2015–March 2020 | 7.07% (5.70–8.44%) | 5.19% (4.02–6.35%) |
| 4b | Aug 2021–Aug 2023 | 8.08% (6.88–9.29%) | 4.56% (3.78–5.33%) |

Note the flipped pattern in Era 1—women had higher prevalence than men. We double-checked the coding; it's not an error. Likely reflects something about NHANES III methodology or how CHD was diagnosed/reported in that era. From Era 2 onward, the expected pattern holds.

These are crude estimates. We can generate age-standardized versions by sex if needed.

### 5.5 By Race/Ethnicity (1999–2023)

We're only showing continuous NHANES here because the race categories changed between NHANES III and later cycles.

| Group | Era 2 | Era 3 | Era 4a | Era 4b |
|-------|-------|-------|--------|--------|
| NH White | 7.03% (6.38–7.68%) | 6.40% (5.83–6.98%) | 6.80% (5.17–8.44%) | 7.57% (6.50–8.65%) |
| NH Black | 5.18% (4.45–5.91%) | 4.57% (4.00–5.15%) | 5.33% (4.00–6.67%) | 4.08% (3.07–5.09%) |
| Mexican American | 2.81% (2.34–3.27%) | 3.28% (2.67–3.90%) | 2.52% (1.49–3.56%) | 2.95% (1.57–4.32%) |
| Other Hispanic | 3.08% (2.35–3.81%) | 3.89% (3.06–4.72%) | 4.62% (3.59–5.66%) | 4.36% (2.38–6.34%) |
| Other/Multi | 4.54% (2.52–6.55%) | 4.36% (3.31–5.42%) | 6.51% (3.27–9.76%) | 5.22% (3.43–7.00%) |

The pattern is consistent: NH White adults have the highest prevalence, Mexican American the lowest. The gap is 3–4 percentage points throughout.

---

## 6. Limitations

**Self-report.** This is the big one—we're relying on people remembering whether a doctor told them they have CHD. Recall bias and diagnostic access both matter here.

**NHANES III differences.** Era 1 used different interview methods. That flipped sex pattern might be real or might be methodological. Hard to know for sure.

**Pandemic disruption.** The 2019–20 cycle got cut short. We combined it with 2017–18 per NCHS guidance, but Era 4a has smaller n than we'd like.

**Cross-sectional data.** We can describe prevalence but can't say anything about incidence. Changes in survival, diagnostic criteria, and awareness over 35 years all feed into prevalence trends in ways we can't disentangle.

**Weight harmonization.** We followed NCHS guidance throughout (see Section 4.2), but combining weights across different survey designs is always imperfect.

**Linear trend.** Our test assumes monotonic change. If there were ups and downs, we'd miss that.

---

## 7. Technical Details

### Pipeline

```
01_download_data_fixed.py    → Continuous NHANES (1999–2023)
05_nhanes_iii_processor.py   → NHANES III download
06_nhanes_iii_harmonize.py   → NHANES III variable mapping
02_harmonize_variables.py    → Combine everything
04_R_survey_analysis.R       → Analysis with survey weights
```

### Output Files

| File | What It Contains |
|------|------------------|
| `nhanes_chd_full_35year.parquet` | Full harmonized dataset (n=139,605) |
| `R_age_standardized_prevalence_by_era.csv` | Age-standardized estimates |
| `R_survey_prevalence_by_era.csv` | Crude estimates |
| `R_survey_prevalence_by_sex.csv` | Sex-stratified |
| `R_survey_prevalence_by_race.csv` | Race/ethnicity-stratified |
| `R_trend_test_results.csv` | Model coefficients |

---

## 8. What's Next

A few things we're thinking about:

1. **Risk factor trends** — How have HTN, diabetes, and obesity among CHD cases changed over time?
2. **Mortality linkage** — NHANES has linked mortality through 2019. Could look at survival patterns.
3. **Subgroup analyses** — Trends by age group, education, income
4. **Sensitivity checks** — Try narrower CHD definitions (MI only, for instance)
5. **Non-linear models** — Categorical era terms, maybe joinpoint regression

---

## 9. Decisions Log

| Issue | What We Did | Why |
|-------|-------------|-----|
| Split Era 4? | Yes, 4a vs 4b | PI wanted to see pandemic effect separately |
| Mortality linkage | Not yet | Keeping focus on prevalence first |
| Physical activity | Excluded | Questionnaire changed too much across cycles |
| LDL calculation | Friedewald | Standard; excluded TG >400 |
| Age standardization | 2000 US Standard Pop | NCHS convention |
| Missing data | Complete case | Standard for NHANES |
| Trend model | Age-adjusted | Necessary given 35-year age shift |

---

## Appendix: Methods Paragraph for Manuscripts

> We analyzed data from NHANES III (1988–1994) and continuous NHANES (1999–2023), including 73,598 adults aged 20 years or older with valid MEC examination weights and CHD outcome data. CHD was defined as self-reported diagnosis of coronary heart disease, angina, or myocardial infarction. We estimated age-standardized prevalence using direct standardization to the 2000 US Standard Population. Trend across five eras was assessed using survey-weighted logistic regression with era as a continuous predictor, adjusting for age category. All analyses incorporated NHANES complex survey design using the R survey package with Taylor series linearization.

---

*Analysis completed December 2024*  
*R 4.4.1 (survey 4.2) • Python 3.11*
