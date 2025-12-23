"""
NHANES III (1988-1994) Data Download and Processor
Downloads and converts ASCII DAT files to parquet format
"""

import os
import requests
import pandas as pd
from pathlib import Path

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw" / "NHANES_III"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
}

# NHANES III files - ASCII DAT format with SAS code for reading
NHANES_III_FILES = {
    "adult": {
        "dat": "https://wwwn.cdc.gov/nchs/data/nhanes3/1a/adult.dat",
        "sas": "https://wwwn.cdc.gov/nchs/data/nhanes3/1a/adult.sas",
    },
    "exam": {
        "dat": "https://wwwn.cdc.gov/nchs/data/nhanes3/1a/exam.dat", 
        "sas": "https://wwwn.cdc.gov/nchs/data/nhanes3/1a/exam.sas",
    },
    "lab": {
        "dat": "https://wwwn.cdc.gov/nchs/data/nhanes3/1a/lab.dat",
        "sas": "https://wwwn.cdc.gov/nchs/data/nhanes3/1a/lab.sas",
    },
}

# Key variables we need from NHANES III adult file
# Based on CDC documentation
NHANES_III_VARS = {
    # Demographics - from adult file
    "SEQN": (1, 5),        # Sequence number
    "HSAGEIR": (18, 2),    # Age in years
    "HSSEX": (20, 1),      # Sex: 1=Male, 2=Female
    "DMARETHN": (21, 1),   # Race/ethnicity
    "DMAETHNR": (22, 1),   # Hispanic origin
    "HFA8R": (30, 1),      # Education level
    "DMPPIR": (31, 6),     # Poverty income ratio
    
    # Weights
    "WTPFEX6": (120, 12),  # MEC examined weight
    
    # CHD outcomes (Medical History)
    "HAD1": (200, 1),      # Ever told coronary heart disease
    "HAD2": (201, 1),      # Ever told angina
    "HAD3": (202, 1),      # Ever told heart attack
    
    # Smoking
    "HAR1": (250, 1),      # Smoked 100+ cigarettes
    "HAR3": (252, 1),      # Do you smoke now
}

# NOTE: The above column positions are PLACEHOLDERS
# Actual positions must be verified from SAS code files


def download_file(url: str, dest_path: Path) -> bool:
    """Download file with SSL handling."""
    try:
        if dest_path.exists() and dest_path.stat().st_size > 1000:
            print(f"  [EXISTS] {dest_path.name}")
            return True
            
        print(f"  [DOWNLOADING] {url.split('/')[-1]}...")
        response = requests.get(url, headers=HEADERS, verify=False, timeout=120)
        
        if response.status_code == 200 and len(response.content) > 1000:
            with open(dest_path, 'wb') as f:
                f.write(response.content)
            print(f"  [SUCCESS] {dest_path.name} ({len(response.content):,} bytes)")
            return True
        else:
            print(f"  [FAILED] Got {len(response.content)} bytes")
            return False
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False


def download_nhanes_iii():
    """Download all NHANES III files."""
    print("\n" + "="*60)
    print("DOWNLOADING NHANES III (1988-1994)")
    print("="*60)
    
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    
    for name, files in NHANES_III_FILES.items():
        print(f"\n[{name}]")
        for ext, url in files.items():
            dest_path = DATA_RAW / f"{name}.{ext}"
            download_file(url, dest_path)


def parse_sas_input(sas_file: Path) -> dict:
    """
    Parse SAS INPUT statement to extract variable positions.
    Returns dict of {varname: (start_col, length)}
    """
    variables = {}
    with open(sas_file, 'r') as f:
        content = f.read()
        
    # Look for INPUT statement
    # Format: @col varname $length. or @col varname length.
    import re
    pattern = r'@(\d+)\s+(\w+)\s+\$?(\d+)\.'
    matches = re.findall(pattern, content)
    
    for col, var, length in matches:
        variables[var.upper()] = (int(col), int(length))
    
    return variables


def read_fixed_width(dat_file: Path, var_positions: dict) -> pd.DataFrame:
    """Read fixed-width ASCII file using position specifications."""
    colspecs = [(pos-1, pos-1+length) for pos, length in var_positions.values()]
    names = list(var_positions.keys())
    
    try:
        df = pd.read_fwf(dat_file, colspecs=colspecs, names=names, encoding='latin1')
        return df
    except Exception as e:
        print(f"Error reading {dat_file}: {e}")
        return pd.DataFrame()


def main():
    """Main function to download and process NHANES III."""
    download_nhanes_iii()
    
    # Check if files downloaded
    adult_dat = DATA_RAW / "adult.dat"
    adult_sas = DATA_RAW / "adult.sas"
    
    if adult_dat.exists() and adult_sas.exists():
        print("\n" + "="*60)
        print("PARSING NHANES III ADULT FILE")
        print("="*60)
        
        # Parse SAS code for variable positions
        print("\n[Parsing SAS INPUT statement...]")
        var_positions = parse_sas_input(adult_sas)
        print(f"  Found {len(var_positions)} variables")
        
        if var_positions:
            # Read the data
            print("\n[Reading adult.dat...]")
            df = read_fixed_width(adult_dat, var_positions)
            print(f"  Loaded {len(df):,} participants")
            
            # Save as parquet
            output_path = DATA_RAW / "nhanes3_adult.parquet"
            df.to_parquet(output_path)
            print(f"\n[Saved] {output_path}")
    else:
        print("\nNHANES III files not fully downloaded.")
        print("You may need to download manually from:")
        print("  https://wwwn.cdc.gov/nchs/nhanes/nhanes3/datafiles.aspx")
    
    print("\n" + "="*60)
    print("NHANES III PROCESSING COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
