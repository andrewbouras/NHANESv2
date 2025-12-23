"""
NHANES Data Download - Fixed version with SSL handling
Downloads XPT files from CDC for all NHANES continuous cycles
"""

import os
import sys
import requests
from pathlib import Path
from bs4 import BeautifulSoup

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"

# Headers to mimic browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

CYCLES = [
    ("1999-2000", "1999"),
    ("2001-2002", "2001"),
    ("2003-2004", "2003"),
    ("2005-2006", "2005"),
    ("2007-2008", "2007"),
    ("2009-2010", "2009"),
    ("2011-2012", "2011"),
    ("2013-2014", "2013"),
    ("2015-2016", "2015"),
]

COMPONENTS = ["Demographics", "Questionnaire", "Examination", "Laboratory"]

# Files we need (base names without suffix)
NEEDED_FILES = {
    "DEMO", "MCQ", "BPQ", "DIQ", "SMQ", "PAQ", "BMX", "BPX",
    "GHB", "GLU", "TCHOL", "HDL", "TRIGLY"
}


def download_file(url: str, dest_path: Path) -> bool:
    """Download a file with proper headers and SSL handling."""
    try:
        if dest_path.exists() and dest_path.stat().st_size > 50000:
            print(f"  [EXISTS] {dest_path.name}")
            return True
            
        print(f"  [DOWNLOADING] {url.split('/')[-1]}...")
        response = requests.get(url, headers=HEADERS, verify=False, timeout=60)
        
        # Check if we got actual data (not HTML error page)
        if response.status_code == 200 and len(response.content) > 50000:
            with open(dest_path, 'wb') as f:
                f.write(response.content)
            print(f"  [SUCCESS] {dest_path.name} ({len(response.content)} bytes)")
            return True
        else:
            print(f"  [FAILED] {dest_path.name} - got {len(response.content)} bytes")
            return False
            
    except Exception as e:
        print(f"  [ERROR] {url}: {e}")
        return False


def get_xpt_links_from_page(cycle_year: str, component: str) -> list:
    """Parse CDC data page to find XPT file links."""
    url = f"https://wwwn.cdc.gov/nchs/nhanes/Search/DataPage.aspx?Component={component}&CycleBeginYear={cycle_year}"
    
    try:
        response = requests.get(url, headers=HEADERS, verify=False, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '.xpt' in href.lower():
                # Check if this is a file we need
                filename = href.split('/')[-1].upper()
                base_name = filename.split('_')[0].split('.')[0]
                
                if base_name in NEEDED_FILES:
                    full_url = f"https://wwwn.cdc.gov{href}" if href.startswith('/') else href
                    links.append((filename, full_url))
        
        return links
    except Exception as e:
        print(f"  Error parsing page: {e}")
        return []


def download_cycle(cycle_name: str, cycle_year: str):
    """Download all needed files for a cycle."""
    print(f"\n{'='*60}")
    print(f"CYCLE: {cycle_name}")
    print('='*60)
    
    cycle_dir = DATA_RAW / cycle_name
    cycle_dir.mkdir(parents=True, exist_ok=True)
    
    all_links = []
    for component in COMPONENTS:
        print(f"\n[{component}]")
        links = get_xpt_links_from_page(cycle_year, component)
        print(f"  Found {len(links)} relevant XPT files")
        all_links.extend(links)
    
    # Remove duplicates
    seen = set()
    unique_links = []
    for name, url in all_links:
        if name not in seen:
            seen.add(name)
            unique_links.append((name, url))
    
    print(f"\n[Downloading {len(unique_links)} files]")
    for filename, url in unique_links:
        dest_path = cycle_dir / filename
        download_file(url, dest_path)


def main():
    print("\n" + "="*60)
    print("NHANES DATA DOWNLOAD - FIXED VERSION")
    print("="*60)
    
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    
    for cycle_name, cycle_year in CYCLES:
        download_cycle(cycle_name, cycle_year)
    
    print("\n" + "="*60)
    print("DOWNLOAD COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
