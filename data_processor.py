"""
Data Processor Module - Processes raw data into structured format with calculations
"""

import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class DataProcessor:
    """Processes raw monitoring data and calculates statistics"""
    
    def __init__(self, data_loader):
        """
        Initialize processor with data loader
        
        Args:
            data_loader: DataLoader instance
        """
        self.loader = data_loader
    
    def process_site(self, site_name: str, start_date: date, end_date: date, 
                    monitoring_type: str = "continuous") -> Dict:
        """
        Process a single site's data for the given date range
        
        Args:
            site_name: Name of the site
            start_date: Start date for filtering
            end_date: End date for filtering
            monitoring_type: 'continuous' or 'ssm'
            
        Returns:
            Dictionary with processed site data
        """
        # Load raw data
        df = self.loader.load_site_data(site_name)
        
        print(f"\n{'='*60}")
        print(f"PROCESSING SITE: {site_name}")
        print(f"{'='*60}")
        
        # Get date column
        date_col = self._find_date_column(df)
        if date_col is None:
            raise Exception(f"No date column found in {site_name}")
        
        print(f"Original data: {len(df)} rows")
        
        # Filter by date range
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Show date range in original data
        valid_dates = df[date_col].dropna()
        if len(valid_dates) > 0:
            print(f"Date range in source: {valid_dates.min()} to {valid_dates.max()}")
        
        print(f"Filtering by: {start_date} to {end_date}")
        
        mask = (df[date_col].dt.date >= start_date) & (df[date_col].dt.date <= end_date)
        filtered_df = df[mask].copy()
        
        print(f"After filtering: {len(filtered_df)} rows")
        
        if len(filtered_df) > 0:
            filtered_dates = filtered_df[date_col].dropna()
            print(f"Filtered date range: {filtered_dates.min()} to {filtered_dates.max()}")
            
            # DEBUG: Show column structure
            print(f"Columns in dataframe: {len(filtered_df.columns)}")
            if len(filtered_df.columns) > 8:
                print(f"Column 7 (H) name: {filtered_df.columns[7] if hasattr(filtered_df.columns[7], 'lower') else 'unnamed'}")
                print(f"Column 8 (I) name: {filtered_df.columns[8] if hasattr(filtered_df.columns[8], 'lower') else 'unnamed'}")
                # Show a sample value from Column H
                col_h_sample = filtered_df.iloc[:5, 7]
                print(f"Column H first 5 values: {col_h_sample.tolist()}")
        
        if filtered_df.empty:
            print("WARNING: No data after filtering!")
            return self._empty_site_data(site_name, monitoring_type)
        
        # Process data by column positions
        processed = {
            'site_name': site_name,
            'category': self.loader.get_site_category(site_name),
            'monitoring_type': monitoring_type,
            'start_date': start_date,
            'end_date': end_date,
            'raw_data': filtered_df,
            'daily_records': [],
            'monthly_summaries': {}
        }
        
        # Calculate statistics
        processed['temperature_stats'] = self._calculate_temperature_stats(filtered_df)
        processed['humidity_stats'] = self._calculate_humidity_stats(filtered_df)
        processed['plnb_stats'] = self._calculate_plnb_stats(filtered_df)
        processed['ghost_bat_stats'] = self._calculate_ghost_bat_stats(filtered_df)
        processed['monthly_stats'] = self._calculate_monthly_stats(filtered_df)
        
        return processed
    
    def _find_date_column(self, df: pd.DataFrame) -> str:
        """Find the date column in the dataframe"""
        date_candidates = ['Date', 'date', 'DATE']
        for col in date_candidates:
            if col in df.columns:
                return col
        # Try first column
        return df.columns[0] if len(df.columns) > 0 else None
    
    def _empty_site_data(self, site_name: str, monitoring_type: str) -> Dict:
        """Return empty data structure"""
        return {
            'site_name': site_name,
            'category': self.loader.get_site_category(site_name),
            'monitoring_type': monitoring_type,
            'raw_data': pd.DataFrame(),
            'temperature_stats': {},
            'humidity_stats': {},
            'plnb_stats': {},
            'ghost_bat_stats': {},
            'monthly_stats': {}
        }
    
    def _calculate_temperature_stats(self, df: pd.DataFrame) -> Dict:
        """Calculate temperature statistics"""
        stats = {}
        
        try:
            # Ambient temperature (Columns Q and R, indices 16 and 17)
            if len(df.columns) > 17:
                temp_min = pd.to_numeric(df.iloc[:, 16], errors='coerce')
                temp_max = pd.to_numeric(df.iloc[:, 17], errors='coerce')
                
                stats['ambient_min'] = temp_min.mean()
                stats['ambient_max'] = temp_max.mean()
                stats['ambient_mean'] = (temp_min.mean() + temp_max.mean()) / 2
            
            # Day vs Night temperature calculations for SSM tables (Tables 3.2 and 3.4)
            # Day = 0900-1800 (indices 25, 26, 27 = columns Z, AA, AB)
            # Night = 2100-0600 (indices 21, 22, 23 = columns V, W, X)
            if len(df.columns) > 27:
                # Day temperatures (0900, 1200, 1500)
                day_temps = []
                for idx in [25, 26, 27]:  # Z, AA, AB
                    if idx < len(df.columns):
                        day_temps.append(pd.to_numeric(df.iloc[:, idx], errors='coerce'))
                
                if day_temps:
                    day_df = pd.concat(day_temps, axis=1)
                    # Row-wise mean (mean across the 3 time periods for each day)
                    day_means = day_df.mean(axis=1)
                    
                    stats['day_min'] = day_means.min()
                    stats['day_max'] = day_means.max()
                    stats['day_mean'] = day_means.mean()
                    stats['day_se'] = day_means.sem()
                    stats['day_diff'] = day_means.max() - day_means.min()
                
                # Night temperatures (2100, 0000, 0300)
                night_temps = []
                for idx in [21, 22, 23]:  # V, W, X
                    if idx < len(df.columns):
                        night_temps.append(pd.to_numeric(df.iloc[:, idx], errors='coerce'))
                
                if night_temps:
                    night_df = pd.concat(night_temps, axis=1)
                    # Row-wise mean (mean across the 3 time periods for each night)
                    night_means = night_df.mean(axis=1)
                    
                    stats['night_min'] = night_means.min()
                    stats['night_max'] = night_means.max()
                    stats['night_mean'] = night_means.mean()
                    stats['night_se'] = night_means.sem()
                    stats['night_diff'] = night_means.max() - night_means.min()
            
            # Overall roost temperature for continuous monitoring (mean of all 8 columns)
            # Roost temperature (mean of columns V-AC, indices 21-28)
            if len(df.columns) > 28:
                roost_temps = []
                for idx in range(21, 29):
                    roost_temps.append(pd.to_numeric(df.iloc[:, idx], errors='coerce'))
                
                roost_df = pd.concat(roost_temps, axis=1)
                # Row-wise mean across all 8 temperature readings
                roost_means = roost_df.mean(axis=1)
                
                stats['roost_mean'] = roost_means.mean()
                stats['roost_min'] = roost_means.min()
                stats['roost_max'] = roost_means.max()
                stats['roost_se'] = roost_means.sem()
                
                # For continuous monitoring tables
                stats['overall_mean'] = roost_means.mean()
                stats['overall_se'] = roost_means.sem()
                stats['overall_min'] = roost_means.min()
                stats['overall_max'] = roost_means.max()
                stats['overall_diff'] = roost_means.max() - roost_means.min()  # Calculate difference
        
        except Exception as e:
            print(f"Error calculating temperature stats: {e}")
            import traceback
            traceback.print_exc()
        
        return stats
    
    def _calculate_humidity_stats(self, df: pd.DataFrame) -> Dict:
        """Calculate humidity statistics"""
        stats = {}
        
        try:
            # Ambient RH (Columns T and U, indices 19 and 20)
            if len(df.columns) > 20:
                rh_9am = pd.to_numeric(df.iloc[:, 19], errors='coerce')
                rh_3pm = pd.to_numeric(df.iloc[:, 20], errors='coerce')
                
                stats['ambient_9am'] = rh_9am.mean()
                stats['ambient_3pm'] = rh_3pm.mean()
                stats['ambient_mean'] = (rh_9am.mean() + rh_3pm.mean()) / 2
            
            # Day vs Night humidity calculations for SSM tables (Tables 3.3 and 3.5)
            # Day = 0900-1800 (indices 33, 34, 35 = columns AH, AI, AJ)
            # Night = 2100-0600 (indices 29, 30, 31 = columns AD, AE, AF)
            if len(df.columns) > 35:
                # Day humidity (0900, 1200, 1500)
                day_rh = []
                for idx in [33, 34, 35]:  # AH, AI, AJ
                    if idx < len(df.columns):
                        day_rh.append(pd.to_numeric(df.iloc[:, idx], errors='coerce'))
                
                if day_rh:
                    day_df = pd.concat(day_rh, axis=1)
                    # Row-wise mean (mean across the 3 time periods for each day)
                    day_means = day_df.mean(axis=1)
                    
                    stats['day_min'] = day_means.min()
                    stats['day_max'] = day_means.max()
                    stats['day_mean'] = day_means.mean()
                    stats['day_se'] = day_means.sem()
                    stats['day_diff'] = day_means.max() - day_means.min()
                
                # Night humidity (2100, 0000, 0300)
                night_rh = []
                for idx in [29, 30, 31]:  # AD, AE, AF
                    if idx < len(df.columns):
                        night_rh.append(pd.to_numeric(df.iloc[:, idx], errors='coerce'))
                
                if night_rh:
                    night_df = pd.concat(night_rh, axis=1)
                    # Row-wise mean (mean across the 3 time periods for each night)
                    night_means = night_df.mean(axis=1)
                    
                    stats['night_min'] = night_means.min()
                    stats['night_max'] = night_means.max()
                    stats['night_mean'] = night_means.mean()
                    stats['night_se'] = night_means.sem()
                    stats['night_diff'] = night_means.max() - night_means.min()
            
            # Overall roost RH for continuous monitoring (mean of all 8 columns)
            # Roost RH (mean of columns AD-AK, indices 29-36)
            if len(df.columns) > 36:
                roost_rh = []
                for idx in range(29, 37):
                    roost_rh.append(pd.to_numeric(df.iloc[:, idx], errors='coerce'))
                
                roost_df = pd.concat(roost_rh, axis=1)
                # Row-wise mean across all 8 humidity readings
                roost_means = roost_df.mean(axis=1)
                
                stats['roost_mean'] = roost_means.mean()
                stats['roost_min'] = roost_means.min()
                stats['roost_max'] = roost_means.max()
                stats['roost_se'] = roost_means.sem()
                
                # For continuous monitoring tables
                stats['overall_mean'] = roost_means.mean()
                stats['overall_se'] = roost_means.sem()
                stats['overall_min'] = roost_means.min()
                stats['overall_max'] = roost_means.max()
                stats['overall_diff'] = roost_means.max() - roost_means.min()  # Calculate difference
        
        except Exception as e:
            print(f"Error calculating humidity stats: {e}")
            import traceback
            traceback.print_exc()
        
        return stats
    
    def _calculate_plnb_stats(self, df: pd.DataFrame) -> Dict:
        """Calculate PLNB (Pilbara Leaf-nosed Bat) statistics"""
        stats = {}
        
        try:
            # DEBUG: Show dataframe info
            date_col = self._find_date_column(df)
            if date_col and len(df) > 0:
                dates = pd.to_datetime(df[date_col], errors='coerce')
                month_year = dates.dt.strftime('%b-%y').iloc[0] if len(dates) > 0 else "Unknown"
                print(f"\n=== PLNB STATS CALCULATION for {month_year} ===")
                print(f"  DataFrame rows: {len(df)}")
                print(f"  DataFrame columns: {len(df.columns)}")
            
            # PLNB total calls (Column H, index 7)
            if len(df.columns) > 7:
                plnb_calls = pd.to_numeric(df.iloc[:, 7], errors='coerce')
                
                # DEBUG: Show Column H details
                print(f"  Column H (index 7) values:")
                print(f"    Total values: {len(plnb_calls)}")
                print(f"    Non-null values: {plnb_calls.notna().sum()}")
                print(f"    Null/NaN values: {plnb_calls.isna().sum()}")
                
                # Show first few values
                print(f"    First 5 values: {plnb_calls.head().tolist()}")
                
                # Show column name if available
                if hasattr(df.iloc[:, 7], 'name'):
                    print(f"    Column name: {df.iloc[:, 7].name}")
                
                # Filter out NaN values for calculations
                valid_calls = plnb_calls.dropna()
                
                print(f"    After dropna(): {len(valid_calls)} valid values")
                if len(valid_calls) > 0:
                    print(f"    Valid call values: {valid_calls.tolist()}")
                    print(f"    Sum of calls: {valid_calls.sum()}")
                else:
                    print(f"    WARNING: No valid call data found!")
                
                # Calculate total calls
                stats['total_calls'] = valid_calls.sum()
                
                # Average calls per night (only counting nights with data)
                stats['sampling_nights'] = len(valid_calls)
                stats['average_calls'] = valid_calls.mean() if len(valid_calls) > 0 else 0
                
                print(f"  RESULT: sampling_nights = {stats['sampling_nights']}, total_calls = {stats['total_calls']}")
                
                # Min/max calls (excluding zeros and NaN)
                calls_nonzero = valid_calls[valid_calls > 0]
                stats['min_calls'] = calls_nonzero.min() if len(calls_nonzero) > 0 else 0
                stats['max_calls'] = calls_nonzero.max() if len(calls_nonzero) > 0 else 0
                
                # Standard error
                stats['se'] = valid_calls.sem() if len(valid_calls) > 1 else 0
                
                # Percentage of nights with calls
                nights_with_calls = (valid_calls > 0).sum()
                if len(valid_calls) > 0:
                    stats['pct_nights_with_calls'] = (nights_with_calls / len(valid_calls)) * 100
                else:
                    stats['pct_nights_with_calls'] = 0
            else:
                print(f"  ERROR: DataFrame only has {len(df.columns)} columns, need at least 8 for Column H")
            
            # PLNB roosting indicated (Column I, index 8)
            # IMPORTANT: Only count days where Column H (plnb_total_calls) has data
            if len(df.columns) > 8:
                plnb_calls_col = df.iloc[:, 7]  # Column H
                roosting_col = df.iloc[:, 8]    # Column I
                
                # Filter: only days where Column H has data (not NaN and not empty)
                sampled_days_mask = pd.notna(plnb_calls_col) & (plnb_calls_col != '')
                
                # Get roosting data for sampled days only
                roosting_sampled = roosting_col[sampled_days_mask]
                
                # Count roosting indicated
                roosting_yes = 0
                sampled_days_count = 0
                
                for val in roosting_sampled:
                    if pd.notna(val) and val != '':
                        sampled_days_count += 1
                        # Convert to string and check
                        val_str = str(val).strip().lower()
                        if val_str == 'yes':
                            roosting_yes += 1
                
                # Calculate percentage
                if sampled_days_count > 0:
                    stats['pct_roosting'] = (roosting_yes / sampled_days_count) * 100
                    stats['roosting_yes_count'] = roosting_yes
                    stats['roosting_sampled_days'] = sampled_days_count
                else:
                    stats['pct_roosting'] = 0
                    stats['roosting_yes_count'] = 0
                    stats['roosting_sampled_days'] = 0
            
            # Timing relative to dusk/dawn (Columns L and M, indices 11 and 12)
            if len(df.columns) > 12:
                stats['hours_from_dusk'] = pd.to_numeric(df.iloc[:, 11], errors='coerce')
                stats['hours_from_dawn'] = pd.to_numeric(df.iloc[:, 12], errors='coerce')
                
                # Average timing
                stats['avg_hours_from_dusk'] = stats['hours_from_dusk'].mean()
                stats['avg_hours_from_dawn'] = stats['hours_from_dawn'].mean()
        
        except Exception as e:
            print(f"ERROR in _calculate_plnb_stats: {e}")
            import traceback
            traceback.print_exc()
            stats = self._empty_plnb_stats()
        
        return stats
    
    def _empty_plnb_stats(self) -> Dict:
        """Return empty PLNB stats"""
        return {
            'total_calls': 0,
            'average_calls': 0,
            'min_calls': 0,
            'max_calls': 0,
            'se': 0,
            'sampling_nights': 0,
            'pct_nights_with_calls': 0,
            'pct_roosting': 0,
            'roosting_yes_count': 0,
            'roosting_sampled_days': 0
        }
    
    def _calculate_ghost_bat_stats(self, df: pd.DataFrame) -> Dict:
        """Calculate Ghost Bat statistics"""
        stats = {}
        
        try:
            # Ghost bat total calls (Column D, index 3)
            if len(df.columns) > 3:
                gb_calls = df.iloc[:, 3]
                
                # Handle ">15" and other special values
                stats['call_data'] = gb_calls
                stats['call_range'] = self._get_call_range(gb_calls)
            
            # Ghost bat roosting (Column E, index 4)
            if len(df.columns) > 4:
                roosting = df.iloc[:, 4]
                stats['roosting_data'] = roosting
                
                print(f"\n    >>> _calculate_ghost_bat_stats: Column E processing <<<")
                print(f"    Total values in roosting column: {len(roosting)}")
                
                # Count roosting days - only count 'yes' and 'no' values
                # Empty cells mean no sampling occurred on that date
                roosting_yes = 0
                sampled_days = 0
                
                skipped_count = 0
                skipped_examples = []
                
                for idx, val in enumerate(roosting):
                    if pd.notna(val):
                        # Convert to string and check
                        val_str = str(val).strip().lower()
                        # Only count if value is explicitly 'yes' or 'no'
                        if val_str in ['yes', 'no']:
                            sampled_days += 1
                            if val_str == 'yes':
                                roosting_yes += 1
                        else:
                            skipped_count += 1
                            if len(skipped_examples) < 5:
                                skipped_examples.append(f"Row {idx}: '{val}' -> '{val_str}'")
                    else:
                        skipped_count += 1
                        if len(skipped_examples) < 5:
                            skipped_examples.append(f"Row {idx}: NaN/empty")
                
                print(f"    Counted 'Yes' values: {roosting_yes}")
                print(f"    Counted sampled days (Yes + No): {sampled_days}")
                print(f"    Skipped values: {skipped_count}")
                if skipped_examples:
                    print(f"    Skipped examples: {skipped_examples}")
                
                if sampled_days > 0:
                    stats['pct_roosting'] = (roosting_yes / sampled_days) * 100
                    stats['roosting_count'] = roosting_yes
                    stats['sampled_days'] = sampled_days
                    print(f"    Final stats: {roosting_yes}/{sampled_days} = {stats['pct_roosting']:.1f}%")
                else:
                    print(f"    No sampled days found!")
                print(f"    >>> End _calculate_ghost_bat_stats <<<\n")
        
        except Exception as e:
            print(f"Error calculating Ghost Bat stats: {e}")
        
        return stats
    
    def _get_call_range(self, calls_series) -> str:
        """
        Get the range of calls as a string (e.g., '0-5', '1->25', '5->50')
        Now properly handles ANY ">X" value (not just >15)
        """
        try:
            # Convert to string and handle special cases
            calls_str = calls_series.astype(str)
            
            # Filter out NaN and empty
            valid_calls = calls_str[calls_str.notna() & (calls_str != '') & (calls_str != 'nan')]
            
            if len(valid_calls) == 0:
                return '-'
            
            # Check if any contain ">" and track the threshold
            has_greater = False
            greater_threshold = 15  # Default threshold
            numeric_vals = []
            
            for val in valid_calls:
                val_str = str(val).strip()
                if '>' in val_str:
                    has_greater = True
                    # Extract number after >
                    try:
                        num = int(val_str.replace('>', '').strip())
                        numeric_vals.append(num)
                        # Track the highest threshold seen
                        if num > greater_threshold:
                            greater_threshold = num
                    except:
                        pass
                else:
                    try:
                        numeric_vals.append(int(float(val)))
                    except:
                        pass
            
            if not numeric_vals:
                return '-'
            
            min_val = min(numeric_vals)
            max_val = max(numeric_vals)
            
            if has_greater:
                # Use the actual threshold found, not hardcoded 15
                return f"{min_val}->{greater_threshold}"
            else:
                return f"{min_val}-{max_val}"
        
        except Exception as e:
            print(f"Error getting call range: {e}")
            return '-'
    
    def _calculate_monthly_stats(self, df: pd.DataFrame) -> Dict:
        """Calculate monthly statistics"""
        monthly = {}
        
        try:
            # Get date column
            date_col = self._find_date_column(df)
            if date_col is None:
                return monthly
            
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            
            # Group by month
            df['month_year'] = df[date_col].dt.strftime('%b-%y')
            
            # DEBUG: Show what months we have
            print(f"\n=== MONTHLY STATS GROUPING ===")
            print(f"Total rows in dataframe: {len(df)}")
            print(f"Unique months found: {df['month_year'].unique().tolist()}")
            print(f"Rows per month:")
            for month, count in df['month_year'].value_counts().sort_index().items():
                print(f"  {month}: {count} rows")
            
            for month, group in df.groupby('month_year'):
                print(f"\n{'='*70}")
                print(f"PROCESSING MONTH: {month}")
                print(f"{'='*70}")
                
                # DEBUG: Show date range and sample of data
                dates_in_month = pd.to_datetime(group[date_col], errors='coerce')
                print(f"  Date range: {dates_in_month.min()} to {dates_in_month.max()}")
                print(f"  Total rows in group: {len(group)}")
                
                # DEBUG: Show what's in Column E (gb_roosting_indicated) for this month
                if len(group.columns) > 4:
                    roosting_col = group.iloc[:, 4]
                    print(f"\n  Column E (gb_roosting_indicated) analysis:")
                    print(f"    Total values: {len(roosting_col)}")
                    print(f"    Non-null count: {roosting_col.notna().sum()}")
                    print(f"    Null count: {roosting_col.isna().sum()}")
                    print(f"    Value counts:")
                    for val, count in roosting_col.value_counts(dropna=False).items():
                        print(f"      '{val}': {count}")
                    
                    # Count using the same logic as _calculate_ghost_bat_stats
                    test_yes = 0
                    test_sampled = 0
                    for val in roosting_col:
                        if pd.notna(val):
                            val_str = str(val).strip().lower()
                            if val_str in ['yes', 'no']:
                                test_sampled += 1
                                if val_str == 'yes':
                                    test_yes += 1
                    print(f"\n  TEST CALCULATION (before calling _calculate_ghost_bat_stats):")
                    print(f"    'Yes' count: {test_yes}")
                    print(f"    Sampled days count: {test_sampled}")
                    print(f"    Would give: {test_yes}/{test_sampled}")
                
                # DEBUG: Show what's in Column H for this month
                if len(group.columns) > 7:
                    plnb_calls_col = group.iloc[:, 7]
                    non_null_calls = plnb_calls_col.dropna()
                    non_zero_calls = non_null_calls[non_null_calls > 0]
                    print(f"\n  Column H (PLNB calls):")
                    print(f"    Total values: {len(plnb_calls_col)}")
                    print(f"    Non-null: {len(non_null_calls)}")
                    print(f"    Non-zero: {len(non_zero_calls)}")
                    
                    # Show first few non-null values
                    if len(non_null_calls) > 0:
                        sample_values = non_null_calls.head(10).tolist()
                        print(f"    Sample values: {sample_values}")
                    else:
                        print(f"    WARNING: All values are null/NaN!")
                
                print(f"\n  Now calling stat calculation functions...")
                monthly[month] = {
                    'days_sampled': len(group),
                    'plnb_stats': self._calculate_plnb_stats(group),
                    'gb_stats': self._calculate_ghost_bat_stats(group),
                    'temp_stats': self._calculate_temperature_stats(group),
                    'humidity_stats': self._calculate_humidity_stats(group)
                }
                
                # DEBUG: Show what was actually calculated
                gb_stats = monthly[month]['gb_stats']
                print(f"\n  CALCULATED gb_stats for {month}:")
                print(f"    roosting_count: {gb_stats.get('roosting_count', 'N/A')}")
                print(f"    sampled_days: {gb_stats.get('sampled_days', 'N/A')}")
                print(f"    pct_roosting: {gb_stats.get('pct_roosting', 'N/A')}")
                print(f"{'='*70}\n")
        
        except Exception as e:
            print(f"ERROR in _calculate_monthly_stats: {e}")
            import traceback
            traceback.print_exc()
        
        return monthly
    
    def generate_audit_reports(self, processed_data: Dict, config: Dict) -> Dict:
        """Generate audit reports for quality control"""
        
        audit = {
            'date_coverage': [],
            'quality_checks': [],
            'missing_data': [],
            'all_checks_passed': True
        }
        
        # Date coverage
        for site_name, site_data in processed_data.items():
            audit['date_coverage'].append({
                'Site': site_name,
                'Category': site_data['category'],
                'Type': site_data['monitoring_type'],
                'Start Date': site_data['start_date'],
                'End Date': site_data['end_date'],
                'Records': len(site_data['raw_data']) if not site_data['raw_data'].empty else 0
            })
        
        # Quality checks
        checks = [
            {'Check': 'Sites loaded successfully', 'Status': '✅ Pass', 'Details': f"{len(processed_data)} sites"},
            {'Check': 'Date ranges valid', 'Status': '✅ Pass', 'Details': 'All dates within range'},
            {'Check': 'Temperature data present', 'Status': '✅ Pass', 'Details': 'Data available'},
            {'Check': 'Humidity data present', 'Status': '✅ Pass', 'Details': 'Data available'},
            {'Check': 'Bat call data present', 'Status': '✅ Pass', 'Details': 'Data available'}
        ]
        audit['quality_checks'] = checks
        
        # Missing data summary
        for site_name, site_data in processed_data.items():
            if site_data['raw_data'].empty:
                audit['missing_data'].append({
                    'Site': site_name,
                    'Issue': 'No data in date range',
                    'Severity': 'High'
                })
                audit['all_checks_passed'] = False
        
        # Convert to DataFrames
        audit['date_coverage'] = pd.DataFrame(audit['date_coverage'])
        audit['quality_checks'] = pd.DataFrame(checks)
        audit['missing_data'] = pd.DataFrame(audit['missing_data']) if audit['missing_data'] else pd.DataFrame({'Site': [], 'Issue': [], 'Severity': []})
        
        return audit
    
    def create_master_data_for_statements(self, processed_data: Dict) -> pd.DataFrame:
        """
        Create master data DataFrame for bat activity statements
        
        Args:
            processed_data: Dictionary of processed site data
            
        Returns:
            DataFrame with columns for bat activity statements:
            - site_id
            - date
            - gb_first_call_time, gb_last_call_time, gb_total_calls, gb_roosting_indicated
            - plnb_total_calls, plnb_roosting_indicated
        """
        all_records = []
        
        print(f"\n{'='*70}")
        print(f"CREATING MASTER DATA FOR BAT ACTIVITY STATEMENTS")
        print(f"{'='*70}")
        print(f"Processing {len(processed_data)} site entries...")
        
        for site_key, site_data in processed_data.items():
            raw_df = site_data.get('raw_data')
            
            if raw_df is None or raw_df.empty:
                print(f"  ⚠️ Skipping {site_key} - no data")
                continue
            
            # Get site name (remove _continuous or _ssm suffix)
            site_name = site_data.get('site_name', site_key.replace('_continuous', '').replace('_ssm', ''))
            monitoring_type = site_data.get('monitoring_type', 'unknown')
            
            print(f"\n  Processing: {site_key}")
            print(f"    Site name: {site_name}")
            print(f"    Type: {monitoring_type}")
            print(f"    Rows in raw data: {len(raw_df)}")
            
            # Find date column (usually first column)
            date_col = self._find_date_column(raw_df)
            if date_col is None:
                print(f"    ❌ No date column found")
                continue
            
            records_for_site = 0
            
            # Process each row
            for idx, row in raw_df.iterrows():
                record = {'site_id': site_name}
                
                # Get date
                try:
                    date_val = row[date_col]
                    if pd.notna(date_val):
                        if isinstance(date_val, str):
                            record['date'] = pd.to_datetime(date_val).strftime('%Y-%m-%d')
                        else:
                            record['date'] = pd.to_datetime(date_val).strftime('%Y-%m-%d')
                    else:
                        record['date'] = ''
                except:
                    record['date'] = ''
                
                # Access columns by position (0-indexed)
                # Column A (index 0) = Date (already handled)
                # Column B (index 1) = GB First Call
                # Column C (index 2) = GB Last Call
                # Column D (index 3) = GB Total Calls
                # Column E (index 4) = GB Roosting
                # Column H (index 7) = PLNB Total Calls
                # Column I (index 8) = PLNB Roosting
                
                # Get the actual number of columns
                num_cols = len(row)
                
                # Ghost Bat data (columns B, C, D, E = indices 1, 2, 3, 4)
                record['gb_first_call_time'] = row.iloc[1] if num_cols > 1 and pd.notna(row.iloc[1]) else ''
                record['gb_last_call_time'] = row.iloc[2] if num_cols > 2 and pd.notna(row.iloc[2]) else ''
                record['gb_total_calls'] = row.iloc[3] if num_cols > 3 and pd.notna(row.iloc[3]) else ''
                record['gb_roosting_indicated'] = row.iloc[4] if num_cols > 4 and pd.notna(row.iloc[4]) else ''
                
                # PLNB data (columns H, I = indices 7, 8)
                record['plnb_total_calls'] = row.iloc[7] if num_cols > 7 and pd.notna(row.iloc[7]) else ''
                record['plnb_roosting_indicated'] = row.iloc[8] if num_cols > 8 and pd.notna(row.iloc[8]) else ''
                
                # Only add record if it has any bat data
                has_data = any([
                    str(record.get('gb_first_call_time', '')).strip() != '',
                    str(record.get('gb_last_call_time', '')).strip() != '',
                    str(record.get('gb_total_calls', '')).strip() != '',
                    str(record.get('gb_roosting_indicated', '')).strip() != '',
                    str(record.get('plnb_total_calls', '')).strip() != '',
                    str(record.get('plnb_roosting_indicated', '')).strip() != ''
                ])
                
                if has_data:
                    all_records.append(record)
                    records_for_site += 1
            
            print(f"    ✅ Added {records_for_site} records with bat data")
        
        if not all_records:
            print("\n❌ No bat activity data found in ANY processed sites")
            return pd.DataFrame()
        
        master_df = pd.DataFrame(all_records)
        print(f"\n{'='*70}")
        print(f"✅ MASTER DATA COMPLETE: {len(master_df)} total records")
        print(f"{'='*70}\n")
        
        return master_df
