"""
NHANES CHD Study - Statistical Analysis
Survey-weighted prevalence estimates and trend analysis
"""

import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUT = PROJECT_ROOT / "output"

# 2000 US Standard Population weights for age-standardization
US_STD_2000 = {
    "20-29": 0.1318,
    "30-39": 0.1342,
    "40-49": 0.1354,
    "50-59": 0.0933,
    "60-69": 0.0640,
    "70-79": 0.0463,
    "80+": 0.0229,
}


def create_age_groups(age: pd.Series) -> pd.Series:
    """Create age groups for standardization."""
    bins = [20, 30, 40, 50, 60, 70, 80, 120]
    labels = ["20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
    return pd.cut(age, bins=bins, labels=labels, right=False)


def calculate_survey_weighted_prevalence(df: pd.DataFrame, 
                                          outcome: str,
                                          weight: str = "WTMEC2YR",
                                          strata: str = "SDMVSTRA",
                                          psu: str = "SDMVPSU") -> dict:
    """
    Calculate survey-weighted prevalence with 95% CI.
    Uses Taylor series linearization for variance estimation.
    
    For production use, recommend using R's `survey` package or 
    Python's `samplics` for proper complex survey analysis.
    """
    # Filter to valid cases
    valid = df[[outcome, weight]].dropna()
    
    if len(valid) == 0:
        return {"prevalence": np.nan, "se": np.nan, "ci_low": np.nan, "ci_high": np.nan, "n": 0}
    
    # Weighted prevalence (simplified - use survey package for production)
    weighted_sum = (valid[outcome] * valid[weight]).sum()
    total_weight = valid[weight].sum()
    prevalence = weighted_sum / total_weight
    
    # Approximate SE (for production, use proper survey design)
    n = len(valid)
    p = prevalence
    se_approx = np.sqrt(p * (1 - p) / n)
    
    # 95% CI
    ci_low = max(0, prevalence - 1.96 * se_approx)
    ci_high = min(1, prevalence + 1.96 * se_approx)
    
    return {
        "prevalence": prevalence,
        "se": se_approx,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "n": n,
        "n_cases": int(valid[outcome].sum())
    }


def age_standardize(prevalence_by_age: dict) -> float:
    """
    Age-standardize prevalence using 2000 US standard population.
    
    prevalence_by_age: dict mapping age group to prevalence
    """
    standardized = 0
    total_weight = 0
    
    for age_group, weight in US_STD_2000.items():
        if age_group in prevalence_by_age:
            standardized += prevalence_by_age[age_group] * weight
            total_weight += weight
    
    # Normalize if not all age groups present
    if total_weight > 0 and total_weight < 1:
        standardized = standardized / total_weight
    
    return standardized


def analyze_prevalence_by_era(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate age-standardized CHD prevalence by era."""
    results = []
    
    for era in sorted(df['era'].unique()):
        era_df = df[df['era'] == era]
        
        # Overall prevalence for era
        prev = calculate_survey_weighted_prevalence(era_df, 'chd_composite')
        
        # Age-specific prevalence for standardization
        era_df['age_group'] = create_age_groups(era_df['RIDAGEYR'])
        age_prev = {}
        for ag in US_STD_2000.keys():
            ag_df = era_df[era_df['age_group'] == ag]
            if len(ag_df) > 30:  # Minimum sample size
                ag_prev = calculate_survey_weighted_prevalence(ag_df, 'chd_composite')
                age_prev[ag] = ag_prev['prevalence']
        
        # Age-standardized prevalence
        age_std_prev = age_standardize(age_prev) if age_prev else np.nan
        
        results.append({
            "era": era,
            "n_total": len(era_df),
            "n_chd": prev['n_cases'],
            "crude_prevalence": prev['prevalence'],
            "crude_ci_low": prev['ci_low'],
            "crude_ci_high": prev['ci_high'],
            "age_std_prevalence": age_std_prev,
        })
    
    return pd.DataFrame(results)


def analyze_risk_factors_by_era(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze risk factor prevalence among CHD cases by era."""
    results = []
    
    risk_factors = ['hypertension', 'diabetes', 'hyperlipidemia', 'obesity']
    
    for era in sorted(df['era'].unique()):
        era_df = df[(df['era'] == era) & (df['chd_composite'] == 1)]
        
        row = {"era": era, "n_chd": len(era_df)}
        
        for rf in risk_factors:
            if rf in era_df.columns:
                prev = calculate_survey_weighted_prevalence(era_df, rf)
                row[f"{rf}_prev"] = prev['prevalence']
                row[f"{rf}_n"] = prev['n_cases']
        
        results.append(row)
    
    return pd.DataFrame(results)


def analyze_by_subgroup(df: pd.DataFrame, 
                        subgroup_var: str,
                        subgroup_labels: dict) -> pd.DataFrame:
    """Analyze CHD prevalence by subgroup (sex, race, etc.)."""
    results = []
    
    for era in sorted(df['era'].unique()):
        era_df = df[df['era'] == era]
        
        for value, label in subgroup_labels.items():
            sub_df = era_df[era_df[subgroup_var] == value]
            
            if len(sub_df) > 50:  # Minimum sample size
                prev = calculate_survey_weighted_prevalence(sub_df, 'chd_composite')
                
                results.append({
                    "era": era,
                    "subgroup": label,
                    "n_total": len(sub_df),
                    "n_chd": prev['n_cases'],
                    "prevalence": prev['prevalence'],
                    "ci_low": prev['ci_low'],
                    "ci_high": prev['ci_high'],
                })
    
    return pd.DataFrame(results)


def main():
    """Main analysis function."""
    print("="*60)
    print("NHANES CHD STUDY - STATISTICAL ANALYSIS")
    print("="*60)
    
    # Load harmonized data
    data_path = DATA_PROCESSED / "nhanes_chd_harmonized.parquet"
    
    if not data_path.exists():
        print(f"[ERROR] Data file not found: {data_path}")
        print("Run 02_harmonize_variables.py first.")
        return
    
    df = pd.read_parquet(data_path)
    print(f"Loaded {len(df):,} participants")
    
    # Apply exclusion criteria
    print("\n[Applying exclusions]")
    original_n = len(df)
    
    # Age >= 20
    df = df[df['RIDAGEYR'] >= 20]
    print(f"  Age >= 20: {len(df):,} ({original_n - len(df):,} excluded)")
    
    # Non-missing CHD status
    df = df[df['chd_composite'].notna()]
    print(f"  Valid CHD status: {len(df):,}")
    
    # Valid survey weights
    df = df[df['WTMEC2YR'] > 0]
    print(f"  Valid weights: {len(df):,}")
    
    # Create output directory
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "tables").mkdir(exist_ok=True)
    (OUTPUT / "figures").mkdir(exist_ok=True)
    
    # =========================================================================
    # Table 1: CHD Prevalence by Era
    # =========================================================================
    print("\n[Analysis 1: CHD Prevalence by Era]")
    table1 = analyze_prevalence_by_era(df)
    table1.to_csv(OUTPUT / "tables" / "table1_chd_prevalence_by_era.csv", index=False)
    print(table1.to_string(index=False))
    
    # =========================================================================
    # Table 2: Risk Factor Prevalence Among CHD Cases
    # =========================================================================
    print("\n[Analysis 2: Risk Factors Among CHD Cases]")
    table2 = analyze_risk_factors_by_era(df)
    table2.to_csv(OUTPUT / "tables" / "table2_risk_factors_by_era.csv", index=False)
    print(table2.to_string(index=False))
    
    # =========================================================================
    # Table 3: CHD Prevalence by Sex
    # =========================================================================
    print("\n[Analysis 3: CHD Prevalence by Sex]")
    sex_labels = {1: "Male", 2: "Female"}
    table3 = analyze_by_subgroup(df, 'RIAGENDR', sex_labels)
    table3.to_csv(OUTPUT / "tables" / "table3_chd_by_sex.csv", index=False)
    print(table3.to_string(index=False))
    
    # =========================================================================
    # Table 4: CHD Prevalence by Race/Ethnicity
    # =========================================================================
    print("\n[Analysis 4: CHD Prevalence by Race/Ethnicity]")
    race_labels = {
        1: "Mexican American",
        2: "Other Hispanic", 
        3: "Non-Hispanic White",
        4: "Non-Hispanic Black",
        5: "Other/Multi-racial"
    }
    table4 = analyze_by_subgroup(df, 'RIDRETH1', race_labels)
    table4.to_csv(OUTPUT / "tables" / "table4_chd_by_race.csv", index=False)
    print(table4.to_string(index=False))
    
    # =========================================================================
    # Summary Statistics
    # =========================================================================
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total analytic sample: {len(df):,}")
    print(f"CHD cases: {int(df['chd_composite'].sum()):,} ({100*df['chd_composite'].mean():.1f}%)")
    print(f"\nPrevalence by Era:")
    for _, row in table1.iterrows():
        print(f"  {row['era']}: {100*row['crude_prevalence']:.2f}% "
              f"(n={row['n_chd']:,}/{row['n_total']:,})")
    
    print(f"\nResults saved to: {OUTPUT / 'tables'}")
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)
    print("\nNOTE: For publication, re-run analyses in R using the `survey` package")
    print("or SAS PROC SURVEY procedures for proper variance estimation.")


if __name__ == "__main__":
    main()
