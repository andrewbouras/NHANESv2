# NHANES CHD Prevalence Trends Study (1988-2023)

A comprehensive analysis of 35-year trends in coronary heart disease (CHD) prevalence using NHANES data.

## Study Overview

This project analyzes CHD prevalence across five eras spanning 35 years:

| Era | Period | Sample | CHD Prevalence |
|-----|--------|--------|---------------|
| Era 1 | 1988-1994 | 16,552 | 5.5% (5.0-6.0%) |
| Era 2 | 1999-2006 | 20,196 | 6.2% (5.6-6.8%) |
| Era 3 | 2007-2014 | 23,390 | 5.7% (5.2-6.1%) |
| Era 4a | 2015-2020 | 5,688 | 6.1% (5.0-7.2%) |
| Era 4b | 2021-2023 | 7,772 | 6.3% (5.5-7.0%) |

**Total: 73,598 adults ≥20 years**

## Key Findings

1. **No significant secular trend** (p=0.62) in CHD prevalence over 35 years
2. **Persistent sex disparity**: Males 7-8% vs Females 4-6%
3. **Post-pandemic prevalence**: Slight increase to 6.3% (not statistically significant)

## Project Structure

```
├── data/
│   ├── raw/           # Downloaded NHANES XPT files (~300MB)
│   └── processed/     # Harmonized parquet files
├── scripts/
│   ├── 01_download_data_fixed.py    # Download Continuous NHANES
│   ├── 02_harmonize_variables.py    # Variable crosswalk
│   ├── 03_statistical_analysis.py   # Python analysis
│   ├── 04_R_survey_analysis.R       # R survey-weighted analysis
│   ├── 05_nhanes_iii_processor.py   # NHANES III download
│   └── 06_nhanes_iii_harmonize.py   # NHANES III processing
├── output/
│   └── tables/        # Results CSV files
└── README.md
```

## Quick Start

### Prerequisites
- Python 3.8+
- R 4.0+ with `survey` and `arrow` packages
- pandas, numpy, requests, beautifulsoup4

### Installation

```bash
pip install pandas numpy pyarrow requests beautifulsoup4

# R packages
R -e "install.packages(c('survey', 'arrow'))"
```

### Running the Analysis

```bash
# 1. Download NHANES data (Continuous 1999-2023)
python scripts/01_download_data_fixed.py

# 2. Download and process NHANES III (1988-1994)
python scripts/05_nhanes_iii_processor.py
python scripts/06_nhanes_iii_harmonize.py

# 3. Harmonize all data
python scripts/02_harmonize_variables.py

# 4. Run survey-weighted analysis (publication-ready)
Rscript scripts/04_R_survey_analysis.R
```

## Methodology

### CHD Definition
Composite of affirmative response to any:
- Coronary heart disease (MCQ160C / HAD1)
- Angina (MCQ160D / HAD2)  
- Heart attack (MCQ160E / HAD3)

### Analysis
- **Weighting**: Complex survey design using Taylor series linearization
- **Age standardization**: 2000 U.S. Standard Population
- **Software**: R `survey` package for variance estimation

## Data Sources

- [NHANES Continuous (1999-2023)](https://wwwn.cdc.gov/nchs/nhanes/Default.aspx)
- [NHANES III (1988-1994)](https://wwwn.cdc.gov/nchs/nhanes/nhanes3/default.aspx)

## Output Files

- `R_survey_prevalence_by_era.csv` - Main prevalence estimates with 95% CIs
- `R_survey_prevalence_by_sex.csv` - Sex-stratified results

## License

This project uses publicly available NHANES data from the CDC/NCHS.

## Citation

If using this code, please cite the NHANES documentation and this repository.
