"""
Data Loader Module - Handles Excel file reading and raw data extraction
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Union, List, Dict

class DataLoader:
    """Loads and provides access to raw monitoring data from Excel"""
    
    def __init__(self, file_path: Union[str, object]):
        """
        Initialize the data loader
        
        Args:
            file_path: Path to Excel file or uploaded file object
        """
        self.file_path = file_path
        self.excel_file = None
        self.load_excel()
    
    def load_excel(self):
        """Load the Excel file into memory"""
        try:
            self.excel_file = pd.ExcelFile(self.file_path)
        except Exception as e:
            raise Exception(f"Failed to load Excel file: {str(e)}")
    
    def get_sheet_names(self) -> List[str]:
        """Get list of all sheet names (cleaned for display)"""
        sheets = self.excel_file.sheet_names
        # Clean up sheet names - remove " raw data" suffix for cleaner display
        cleaned = []
        for sheet in sheets:
            if sheet.endswith(' raw data'):
                cleaned.append(sheet.replace(' raw data', '').strip())
            else:
                cleaned.append(sheet)
        return cleaned
    
    def load_site_data(self, site_name: str) -> pd.DataFrame:
        """
        Load raw data for a specific site
        
        Args:
            site_name: Name of the site/worksheet
            
        Returns:
            DataFrame with raw site data
        """
        available_sheets = self.excel_file.sheet_names
        
        # Strategy 1: Try exact match
        if site_name in available_sheets:
            df = pd.read_excel(self.excel_file, sheet_name=site_name)
            return self._clean_dataframe(df)
        
        # Strategy 2: Try with " raw data" suffix (common pattern)
        sheet_with_suffix = f"{site_name} raw data"
        if sheet_with_suffix in available_sheets:
            df = pd.read_excel(self.excel_file, sheet_name=sheet_with_suffix)
            return self._clean_dataframe(df)
        
        # Strategy 3: Try case-insensitive match
        for sheet in available_sheets:
            if sheet.upper() == site_name.upper():
                df = pd.read_excel(self.excel_file, sheet_name=sheet)
                return self._clean_dataframe(df)
        
        # Strategy 4: Try partial match (sheet starts with site_name)
        for sheet in available_sheets:
            if sheet.upper().startswith(site_name.upper()):
                df = pd.read_excel(self.excel_file, sheet_name=sheet)
                return self._clean_dataframe(df)
        
        # Strategy 5: Try if site_name is contained in sheet name
        for sheet in available_sheets:
            if site_name.upper() in sheet.upper():
                df = pd.read_excel(self.excel_file, sheet_name=sheet)
                return self._clean_dataframe(df)
        
        # If still no match, provide helpful error
        raise Exception(
            f"Worksheet for site '{site_name}' not found.\n"
            f"Available worksheets:\n" + 
            "\n".join([f"  - {s}" for s in available_sheets[:15]])
        )
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize the raw dataframe"""
        
        # Standardize column names (remove spaces, lowercase)
        df.columns = df.columns.str.strip()
        
        # Convert date column
        if 'Date' in df.columns or 'date' in df.columns:
            date_col = 'Date' if 'Date' in df.columns else 'date'
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Replace Excel errors with NaN
        df = df.replace(['#DIV/0!', '#VALUE!', '#REF!', '#NAME?'], np.nan)
        
        # DIAGNOSTIC: Check Column H for CMPC-08
        if len(df.columns) > 7:
            col_h = df.iloc[:, 7]
            # Check if we have date column to filter October
            if 'Date' in df.columns or 'date' in df.columns:
                date_col = 'Date' if 'Date' in df.columns else 'date'
                oct_2024_mask = (df[date_col] >= '2024-10-01') & (df[date_col] <= '2024-10-31')
                oct_data = df[oct_2024_mask]
                
                if len(oct_data) > 0:
                    print(f"\n🔍 DIAGNOSTIC: Column H in October 2024")
                    print(f"   Sheet has {len(df.columns)} columns")
                    print(f"   Column H (index 7) name: {df.columns[7]}")
                    print(f"   Column H dtype: {col_h.dtype}")
                    print(f"   October 2024 rows: {len(oct_data)}")
                    
                    oct_col_h = oct_data.iloc[:, 7]
                    print(f"   October Column H non-null: {oct_col_h.notna().sum()}")
                    print(f"   October Column H null: {oct_col_h.isna().sum()}")
                    print(f"   October Column H first 10 values:")
                    for i, val in enumerate(oct_col_h.head(10)):
                        date_val = oct_data.iloc[i][date_col]
                        print(f"     {date_val.date()}: {val} (type: {type(val).__name__})")
        
        return df
    
    def get_column_mapping(self) -> Dict[str, str]:
        """
        Returns the column mapping from the documentation
        
        Returns:
            Dictionary mapping field names to Excel columns
        """
        return {
            # Date
            'date': 'A',
            
            # Ghost Bat columns
            'gb_first_call': 'B',
            'gb_last_call': 'C',
            'gb_total_calls': 'D',
            'gb_roosting_indicated': 'E',
            
            # PLNB columns
            'plnb_first_call': 'F',
            'plnb_last_call': 'G',
            'plnb_total_calls': 'H',
            'plnb_roosting_indicated': 'I',
            
            # Civil twilight
            'civil_dusk': 'J',
            'civil_dawn': 'K',
            
            # PLNB relative timing
            'first_call_relative_to_dusk_ct': 'L',
            'last_call_relative_to_dawn_ct': 'M',
            
            # Moon data
            'moon_illumination': 'N',
            'moon_phase': 'O',
            'moon_depiction': 'P',
            
            # BoM data
            'temp_min': 'Q',
            'temp_max': 'R',
            'rainfall': 'S',
            'humidity_0900': 'T',
            'humidity_1500': 'U',
            
            # Temperature buckets (3-hour readings)
            'temp_2100': 'V',  # 2100-0000
            'temp_0000': 'W',  # 0000-0300
            'temp_0300': 'X',  # 0300-0600
            'temp_0600': 'Y',  # 0600-0900
            'temp_0900': 'Z',  # 0900-1200
            'temp_1200': 'AA', # 1200-1500
            'temp_1500': 'AB', # 1500-1800
            'temp_1800': 'AC', # 1800-2100
            
            # Humidity buckets (3-hour readings)
            'rh_2100': 'AD',  # 2100-0000
            'rh_0000': 'AE',  # 0000-0300
            'rh_0300': 'AF',  # 0300-0600
            'rh_0600': 'AG',  # 0600-0900
            'rh_0900': 'AH',  # 0900-1200
            'rh_1200': 'AI',  # 1200-1500
            'rh_1500': 'AJ',  # 1500-1800
            'rh_1800': 'AK',  # 1800-2100
        }
    
    def get_column_by_letter(self, df: pd.DataFrame, letter: str):
        """
        Get column data by Excel column letter
        
        Args:
            df: DataFrame to extract from
            letter: Excel column letter (e.g., 'A', 'B', 'AA')
            
        Returns:
            Series with column data
        """
        # Convert letter to column index
        col_index = self._letter_to_index(letter)
        
        if col_index < len(df.columns):
            return df.iloc[:, col_index]
        else:
            return pd.Series([np.nan] * len(df))
    
    def _letter_to_index(self, letter: str) -> int:
        """Convert Excel column letter to 0-based index"""
        index = 0
        for char in letter:
            index = index * 26 + (ord(char.upper()) - ord('A') + 1)
        return index - 1
    
    def get_site_category(self, site_name: str) -> str:
        """
        Determine if site is Impact or Control
        
        Args:
            site_name: Name of the site
            
        Returns:
            'Impact' or 'Control'
        """
        # Clean site name - remove any parenthetical info and "raw data" suffix
        clean_name = site_name.replace(' raw data', '').strip()
        if '(' in clean_name:
            clean_name = clean_name.split('(')[0].strip()
        
        # Based on the sample data, certain sites are controls
        control_sites = ['CMPC-18', 'CMPC-26', 'CMPC-28', 'WMPC-05', 'WMPC-21', 'WMPC-35']
        
        # Check if the cleaned name matches any control site
        for control_site in control_sites:
            if clean_name.upper().startswith(control_site.upper()):
                return 'Control'
        
        return 'Impact'
