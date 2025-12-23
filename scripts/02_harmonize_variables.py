"""
NHANES CHD Study - Variable Harmonization
Creates unified variable definitions across all NHANES cycles (1988-2023)
"""

import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# ============================================================================
# VARIABLE HARMONIZATION CROSSWALK
# ============================================================================

# Era definitions
ERA_MAPPING = {
    "1988-1994": "Era1_1988-1994",
    "1999-2000": "Era2_1999-2006",
    "2001-2002": "Era2_1999-2006",
    "2003-2004": "Era2_1999-2006",
    "2005-2006": "Era2_1999-2006",
    "2007-2008": "Era3_2007-2014",
    "2009-2010": "Era3_2007-2014",
    "2011-2012": "Era3_2007-2014",
    "2013-2014": "Era3_2007-2014",
    "2015-2016": "Era4a_2015-2020",
    "2017-2020": "Era4a_2015-2020",
    "2021-2023": "Era4b_2021-2023",
}

# CHD outcome variable mapping
CHD_VARS = {
    # Continuous NHANES (1999+): MCQ file
    "continuous": {
        "chd": "MCQ160C",      # Ever told you had coronary heart disease
        "angina": "MCQ160D",  # Ever told you had angina
        "mi": "MCQ160E",      # Ever told you had heart attack
    },
    # NHANES III: Different variable names in Adult file
    "nhanes_iii": {
        "chd": "HAD1",        # Doctor told - coronary heart disease
        "angina": "HAD2",     # Doctor told - angina
        "mi": "HAD3",         # Doctor told - heart attack
    }
}

# Demographics variable mapping
DEMO_VARS = {
    "continuous": {
        "id": "SEQN",
        "age": "RIDAGEYR",
        "sex": "RIAGENDR",       # 1=Male, 2=Female
        "race_eth": "RIDRETH1",  # 1=Mexican American, 2=Other Hispanic, 3=NH White, 4=NH Black, 5=Other
        "race_eth3": "RIDRETH3", # More detailed (available 2011+)
        "education": "DMDEDUC2", # Adults 20+ education level
        "pir": "INDFMPIR",       # Family poverty income ratio
        "weight_interview": "WTINT2YR",
        "weight_exam": "WTMEC2YR",
        "psu": "SDMVPSU",
        "strata": "SDMVSTRA",
    },
    "nhanes_iii": {
        "id": "SEQN",
        "age": "HSAGEIR",
        "sex": "HSSEX",
        "race_eth": "DMARETHN",
        "education": "HFA8R",
        "pir": "DMPPIR",
        "weight_exam": "WTPFEX6",  # MEC examined weight - Phase 1 & 2
    }
}

# Cardiometabolic risk factor mapping
RISK_FACTOR_VARS = {
    "continuous": {
        # Blood pressure (examination)
        "sbp1": "BPXSY1",
        "sbp2": "BPXSY2", 
        "sbp3": "BPXSY3",
        "dbp1": "BPXDI1",
        "dbp2": "BPXDI2",
        "dbp3": "BPXDI3",
        
        # Blood pressure meds (questionnaire BPQ)
        "bp_med": "BPQ040A",  # Taking BP medication
        
        # Diabetes (questionnaire DIQ + labs)
        "diabetes_told": "DIQ010",
        "insulin_use": "DIQ050",
        "oral_dm_med": "DIQ070",
        
        # Labs
        "hba1c": "LBXGH",      # Glycohemoglobin (%)
        "glucose": "LBXGLU",  # Fasting glucose
        "tchol": "LBXTC",     # Total cholesterol
        "hdl": "LBDHDD",      # Direct HDL
        "trigly": "LBXTR",    # Triglycerides
        
        # Body measures
        "bmi": "BMXBMI",
        "weight": "BMXWT",
        "height": "BMXHT",
        
        # Smoking (SMQ)
        "smoke_100": "SMQ020",   # Smoked 100+ cigarettes in life
        "smoke_now": "SMQ040",   # Do you now smoke
    },
    "nhanes_iii": {
        # Blood pressure
        "sbp1": "PEPMNK1R",
        "sbp2": "PEPMNK2R",
        "dbp1": "PEPMNK1D",
        "dbp2": "PEPMNK2D",
        
        # Labs
        "hba1c": "GHP",
        "glucose": "G1P",
        "tchol": "TCP",
        "hdl": "HDP",
        "trigly": "TGP",
        
        # Body measures
        "bmi": "BMPBMI",
        
        # Smoking
        "smoke_100": "HAR1",
        "smoke_now": "HAR3",
    }
}

# Physical Activity mapping (simplified binary)
PA_VARS = {
    "continuous_2007plus": {
        # GPAQ format (2007+)
        "vigorous_work": "PAQ605",
        "vigorous_work_days": "PAQ610",
        "vigorous_work_min": "PAD615",
        "moderate_work": "PAQ620",
        "moderate_work_days": "PAQ625",
        "moderate_work_min": "PAD630",
        "vigorous_rec": "PAQ650",
        "vigorous_rec_days": "PAQ655",
        "vigorous_rec_min": "PAD660",
        "moderate_rec": "PAQ665",
        "moderate_rec_days": "PAQ670",
        "moderate_rec_min": "PAD675",
    },
    "continuous_1999_2006": {
        # Different PAQ format
        "moderate_activity": "PAQ180",
        "vigorous_activity": "PAQ100",
    }
}


def load_xpt(filepath: Path) -> pd.DataFrame:
    """Load XPT file into pandas DataFrame."""
    try:
        return pd.read_sas(filepath, format='xport', encoding='latin1')
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return pd.DataFrame()


def create_chd_composite(df: pd.DataFrame, var_type: str = "continuous") -> pd.Series:
    """
    Create composite CHD outcome: positive if ANY of CHD, angina, or MI = Yes (1).
    """
    vars = CHD_VARS[var_type]
    
    # Get individual conditions (1 = Yes, 2 = No in NHANES coding)
    chd = df.get(vars["chd"], pd.Series([np.nan] * len(df)))
    angina = df.get(vars["angina"], pd.Series([np.nan] * len(df)))
    mi = df.get(vars["mi"], pd.Series([np.nan] * len(df)))
    
    # Composite: 1 if any is 1 (Yes), 0 if all are 2 (No), NaN otherwise
    composite = pd.Series([np.nan] * len(df))
    
    # Any positive = CHD positive
    any_yes = (chd == 1) | (angina == 1) | (mi == 1)
    composite[any_yes] = 1
    
    # All negative = CHD negative
    all_no = (chd == 2) & (angina == 2) & (mi == 2)
    composite[all_no] = 0
    
    return composite


def calculate_ldl(df: pd.DataFrame) -> pd.Series:
    """
    Calculate LDL using Friedewald equation: LDL = TC - HDL - (TG/5)
    Only valid when TG < 400 mg/dL.
    """
    tc = df.get('tchol', pd.Series([np.nan] * len(df)))
    hdl = df.get('hdl', pd.Series([np.nan] * len(df)))
    tg = df.get('trigly', pd.Series([np.nan] * len(df)))
    
    ldl = tc - hdl - (tg / 5)
    
    # Set to NaN if TG >= 400 (Friedewald not valid)
    ldl[tg >= 400] = np.nan
    
    return ldl


def define_hypertension(df: pd.DataFrame) -> pd.Series:
    """
    Define hypertension per 2017 ACC/AHA guidelines:
    SBP >= 130 OR DBP >= 80 OR taking BP medication.
    """
    # Calculate mean SBP and DBP from available readings
    sbp_cols = [c for c in df.columns if c.startswith('sbp')]
    dbp_cols = [c for c in df.columns if c.startswith('dbp')]
    
    mean_sbp = df[sbp_cols].mean(axis=1) if sbp_cols else pd.Series([np.nan] * len(df))
    mean_dbp = df[dbp_cols].mean(axis=1) if dbp_cols else pd.Series([np.nan] * len(df))
    
    bp_med = df.get('bp_med', pd.Series([np.nan] * len(df)))
    
    # Hypertension: SBP >= 130 OR DBP >= 80 OR BP medication (1 = Yes in NHANES)
    htn = ((mean_sbp >= 130) | (mean_dbp >= 80) | (bp_med == 1)).astype(float)
    
    return htn


def define_diabetes(df: pd.DataFrame) -> pd.Series:
    """
    Define diabetes: HbA1c >= 6.5% OR FPG >= 126 OR using insulin/oral meds.
    """
    hba1c = df.get('hba1c', pd.Series([np.nan] * len(df)))
    glucose = df.get('glucose', pd.Series([np.nan] * len(df)))
    insulin = df.get('insulin_use', pd.Series([np.nan] * len(df)))
    oral_med = df.get('oral_dm_med', pd.Series([np.nan] * len(df)))
    diabetes_told = df.get('diabetes_told', pd.Series([np.nan] * len(df)))
    
    dm = ((hba1c >= 6.5) | 
          (glucose >= 126) | 
          (insulin == 1) | 
          (oral_med == 1) |
          (diabetes_told == 1)).astype(float)
    
    return dm


def define_hyperlipidemia(df: pd.DataFrame) -> pd.Series:
    """
    Define hyperlipidemia: TC >= 200 OR LDL >= 130.
    """
    tchol = df.get('tchol', pd.Series([np.nan] * len(df)))
    ldl = df.get('ldl_calc', pd.Series([np.nan] * len(df)))
    
    hyperlip = ((tchol >= 200) | (ldl >= 130)).astype(float)
    
    return hyperlip


def define_obesity(df: pd.DataFrame) -> pd.Series:
    """Define obesity: BMI >= 30."""
    bmi = df.get('bmi', pd.Series([np.nan] * len(df)))
    return (bmi >= 30).astype(float)


def define_smoking_status(df: pd.DataFrame) -> pd.Series:
    """
    Define smoking status: 1=Current, 2=Former, 3=Never.
    """
    smoke_100 = df.get('smoke_100', pd.Series([np.nan] * len(df)))
    smoke_now = df.get('smoke_now', pd.Series([np.nan] * len(df)))
    
    status = pd.Series([np.nan] * len(df))
    
    # Never: didn't smoke 100+ cigarettes
    status[smoke_100 == 2] = 3  # Never
    
    # Current: smoked 100+ and currently smokes (1=every day, 2=some days)
    status[(smoke_100 == 1) & (smoke_now.isin([1, 2]))] = 1  # Current
    
    # Former: smoked 100+ but not at all now (3=not at all)
    status[(smoke_100 == 1) & (smoke_now == 3)] = 2  # Former
    
    return status


def process_cycle(cycle: str, files: dict) -> pd.DataFrame:
    """Process a single NHANES cycle and return harmonized data."""
    print(f"\n[Processing {cycle}]")
    
    cycle_dir = DATA_RAW / cycle
    
    # Initialize with demographics - handle both cases
    demo_file = list(cycle_dir.glob("DEMO*.xpt")) + list(cycle_dir.glob("DEMO*.XPT")) + list(cycle_dir.glob("P_DEMO*.xpt")) + list(cycle_dir.glob("P_DEMO*.XPT"))
    if not demo_file:
        print(f"  No DEMO file found for {cycle}")
        return pd.DataFrame()
    
    df = load_xpt(demo_file[0])
    print(f"  Loaded {len(df)} participants")
    
    # Merge other files - handle both cases
    for component in ['MCQ', 'BPQ', 'DIQ', 'SMQ', 'PAQ', 'BMX', 'BPX', 'GHB', 'GLU', 'TCHOL', 'HDL', 'TRIGLY']:
        files = list(cycle_dir.glob(f"*{component}*.xpt")) + list(cycle_dir.glob(f"*{component}*.XPT"))
        if files:
            comp_df = load_xpt(files[0])
            if 'SEQN' in comp_df.columns and len(comp_df) > 0:
                df = df.merge(comp_df, on='SEQN', how='left', suffixes=('', f'_{component}'))
    
    # Add cycle and era info
    df['cycle'] = cycle
    df['era'] = ERA_MAPPING.get(cycle, 'Unknown')
    
    return df


def main():
    """Main processing function."""
    print("="*60)
    print("NHANES CHD STUDY - VARIABLE HARMONIZATION")
    print("="*60)
    
    all_data = []
    
    # Process all Continuous NHANES cycles
    cycles = ["1999-2000", "2001-2002", "2003-2004", "2005-2006",
              "2007-2008", "2009-2010", "2011-2012", "2013-2014",
              "2015-2016", "2017-2020", "2021-2023"]
    
    for cycle in cycles:
        cycle_dir = DATA_RAW / cycle
        if cycle_dir.exists():
            df = process_cycle(cycle, {})
            if len(df) > 0:
                all_data.append(df)
    
    # Combine all cycles
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        
        # Create derived variables
        print("\n[Creating derived variables]")
        combined['chd_composite'] = create_chd_composite(combined)
        combined['ldl_calc'] = calculate_ldl(combined)
        combined['hypertension'] = define_hypertension(combined)
        combined['diabetes'] = define_diabetes(combined)
        combined['hyperlipidemia'] = define_hyperlipidemia(combined)
        combined['obesity'] = define_obesity(combined)
        combined['smoking_status'] = define_smoking_status(combined)
        
        # Save processed data
        DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
        output_path = DATA_PROCESSED / "nhanes_chd_harmonized.parquet"
        combined.to_parquet(output_path)
        print(f"\n[Saved] {output_path}")
        print(f"Total participants: {len(combined):,}")
        print(f"Eras: {combined['era'].value_counts().to_dict()}")
    
    print("\n" + "="*60)
    print("HARMONIZATION COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
