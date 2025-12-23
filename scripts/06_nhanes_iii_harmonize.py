"""
NHANES III (1988-1994) Data Processor
Reads fixed-width ASCII files using known column positions
"""

import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw" / "NHANES_III"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# Variable positions from adult.sas INPUT statement
# Format: (start_col, end_col) - 1-indexed
NHANES_III_ADULT_VARS = {
    "SEQN":     (1, 5),      # Sequence number
    "DMARETHN": (12, 12),    # Race/ethnicity: 1=NH White, 2=NH Black, 3=Mexican American, 4=Other
    "HSSEX":    (15, 15),    # Sex: 1=Male, 2=Female
    "HSAGEIR":  (18, 19),    # Age in years
    "DMPPIR":   (36, 41),    # Poverty income ratio
    "SDPSTRA6": (44, 45),    # Stratum
    "SDPPSU6":  (43, 43),    # PSU
    "WTPFEX6":  (61, 69),    # MEC examined weight - Phase 1 & 2
    "HAD1":     (1561, 1561), # CHD: 1=Yes, 2=No
    "HAD2":     (1562, 1562), # Angina: 1=Yes, 2=No
    "HAD3":     (1563, 1563), # Heart attack: 1=Yes, 2=No
    "HAR1":     (1707, 1707), # Smoked 100+ cigarettes
    "HAR3":     (1712, 1712), # Do you smoke now
}


def read_nhanes_iii_adult(dat_file: Path) -> pd.DataFrame:
    """Read NHANES III adult file using fixed-width format."""
    print(f"[Reading {dat_file.name}...]")
    
    # Convert to 0-indexed colspecs for pandas
    colspecs = [(v[0]-1, v[1]) for v in NHANES_III_ADULT_VARS.values()]
    names = list(NHANES_III_ADULT_VARS.keys())
    
    try:
        df = pd.read_fwf(dat_file, colspecs=colspecs, names=names, encoding='latin1')
        print(f"  Loaded {len(df):,} participants")
        return df
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()


def harmonize_nhanes_iii(df: pd.DataFrame) -> pd.DataFrame:
    """Harmonize NHANES III variables to match Continuous NHANES."""
    print("[Harmonizing variables...]")
    
    # Rename to match Continuous NHANES
    df = df.rename(columns={
        "SEQN": "SEQN",
        "HSAGEIR": "RIDAGEYR",
        "HSSEX": "RIAGENDR",
        "DMARETHN": "RIDRETH1",  # Note: coding differs
        "DMPPIR": "INDFMPIR",
        "WTPFEX6": "WTMEC2YR",
        "SDPSTRA6": "SDMVSTRA",
        "SDPPSU6": "SDMVPSU",
    })
    
    # Recode race/ethnicity to match Continuous NHANES
    # NHANES III: 1=NH White, 2=NH Black, 3=Mexican American, 4=Other
    # Continuous: 1=Mexican American, 2=Other Hispanic, 3=NH White, 4=NH Black, 5=Other
    race_recode = {1: 3, 2: 4, 3: 1, 4: 5}
    df["RIDRETH1"] = df["RIDRETH1"].map(race_recode)
    
    # Create CHD composite outcome
    # HAD1=CHD, HAD2=angina, HAD3=heart attack
    # 1=Yes, 2=No in NHANES coding
    df["chd_composite"] = np.nan
    any_yes = (df["HAD1"] == 1) | (df["HAD2"] == 1) | (df["HAD3"] == 1)
    all_no = (df["HAD1"] == 2) & (df["HAD2"] == 2) & (df["HAD3"] == 2)
    df.loc[any_yes, "chd_composite"] = 1
    df.loc[all_no, "chd_composite"] = 0
    
    # Add era and cycle info
    df["era"] = "Era1_1988-1994"
    df["cycle"] = "1988-1994"
    
    return df


def main():
    """Main processing function."""
    print("\n" + "="*60)
    print("NHANES III DATA PROCESSOR")
    print("="*60)
    
    adult_dat = DATA_RAW / "adult.dat"
    
    if not adult_dat.exists():
        print(f"[ERROR] File not found: {adult_dat}")
        print("Run 05_nhanes_iii_processor.py first to download.")
        return
    
    # Read adult file
    df = read_nhanes_iii_adult(adult_dat)
    
    if len(df) == 0:
        print("[ERROR] No data loaded")
        return
    
    # Harmonize variables
    df = harmonize_nhanes_iii(df)
    
    # Save processed NHANES III
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    output_path = DATA_PROCESSED / "nhanes3_harmonized.parquet"
    df.to_parquet(output_path)
    print(f"\n[Saved] {output_path}")
    print(f"Total: {len(df):,} participants")
    print(f"CHD cases: {int(df['chd_composite'].sum()):,}")
    
    # Also append to main dataset
    print("\n[Merging with Continuous NHANES...]")
    main_data = DATA_PROCESSED / "nhanes_chd_harmonized.parquet"
    
    if main_data.exists():
        combined_df = pd.read_parquet(main_data)
        
        # Ensure consistent columns
        common_cols = ['SEQN', 'RIDAGEYR', 'RIAGENDR', 'RIDRETH1', 'INDFMPIR',
                       'WTMEC2YR', 'SDMVSTRA', 'SDMVPSU', 'chd_composite', 
                       'era', 'cycle']
        
        df_subset = df[[c for c in common_cols if c in df.columns]]
        combined_subset = combined_df[[c for c in common_cols if c in combined_df.columns]]
        
        # Combine
        full_data = pd.concat([df_subset, combined_subset], ignore_index=True)
        
        # Save full dataset
        full_output = DATA_PROCESSED / "nhanes_chd_full_35year.parquet"
        full_data.to_parquet(full_output)
        print(f"\n[Saved Full Dataset] {full_output}")
        print(f"Total participants: {len(full_data):,}")
        print(f"Eras: {full_data['era'].value_counts().to_dict()}")
    
    print("\n" + "="*60)
    print("NHANES III PROCESSING COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
