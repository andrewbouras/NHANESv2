"""
NHANES CHD Study - Data Download Script
Downloads all required NHANES data files (1988-2023) for CHD prevalence analysis
"""

import os
import pandas as pd
from pathlib import Path
import urllib.request
import ssl

# Disable SSL verification for CDC downloads (some environments have issues)
ssl._create_default_https_context = ssl._create_unverified_context

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"

# NHANES data file URLs organized by cycle and component
NHANES_FILES = {
    # === Era 4b: 2021-2023 (Post-Pandemic) ===
    "2021-2023": {
        "DEMO": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DEMO_L.xpt",
        "MCQ": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/MCQ_L.xpt",
        "BPQ": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BPQ_L.xpt",
        "DIQ": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DIQ_L.xpt",
        "SMQ": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/SMQ_L.xpt",
        "PAQ": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/PAQ_L.xpt",
        "BMX": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BMX_L.xpt",
        "BPX": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BPXO_L.xpt",
        "GHB": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/GHB_L.xpt",
        "GLU": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/GLU_L.xpt",
        "TCHOL": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/TCHOL_L.xpt",
        "HDL": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/HDL_L.xpt",
        "TRIGLY": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/TRIGLY_L.xpt",
    },
    
    # === Era 4a: 2017-2020 Pre-Pandemic ===
    "2017-2020": {
        "DEMO": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DEMO.xpt",
        "MCQ": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_MCQ.xpt",
        "BPQ": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_BPQ.xpt",
        "DIQ": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DIQ.xpt",
        "SMQ": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_SMQ.xpt",
        "PAQ": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_PAQ.xpt",
        "BMX": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_BMX.xpt",
        "BPX": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_BPXO.xpt",
        "GHB": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_GHB.xpt",
        "GLU": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_GLU.xpt",
        "TCHOL": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_TCHOL.xpt",
        "HDL": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_HDL.xpt",
        "TRIGLY": "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_TRIGLY.xpt",
    },
    
    # === Era 4a: 2015-2016 ===
    "2015-2016": {
        "DEMO": "https://wwwn.cdc.gov/Nchs/Nhanes/2015-2016/DEMO_I.xpt",
        "MCQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2015-2016/MCQ_I.xpt",
        "BPQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2015-2016/BPQ_I.xpt",
        "DIQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2015-2016/DIQ_I.xpt",
        "SMQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2015-2016/SMQ_I.xpt",
        "PAQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2015-2016/PAQ_I.xpt",
        "BMX": "https://wwwn.cdc.gov/Nchs/Nhanes/2015-2016/BMX_I.xpt",
        "BPX": "https://wwwn.cdc.gov/Nchs/Nhanes/2015-2016/BPX_I.xpt",
        "GHB": "https://wwwn.cdc.gov/Nchs/Nhanes/2015-2016/GHB_I.xpt",
        "GLU": "https://wwwn.cdc.gov/Nchs/Nhanes/2015-2016/GLU_I.xpt",
        "TCHOL": "https://wwwn.cdc.gov/Nchs/Nhanes/2015-2016/TCHOL_I.xpt",
        "HDL": "https://wwwn.cdc.gov/Nchs/Nhanes/2015-2016/HDL_I.xpt",
        "TRIGLY": "https://wwwn.cdc.gov/Nchs/Nhanes/2015-2016/TRIGLY_I.xpt",
    },
    
    # === Era 3: 2013-2014 ===
    "2013-2014": {
        "DEMO": "https://wwwn.cdc.gov/Nchs/Nhanes/2013-2014/DEMO_H.xpt",
        "MCQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2013-2014/MCQ_H.xpt",
        "BPQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2013-2014/BPQ_H.xpt",
        "DIQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2013-2014/DIQ_H.xpt",
        "SMQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2013-2014/SMQ_H.xpt",
        "PAQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2013-2014/PAQ_H.xpt",
        "BMX": "https://wwwn.cdc.gov/Nchs/Nhanes/2013-2014/BMX_H.xpt",
        "BPX": "https://wwwn.cdc.gov/Nchs/Nhanes/2013-2014/BPX_H.xpt",
        "GHB": "https://wwwn.cdc.gov/Nchs/Nhanes/2013-2014/GHB_H.xpt",
        "GLU": "https://wwwn.cdc.gov/Nchs/Nhanes/2013-2014/GLU_H.xpt",
        "TCHOL": "https://wwwn.cdc.gov/Nchs/Nhanes/2013-2014/TCHOL_H.xpt",
        "HDL": "https://wwwn.cdc.gov/Nchs/Nhanes/2013-2014/HDL_H.xpt",
        "TRIGLY": "https://wwwn.cdc.gov/Nchs/Nhanes/2013-2014/TRIGLY_H.xpt",
    },
    
    # === Era 3: 2011-2012 ===
    "2011-2012": {
        "DEMO": "https://wwwn.cdc.gov/Nchs/Nhanes/2011-2012/DEMO_G.xpt",
        "MCQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2011-2012/MCQ_G.xpt",
        "BPQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2011-2012/BPQ_G.xpt",
        "DIQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2011-2012/DIQ_G.xpt",
        "SMQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2011-2012/SMQ_G.xpt",
        "PAQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2011-2012/PAQ_G.xpt",
        "BMX": "https://wwwn.cdc.gov/Nchs/Nhanes/2011-2012/BMX_G.xpt",
        "BPX": "https://wwwn.cdc.gov/Nchs/Nhanes/2011-2012/BPX_G.xpt",
        "GHB": "https://wwwn.cdc.gov/Nchs/Nhanes/2011-2012/GHB_G.xpt",
        "GLU": "https://wwwn.cdc.gov/Nchs/Nhanes/2011-2012/GLU_G.xpt",
        "TCHOL": "https://wwwn.cdc.gov/Nchs/Nhanes/2011-2012/TCHOL_G.xpt",
        "HDL": "https://wwwn.cdc.gov/Nchs/Nhanes/2011-2012/HDL_G.xpt",
        "TRIGLY": "https://wwwn.cdc.gov/Nchs/Nhanes/2011-2012/TRIGLY_G.xpt",
    },
    
    # === Era 3: 2009-2010 ===
    "2009-2010": {
        "DEMO": "https://wwwn.cdc.gov/Nchs/Nhanes/2009-2010/DEMO_F.xpt",
        "MCQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2009-2010/MCQ_F.xpt",
        "BPQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2009-2010/BPQ_F.xpt",
        "DIQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2009-2010/DIQ_F.xpt",
        "SMQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2009-2010/SMQ_F.xpt",
        "PAQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2009-2010/PAQ_F.xpt",
        "BMX": "https://wwwn.cdc.gov/Nchs/Nhanes/2009-2010/BMX_F.xpt",
        "BPX": "https://wwwn.cdc.gov/Nchs/Nhanes/2009-2010/BPX_F.xpt",
        "GHB": "https://wwwn.cdc.gov/Nchs/Nhanes/2009-2010/GHB_F.xpt",
        "GLU": "https://wwwn.cdc.gov/Nchs/Nhanes/2009-2010/GLU_F.xpt",
        "TCHOL": "https://wwwn.cdc.gov/Nchs/Nhanes/2009-2010/TCHOL_F.xpt",
        "HDL": "https://wwwn.cdc.gov/Nchs/Nhanes/2009-2010/HDL_F.xpt",
        "TRIGLY": "https://wwwn.cdc.gov/Nchs/Nhanes/2009-2010/TRIGLY_F.xpt",
    },
    
    # === Era 3: 2007-2008 ===
    "2007-2008": {
        "DEMO": "https://wwwn.cdc.gov/Nchs/Nhanes/2007-2008/DEMO_E.xpt",
        "MCQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2007-2008/MCQ_E.xpt",
        "BPQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2007-2008/BPQ_E.xpt",
        "DIQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2007-2008/DIQ_E.xpt",
        "SMQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2007-2008/SMQ_E.xpt",
        "PAQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2007-2008/PAQ_E.xpt",
        "BMX": "https://wwwn.cdc.gov/Nchs/Nhanes/2007-2008/BMX_E.xpt",
        "BPX": "https://wwwn.cdc.gov/Nchs/Nhanes/2007-2008/BPX_E.xpt",
        "GHB": "https://wwwn.cdc.gov/Nchs/Nhanes/2007-2008/GHB_E.xpt",
        "GLU": "https://wwwn.cdc.gov/Nchs/Nhanes/2007-2008/GLU_E.xpt",
        "TCHOL": "https://wwwn.cdc.gov/Nchs/Nhanes/2007-2008/TCHOL_E.xpt",
        "HDL": "https://wwwn.cdc.gov/Nchs/Nhanes/2007-2008/HDL_E.xpt",
        "TRIGLY": "https://wwwn.cdc.gov/Nchs/Nhanes/2007-2008/TRIGLY_E.xpt",
    },
    
    # === Era 2: 2005-2006 ===
    "2005-2006": {
        "DEMO": "https://wwwn.cdc.gov/Nchs/Nhanes/2005-2006/DEMO_D.xpt",
        "MCQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2005-2006/MCQ_D.xpt",
        "BPQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2005-2006/BPQ_D.xpt",
        "DIQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2005-2006/DIQ_D.xpt",
        "SMQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2005-2006/SMQ_D.xpt",
        "PAQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2005-2006/PAQ_D.xpt",
        "BMX": "https://wwwn.cdc.gov/Nchs/Nhanes/2005-2006/BMX_D.xpt",
        "BPX": "https://wwwn.cdc.gov/Nchs/Nhanes/2005-2006/BPX_D.xpt",
        "GHB": "https://wwwn.cdc.gov/Nchs/Nhanes/2005-2006/GHB_D.xpt",
        "GLU": "https://wwwn.cdc.gov/Nchs/Nhanes/2005-2006/GLU_D.xpt",
        "TCHOL": "https://wwwn.cdc.gov/Nchs/Nhanes/2005-2006/TCHOL_D.xpt",
        "HDL": "https://wwwn.cdc.gov/Nchs/Nhanes/2005-2006/HDL_D.xpt",
        "TRIGLY": "https://wwwn.cdc.gov/Nchs/Nhanes/2005-2006/TRIGLY_D.xpt",
    },
    
    # === Era 2: 2003-2004 ===
    "2003-2004": {
        "DEMO": "https://wwwn.cdc.gov/Nchs/Nhanes/2003-2004/DEMO_C.xpt",
        "MCQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2003-2004/MCQ_C.xpt",
        "BPQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2003-2004/BPQ_C.xpt",
        "DIQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2003-2004/DIQ_C.xpt",
        "SMQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2003-2004/SMQ_C.xpt",
        "PAQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2003-2004/PAQ_C.xpt",
        "BMX": "https://wwwn.cdc.gov/Nchs/Nhanes/2003-2004/BMX_C.xpt",
        "BPX": "https://wwwn.cdc.gov/Nchs/Nhanes/2003-2004/BPX_C.xpt",
        "GHB": "https://wwwn.cdc.gov/Nchs/Nhanes/2003-2004/L10_C.xpt",
        "GLU": "https://wwwn.cdc.gov/Nchs/Nhanes/2003-2004/L10AM_C.xpt",
        "TCHOL": "https://wwwn.cdc.gov/Nchs/Nhanes/2003-2004/L13_C.xpt",
        "HDL": "https://wwwn.cdc.gov/Nchs/Nhanes/2003-2004/L13_C.xpt",  # Same file as TCHOL
        "TRIGLY": "https://wwwn.cdc.gov/Nchs/Nhanes/2003-2004/L13AM_C.xpt",
    },
    
    # === Era 2: 2001-2002 ===
    "2001-2002": {
        "DEMO": "https://wwwn.cdc.gov/Nchs/Nhanes/2001-2002/DEMO_B.xpt",
        "MCQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2001-2002/MCQ_B.xpt",
        "BPQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2001-2002/BPQ_B.xpt",
        "DIQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2001-2002/DIQ_B.xpt",
        "SMQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2001-2002/SMQ_B.xpt",
        "PAQ": "https://wwwn.cdc.gov/Nchs/Nhanes/2001-2002/PAQ_B.xpt",
        "BMX": "https://wwwn.cdc.gov/Nchs/Nhanes/2001-2002/BMX_B.xpt",
        "BPX": "https://wwwn.cdc.gov/Nchs/Nhanes/2001-2002/BPX_B.xpt",
        "GHB": "https://wwwn.cdc.gov/Nchs/Nhanes/2001-2002/L10_B.xpt",
        "GLU": "https://wwwn.cdc.gov/Nchs/Nhanes/2001-2002/L10AM_B.xpt",
        "TCHOL": "https://wwwn.cdc.gov/Nchs/Nhanes/2001-2002/L13_B.xpt",
        "HDL": "https://wwwn.cdc.gov/Nchs/Nhanes/2001-2002/L13_B.xpt",
        "TRIGLY": "https://wwwn.cdc.gov/Nchs/Nhanes/2001-2002/L13AM_B.xpt",
    },
    
    # === Era 2: 1999-2000 ===
    "1999-2000": {
        "DEMO": "https://wwwn.cdc.gov/Nchs/Nhanes/1999-2000/DEMO.xpt",
        "MCQ": "https://wwwn.cdc.gov/Nchs/Nhanes/1999-2000/MCQ.xpt",
        "BPQ": "https://wwwn.cdc.gov/Nchs/Nhanes/1999-2000/BPQ.xpt",
        "DIQ": "https://wwwn.cdc.gov/Nchs/Nhanes/1999-2000/DIQ.xpt",
        "SMQ": "https://wwwn.cdc.gov/Nchs/Nhanes/1999-2000/SMQ.xpt",
        "PAQ": "https://wwwn.cdc.gov/Nchs/Nhanes/1999-2000/PAQ.xpt",
        "BMX": "https://wwwn.cdc.gov/Nchs/Nhanes/1999-2000/BMX.xpt",
        "BPX": "https://wwwn.cdc.gov/Nchs/Nhanes/1999-2000/BPX.xpt",
        "GHB": "https://wwwn.cdc.gov/Nchs/Nhanes/1999-2000/LAB10.xpt",
        "GLU": "https://wwwn.cdc.gov/Nchs/Nhanes/1999-2000/LAB10AM.xpt",
        "TCHOL": "https://wwwn.cdc.gov/Nchs/Nhanes/1999-2000/LAB13.xpt",
        "HDL": "https://wwwn.cdc.gov/Nchs/Nhanes/1999-2000/LAB13.xpt",
        "TRIGLY": "https://wwwn.cdc.gov/Nchs/Nhanes/1999-2000/LAB13AM.xpt",
    },
}

# NHANES III files (different structure)
NHANES_III_FILES = {
    "adult": "https://wwwn.cdc.gov/nchs/data/nhanes3/1a/adult.xpt",
    "exam": "https://wwwn.cdc.gov/nchs/data/nhanes3/1a/exam.xpt",
    "lab": "https://wwwn.cdc.gov/nchs/data/nhanes3/1a/lab.xpt",
}

# Mortality linkage files
MORTALITY_FILES = {
    "mortality_2019": "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/datalinkage/linked_mortality/NHANES_2017_2018_MORT_2019_PUBLIC.dat",
}


def download_file(url: str, dest_path: Path) -> bool:
    """Download a file from URL to destination path."""
    try:
        if dest_path.exists():
            print(f"  [EXISTS] {dest_path.name}")
            return True
        
        print(f"  [DOWNLOADING] {url.split('/')[-1]}...")
        urllib.request.urlretrieve(url, dest_path)
        print(f"  [SUCCESS] {dest_path.name}")
        return True
    except Exception as e:
        print(f"  [ERROR] {url}: {e}")
        return False


def download_continuous_nhanes():
    """Download all Continuous NHANES files (1999-2023)."""
    print("\n" + "="*60)
    print("DOWNLOADING CONTINUOUS NHANES DATA (1999-2023)")
    print("="*60)
    
    for cycle, files in NHANES_FILES.items():
        cycle_dir = DATA_RAW / cycle
        cycle_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n[{cycle}]")
        for component, url in files.items():
            filename = url.split("/")[-1]
            dest_path = cycle_dir / filename
            download_file(url, dest_path)


def download_nhanes_iii():
    """Download NHANES III files (1988-1994)."""
    print("\n" + "="*60)
    print("DOWNLOADING NHANES III DATA (1988-1994)")
    print("="*60)
    
    nh3_dir = DATA_RAW / "NHANES_III"
    nh3_dir.mkdir(parents=True, exist_ok=True)
    
    for name, url in NHANES_III_FILES.items():
        filename = url.split("/")[-1]
        dest_path = nh3_dir / filename
        download_file(url, dest_path)


def main():
    """Main download function."""
    print("\n" + "="*60)
    print("NHANES CHD STUDY - DATA DOWNLOAD")
    print("="*60)
    print(f"Data will be saved to: {DATA_RAW}")
    
    # Create directories
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    
    # Download all data
    download_continuous_nhanes()
    download_nhanes_iii()
    
    print("\n" + "="*60)
    print("DOWNLOAD COMPLETE")
    print("="*60)
    print(f"\nData saved to: {DATA_RAW}")
    print("\nNext step: Run 02_harmonize_variables.py")


if __name__ == "__main__":
    main()
