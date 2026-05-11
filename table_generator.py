"""
Table Generator Module - Creates all 14 required monitoring tables
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List

class TableGenerator:
    """Generates all monitoring tables from processed data"""
    
    def __init__(self, processed_data: Dict, config: Dict):
        """
        Initialize table generator
        
        Args:
            processed_data: Dictionary of processed site data
            config: Configuration dictionary with site selections
        """
        self.processed_data = processed_data
        self.config = config
        self.tables = {}
    
    def generate_all_tables(self) -> Dict:
        """Generate all tables and return dictionary"""
        
        # Determine which tables to generate based on config
        monitoring_type = self.config.get('monitoring_type', 'Both')
        
        # SSM Tables
        if monitoring_type in ['Short-term (SSM)', 'Both']:
            self.tables['2.1'] = self.generate_table_2_1()
            self.tables['3.2'] = self.generate_table_3_2()
            self.tables['3.3'] = self.generate_table_3_3()
            self.tables['3.6'] = self.generate_table_3_6()
            self.tables['3.7'] = self.generate_table_3_7()
            self.tables['3.8'] = self.generate_table_3_8()
            self.tables['3.9'] = self.generate_table_3_9()
            self.tables['3.10'] = self.generate_table_3_10()
        
        # Continuous Tables
        if monitoring_type in ['Continuous Monitoring', 'Both']:
            self.tables['3.4'] = self.generate_table_3_4()
            self.tables['3.5'] = self.generate_table_3_5()
            self.tables['3.11'] = self.generate_table_3_11()
            self.tables['3.12'] = self.generate_table_3_12()
            self.tables['3.13'] = self.generate_table_3_13()
            self.tables['3.14'] = self.generate_table_3_14()
        
        return self.tables
    
    def generate_table_2_1(self) -> Dict:
        """
        Table 2.1: Daily climate data (BoM) during SSM period
        """
        rows = []
        
        # Get SSM sites data
        ssm_sites = [site for site, data in self.processed_data.items() 
                    if data.get('monitoring_type') == 'ssm']
        
        if not ssm_sites:
            return self._empty_table("Table 2.1: Daily Climate Summary (SSM)")
        
        # Combine all SSM dates
        all_dates = []
        for site in ssm_sites:
            site_data = self.processed_data[site]
            df = site_data.get('raw_data', pd.DataFrame())
            if not df.empty:
                all_dates.append(df)
        
        if not all_dates:
            return self._empty_table("Table 2.1: Daily Climate Summary (SSM)")
        
        combined_df = pd.concat(all_dates, ignore_index=True)
        
        # Get unique dates and aggregate data properly
        date_col = combined_df.columns[0]
        combined_df[date_col] = pd.to_datetime(combined_df[date_col], errors='coerce')
        combined_df = combined_df.sort_values(date_col)
        
        # Group by date and take first non-null value for each column
        grouped_dates = combined_df.groupby(combined_df[date_col].dt.date)
        
        for date_val, group in grouped_dates:
            # For each date, combine all rows taking MOST APPROPRIATE value
            row_data = group.iloc[0].copy()
            
            # CRITICAL FIX: Use column names instead of positions for dusk/dawn
            # to avoid any potential misalignment issues
            print(f"\n{'='*60}")
            print(f"DEBUG: Processing date {date_val}")
            print(f"  group has {len(group)} rows")
            print(f"  row_data has {len(row_data)} columns")
            
            # Get dusk and dawn by column NAME, not position
            if 'dusk_ct' in row_data.index:
                dusk_value = row_data['dusk_ct']
                print(f"  dusk_ct (by name): {dusk_value}")
            else:
                dusk_value = None
                print(f"  ⚠️ dusk_ct column not found!")
            
            if 'dawn_ct' in row_data.index:
                dawn_value = row_data['dawn_ct']
                print(f"  dawn_ct (by name): {dawn_value}")
            else:
                dawn_value = None
                print(f"  ⚠️ dawn_ct column not found!")
            
            # Special handling for Civil Dusk and Civil Dawn
            # If values are missing, try to get from other rows for same date
            if pd.isna(dusk_value) or dusk_value is None:
                print(f"  Dusk is NaN, searching group for non-null value...")
                for _, other_row in group.iterrows():
                    if 'dusk_ct' in other_row.index and pd.notna(other_row['dusk_ct']):
                        dusk_value = other_row['dusk_ct']
                        row_data['dusk_ct'] = dusk_value
                        print(f"  Found dusk value: {dusk_value}")
                        break
            
            if pd.isna(dawn_value) or dawn_value is None:
                print(f"  Dawn is NaN, searching group for non-null value...")
                for _, other_row in group.iterrows():
                    if 'dawn_ct' in other_row.index and pd.notna(other_row['dawn_ct']):
                        dawn_value = other_row['dawn_ct']
                        row_data['dawn_ct'] = dawn_value
                        print(f"  Found dawn value: {dawn_value}")
                        break
            
            # Fill in any other missing values from other rows for the same date
            # But use column NAMES, not positions
            for col_name in row_data.index:
                # Skip dusk_ct and dawn_ct as we already handled them
                if col_name in ['dusk_ct', 'dawn_ct']:
                    continue
                    
                if pd.isna(row_data[col_name]):
                    # Look for non-null value in other rows for this date
                    for _, other_row in group.iterrows():
                        if col_name in other_row.index and pd.notna(other_row[col_name]):
                            row_data[col_name] = other_row[col_name]
                            break
            try:
                # Helper function to safely get values by column name
                def safe_get_by_name(col_name, default='', decimals=None):
                    if col_name not in row_data.index or pd.isna(row_data[col_name]):
                        return default
                    val = row_data[col_name]
                    if decimals is not None and isinstance(val, (int, float)):
                        return round(float(val), decimals)
                    return str(val) if not isinstance(val, (int, float)) else val
                
                # Helper function to format time values by column name
                def format_time_by_name(col_name):
                    print(f"\n  === format_time_by_name('{col_name}') ===")
                    
                    if col_name not in row_data.index:
                        print(f"  ❌ Column '{col_name}' not found in row_data")
                        return ''
                    
                    val = row_data[col_name]
                    
                    if pd.isna(val):
                        print(f"  ❌ Value is NaN")
                        return ''
                    
                    print(f"  ✓ Value retrieved: {val}")
                    print(f"  ✓ Type: {type(val)}")
                    print(f"  ✓ Repr: {repr(val)}")
                    
                    # If it's already a time string, parse and format it
                    if isinstance(val, str) and ':' in val:
                        try:
                            parts = val.split(':')
                            hour = int(parts[0])
                            minute = int(parts[1]) if len(parts) > 1 else 0
                            result = f"{hour}:{minute:02d}"
                            print(f"  → Formatted string time to: {result}")
                            return result
                        except Exception as e:
                            print(f"  ⚠️ Error parsing string time: {e}")
                            return val
                    
                    # If it's a datetime.time or datetime object, extract time
                    if hasattr(val, 'hour'):
                        result = f"{val.hour}:{val.minute:02d}"
                        print(f"  → Extracted time to: {result}")
                        return result
                    
                    # If it's an Excel decimal time
                    if isinstance(val, (int, float)):
                        total_minutes = int(val * 24 * 60)
                        hours = total_minutes // 60
                        minutes = total_minutes % 60
                        result = f"{hours}:{minutes:02d}"
                        print(f"  → Converted decimal {val} to: {result}")
                        return result
                    
                    print(f"  ⚠️ Unknown type, returning str()")
                    return str(val)
                
                # Debug: Check dusk and dawn values before creating row
                print(f"\n{'='*60}")
                print(f"CREATING ROW FOR DATE: {row_data.iloc[0]}")
                print(f"  dusk_ct: {row_data.get('dusk_ct', 'NOT FOUND')} (type: {type(row_data.get('dusk_ct', None))})")
                print(f"  dawn_ct: {row_data.get('dawn_ct', 'NOT FOUND')} (type: {type(row_data.get('dawn_ct', None))})")
                
                dusk_result = format_time_by_name('dusk_ct')
                dawn_result = format_time_by_name('dawn_ct')
                
                print(f"\n  Final values being added to row:")
                print(f"    Civil Dusk: '{dusk_result}'")
                print(f"    Civil Dawn: '{dawn_result}'")
                print(f"{'='*60}\n")
                
                rows.append({
                    'Date': row_data.iloc[0].strftime('%d-%b-%y') if pd.notna(row_data.iloc[0]) else '',
                    'Temp Min (°C)': safe_get_by_name('ambient_temp_min_c', '', 1),
                    'Temp Max (°C)': safe_get_by_name('ambient_temp_max_c', '', 1),
                    'Rainfall (mm)': safe_get_by_name('rainfall_mm', '', 1),
                    'Humidity 0900 (%)': safe_get_by_name('ambient_9am_rh', '', 1),
                    'Humidity 1500 (%)': safe_get_by_name('ambient_3pm_rh', '', 1),
                    'Civil Dusk': dusk_result,
                    'Civil Dawn': dawn_result,
                    'Moon Illumination (%)': safe_get_by_name('moon_fraction_illuminated_pct', '', 2)
                })
            except:
                continue
        
        # Add average row
        if rows:
            numeric_cols = ['Temp Min (°C)', 'Temp Max (°C)', 'Rainfall (mm)', 
                          'Humidity 0900 (%)', 'Humidity 1500 (%)', 'Moon Illumination (%)']
            avg_row = {'Date': 'Average'}
            for col in numeric_cols:
                values = [r[col] for r in rows if r[col] != '' and r[col] is not None and isinstance(r[col], (int, float))]
                avg_row[col] = round(np.mean(values), 1) if values else ''
            
            # Calculate average for time columns
            def time_to_decimal(time_str):
                """Convert time string to decimal hours"""
                try:
                    if ':' in str(time_str):
                        parts = str(time_str).split(':')
                        return int(parts[0]) + int(parts[1])/60
                    return None
                except:
                    return None
            
            def decimal_to_time(decimal_hours):
                """Convert decimal hours back to time string"""
                hours = int(decimal_hours)
                minutes = int((decimal_hours - hours) * 60)
                return f"{hours}:{minutes:02d}"
            
            # Average Civil Dusk
            dusk_values = [time_to_decimal(r['Civil Dusk']) for r in rows if r['Civil Dusk'] and r['Date'] != 'Average']
            dusk_values = [v for v in dusk_values if v is not None]
            avg_row['Civil Dusk'] = decimal_to_time(np.mean(dusk_values)) if dusk_values else ''
            
            # Average Civil Dawn
            dawn_values = [time_to_decimal(r['Civil Dawn']) for r in rows if r['Civil Dawn'] and r['Date'] != 'Average']
            dawn_values = [v for v in dawn_values if v is not None]
            avg_row['Civil Dawn'] = decimal_to_time(np.mean(dawn_values)) if dawn_values else ''
            
            rows.append(avg_row)
        
        df = pd.DataFrame(rows)
        
        # Ensure proper data types
        numeric_cols = ['Temp Min (°C)', 'Temp Max (°C)', 'Rainfall (mm)', 
                       'Humidity 0900 (%)', 'Humidity 1500 (%)', 'Moon Illumination (%)']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Ensure text columns are strings
        for col in ['Date', 'Civil Dusk', 'Civil Dawn']:
            if col in df.columns:
                df[col] = df[col].astype(str)
        
        return {
            'table_id': '2.1',
            'title': 'Table 2.1: Daily Climate Data (BoM) During SSM Period',
            'dataframe': df,
            'notes': ['New Moon = 0%; First and Last Quarter = 50%; Full Moon = 100%']
        }
    
    def generate_table_3_2(self) -> Dict:
        """
        Table 3.2: Temperature data at monitoring sites (SSM)
        """
        rows = []
        
        ssm_sites = [site for site, data in self.processed_data.items() 
                    if data.get('monitoring_type') == 'ssm']
        
        for site in ssm_sites:
            site_data = self.processed_data[site]
            temp_stats = site_data.get('temperature_stats', {})
            
            if temp_stats:
                rows.append({
                    'Caves': site,
                    'Category': site_data['category'],
                    'Day Min (°C)': round(temp_stats.get('day_min', 0), 2),
                    'Day Max (°C)': round(temp_stats.get('day_max', 0), 2),
                    'Day Avg (±SE)': f"{round(temp_stats.get('day_mean', 0), 2)} (±{round(temp_stats.get('day_se', 0), 2)})",
                    'Day Diff': round(temp_stats.get('day_diff', 0), 2),
                    'Night Min (°C)': round(temp_stats.get('night_min', 0), 2),
                    'Night Max (°C)': round(temp_stats.get('night_max', 0), 2),
                    'Night Avg (±SE)': f"{round(temp_stats.get('night_mean', 0), 2)} (±{round(temp_stats.get('night_se', 0), 2)})",
                    'Night Diff': round(temp_stats.get('night_diff', 0), 2)
                })
        
        df = pd.DataFrame(rows)
        
        return {
            'table_id': '3.2',
            'title': 'Table 3.2: Temperature Data at Monitoring Sites (SSM)',
            'dataframe': df,
            'notes': ['Daytime: 0900-1800; Night-time: 2100-0600']
        }
    
    def generate_table_3_3(self) -> Dict:
        """
        Table 3.3: Relative humidity data at monitoring sites (SSM)
        """
        rows = []
        
        ssm_sites = [site for site, data in self.processed_data.items() 
                    if data.get('monitoring_type') == 'ssm']
        
        for site in ssm_sites:
            site_data = self.processed_data[site]
            rh_stats = site_data.get('humidity_stats', {})
            
            if rh_stats:
                rows.append({
                    'Caves': site,
                    'Category': site_data['category'],
                    'Day Min (%)': round(rh_stats.get('day_min', 0), 2),
                    'Day Max (%)': round(rh_stats.get('day_max', 0), 2),
                    'Day Avg (±SE)': f"{round(rh_stats.get('day_mean', 0), 2)} (±{round(rh_stats.get('day_se', 0), 2)})",
                    'Day Diff': round(rh_stats.get('day_diff', 0), 2),
                    'Night Min (%)': round(rh_stats.get('night_min', 0), 2),
                    'Night Max (%)': round(rh_stats.get('night_max', 0), 2),
                    'Night Avg (±SE)': f"{round(rh_stats.get('night_mean', 0), 2)} (±{round(rh_stats.get('night_se', 0), 2)})",
                    'Night Diff': round(rh_stats.get('night_diff', 0), 2)
                })
        
        df = pd.DataFrame(rows)
        
        return {
            'table_id': '3.3',
            'title': 'Table 3.3: Relative Humidity Data at Monitoring Sites (SSM)',
            'dataframe': df,
            'notes': ['Daytime: 0900-1800; Night-time: 2100-0600']
        }
    
    def generate_table_3_4(self) -> Dict:
        """
        Table 3.4: Temperature summary (Continuous)
        """
        rows = []
        
        cont_sites = [site for site, data in self.processed_data.items() 
                     if data.get('monitoring_type') == 'continuous']
        
        for site in cont_sites:
            site_data = self.processed_data[site]
            temp_stats = site_data.get('temperature_stats', {})
            
            if temp_stats:
                rows.append({
                    'Site': site,
                    'Mean (°C) (±SE)': f"{round(temp_stats.get('overall_mean', 0), 2)} (±{round(temp_stats.get('overall_se', 0), 2)})",
                    'Minimum (°C)': round(temp_stats.get('overall_min', 0), 2),
                    'Maximum (°C)': round(temp_stats.get('overall_max', 0), 2),
                    'Min-Max Diff (°C)': round(temp_stats.get('overall_diff', 0), 2),
                    'Avg Daytime (°C)': round(temp_stats.get('day_mean', 0), 2),
                    'Avg Nighttime (°C)': round(temp_stats.get('night_mean', 0), 2)
                })
        
        df = pd.DataFrame(rows)
        
        return {
            'table_id': '3.4',
            'title': 'Table 3.4: Temperature Summary (Continuous Monitoring)',
            'dataframe': df,
            'notes': ['Daytime: 0900-1800; Night-time: 2100-0600']
        }
    
    def generate_table_3_5(self) -> Dict:
        """
        Table 3.5: Relative humidity summary (Continuous)
        """
        rows = []
        
        cont_sites = [site for site, data in self.processed_data.items() 
                     if data.get('monitoring_type') == 'continuous']
        
        for site in cont_sites:
            site_data = self.processed_data[site]
            rh_stats = site_data.get('humidity_stats', {})
            
            if rh_stats:
                rows.append({
                    'Site': site,
                    'Mean RH (%) (±SE)': f"{round(rh_stats.get('overall_mean', 0), 2)} (±{round(rh_stats.get('overall_se', 0), 2)})",
                    'Minimum RH (%)': round(rh_stats.get('overall_min', 0), 2),
                    'Maximum RH (%)': round(rh_stats.get('overall_max', 0), 2),
                    'Min-Max Diff (%)': round(rh_stats.get('overall_diff', 0), 2),
                    'Avg Daytime RH (%)': round(rh_stats.get('day_mean', 0), 2),
                    'Avg Nighttime RH (%)': round(rh_stats.get('night_mean', 0), 2)
                })
        
        df = pd.DataFrame(rows)
        
        return {
            'table_id': '3.5',
            'title': 'Table 3.5: Relative Humidity Summary (Continuous Monitoring)',
            'dataframe': df,
            'notes': ['Daytime: 0900-1800; Night-time: 2100-0600']
        }
    
    def generate_table_3_6(self) -> Dict:
        """
        Table 3.6: PLNB activity summary
        """
        rows = []
        
        ssm_sites = [site for site, data in self.processed_data.items() 
                    if data.get('monitoring_type') == 'ssm']
        
        for site in ssm_sites:
            site_data = self.processed_data[site]
            plnb_stats = site_data.get('plnb_stats', {})
            
            # Calculate sampling nights from date range
            start_date = site_data.get('start_date')
            end_date = site_data.get('end_date')
            if start_date and end_date:
                sampling_nights = (end_date - start_date).days + 1
            else:
                sampling_nights = plnb_stats.get('sampling_nights', 0)
            
            if plnb_stats:
                rows.append({
                    'Cave ID': site_data['site_name'],
                    'Category': site_data['category'],
                    'Sampling Nights': sampling_nights,
                    'Average': round(plnb_stats.get('average_calls', 0), 1),
                    'Minimum': int(plnb_stats.get('min_calls', 0)),
                    'Maximum': int(plnb_stats.get('max_calls', 0)),
                    'SE (±)': round(plnb_stats.get('se', 0), 1)
                })
        
        df = pd.DataFrame(rows)
        
        return {
            'table_id': '3.6',
            'title': 'Table 3.6: Summary of Pilbara Leaf-Nosed Bat Calls',
            'dataframe': df,
            'notes': ['Calls per night statistics for SSM period']
        }
    
    def generate_table_3_7(self) -> Dict:
        """
        Table 3.7: PLNB timing relative to civil twilight
        """
        rows = []
        
        ssm_sites = [site for site, data in self.processed_data.items() 
                    if data.get('monitoring_type') == 'ssm']
        
        for site in ssm_sites:
            site_data = self.processed_data[site]
            plnb_stats = site_data.get('plnb_stats', {})
            
            # Calculate sampling nights from date range
            start_date = site_data.get('start_date')
            end_date = site_data.get('end_date')
            if start_date and end_date:
                sampling_nights = (end_date - start_date).days + 1
            else:
                sampling_nights = plnb_stats.get('sampling_nights', 0)
            
            avg_dusk = plnb_stats.get('avg_hours_from_dusk', np.nan)
            avg_dawn = plnb_stats.get('avg_hours_from_dawn', np.nan)
            
            # Format timing or "no calls"
            dusk_str = f"{avg_dusk:.2f}" if pd.notna(avg_dusk) and avg_dusk != 0 else "no calls"
            dawn_str = f"{avg_dawn:.2f}" if pd.notna(avg_dawn) and avg_dawn != 0 else "no calls"
            
            rows.append({
                'Cave ID': site_data['site_name'],
                'Category': site_data['category'],
                'Sampling Nights': sampling_nights,
                'Hours ± Civil Dusk': dusk_str,
                'Hours ± Civil Dawn': dawn_str
            })
        
        df = pd.DataFrame(rows)
        
        return {
            'table_id': '3.7',
            'title': 'Table 3.7: Timing of Pilbara Leaf-Nosed Bat Calls',
            'dataframe': df,
            'notes': ['Average hours relative to civil twilight during SSM period']
        }
    
    def generate_table_3_8(self) -> Dict:
        """
        Table 3.8: Ghost Bat ultrasonic records matrix
        R = roosting, C = calls, NC = no calls, - = no sampling
        """
        rows = []
        
        ssm_sites = [site for site, data in self.processed_data.items() 
                    if data.get('monitoring_type') == 'ssm']
        
        # Get all unique dates across SSM sites
        all_dates = set()
        for site in ssm_sites:
            site_data = self.processed_data[site]
            df = site_data.get('raw_data', pd.DataFrame())
            if not df.empty and len(df.columns) > 0:
                dates = pd.to_datetime(df.iloc[:, 0], errors='coerce').dt.date
                all_dates.update(dates.dropna())
        
        date_columns = sorted(list(all_dates))[:10]  # Limit to first 10 dates for display
        
        for site in ssm_sites:
            site_data = self.processed_data[site]
            df = site_data.get('raw_data', pd.DataFrame())
            gb_stats = site_data.get('ghost_bat_stats', {})
            
            row = {
                'Cave ID': site,
                'Category': site_data['category']
            }
            
            # For each date, determine status
            for date in date_columns:
                status = '-'
                
                if not df.empty and len(df.columns) > 4:
                    df_copy = df.copy()
                    df_copy.iloc[:, 0] = pd.to_datetime(df_copy.iloc[:, 0], errors='coerce')
                    date_row = df_copy[df_copy.iloc[:, 0].dt.date == date]
                    
                    if not date_row.empty:
                        roosting = date_row.iloc[0, 4] if len(date_row.columns) > 4 else None
                        calls = date_row.iloc[0, 3] if len(date_row.columns) > 3 else None
                        
                        # Determine status
                        if pd.notna(roosting):
                            roosting_str = str(roosting).strip().lower()
                            if roosting_str == 'yes':
                                status = 'R'
                        
                        if status != 'R' and pd.notna(calls):
                            try:
                                call_val = str(calls).strip()
                                if call_val and call_val != 'nan':
                                    if '>' in call_val or (call_val.replace('.','').replace('-','').isdigit() and float(call_val) > 0):
                                        status = 'C'
                                    else:
                                        status = 'NC'
                            except:
                                status = 'NC'
                        elif status != 'R':
                            status = 'NC'
                
                row[date.strftime('%d/%m/%y')] = status
            
            row['Sampling Nights'] = (site_data['end_date'] - site_data['start_date']).days + 1 if site_data.get('start_date') and site_data.get('end_date') else gb_stats.get('sampled_days', 0)
            row['Call Range'] = gb_stats.get('call_range', '-')
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        return {
            'table_id': '3.8',
            'title': 'Table 3.8: Ghost Bat Ultrasonic Records',
            'dataframe': df,
            'notes': ["R = roosting indicated; C = calls recorded; NC = no calls; - = no sampling"]
        }
    
    def generate_table_3_9(self) -> Dict:
        """Table 3.9: Call data for continuous monitoring at CMPC-03"""
        return self._generate_continuous_call_table('CMPC-03', '3.9')
    
    def generate_table_3_10(self) -> Dict:
        """Table 3.10: Call data for continuous monitoring at CMPC-08"""
        return self._generate_continuous_call_table('CMPC-08', '3.10')
    
    def generate_table_3_11(self) -> Dict:
        """Table 3.11: Call data for continuous monitoring at CMPC-10"""
        return self._generate_continuous_call_table('CMPC-10', '3.11')
    
    def generate_table_3_12(self) -> Dict:
        """Table 3.12: Call data for continuous monitoring at CMPC-25"""
        return self._generate_continuous_call_table('CMPC-25', '3.12')
    
    
    def _generate_continuous_call_table(self, site_name: str, table_id: str) -> Dict:
        """
        Generate continuous monitoring call data table for a specific site
        Shows monthly PLNB call statistics including roosting indication
        """
        rows = []
        
        # Find this site in processed data
        site_data = None
        for site, data in self.processed_data.items():
            if site_name in site and data.get('monitoring_type') == 'continuous':
                site_data = data
                break
        
        if not site_data or not site_data.get('monthly_stats'):
            return self._empty_table(f"Table {table_id}: Call data for continuous monitoring at {site_name}")
        
        monthly_stats = site_data['monthly_stats']
        
        for month in sorted(monthly_stats.keys(), key=lambda x: datetime.strptime(x, '%b-%y')):
            month_data = monthly_stats[month]
            plnb_stats = month_data.get('plnb_stats', {})
            
            # Calculate % of days with calls
            total_calls = plnb_stats.get('total_calls', 0)
            sampling_nights = plnb_stats.get('sampling_nights', 0)
            pct_with_calls = plnb_stats.get('pct_nights_with_calls', 0)
            
            # Get roosting indication percentage
            pct_roosting = plnb_stats.get('pct_roosting', 0)
            
            # Get min/max (excluding empty/NaN)
            min_calls = plnb_stats.get('min_calls', 0)
            max_calls = plnb_stats.get('max_calls', 0)
            
            # Handle case where no sampling occurred
            if sampling_nights == 0:
                lowest_str = '-'
                highest_str = '-'
                roosting_pct_str = '-'
            else:
                lowest_str = str(int(min_calls)) if pd.notna(min_calls) else '-'
                highest_str = str(int(max_calls)) if pd.notna(max_calls) else '-'
                # Format roosting percentage as integer (0 decimal places)
                roosting_pct_str = int(round(pct_roosting)) if pd.notna(pct_roosting) else 0
            
            rows.append({
                'Sampling month': month,
                '% of days with calls recorded': round(pct_with_calls, 0) if sampling_nights > 0 else '-',
                'Total calls during month': int(total_calls) if sampling_nights > 0 else '-',
                'Lowest call total during month': lowest_str,
                'Highest call total during month': highest_str,
                '% of days where calls were indicative of roosting': roosting_pct_str
            })
        
        df = pd.DataFrame(rows)
        
        return {
            'table_id': table_id,
            'title': f"Table {table_id}: Call data for continuous monitoring at {site_name}",
            'dataframe': df,
            'notes': ['Monthly PLNB call activity summary']
        }
    def _generate_monthly_climate_table(self, climate_type: str, monitoring: str, table_id: str) -> Dict:
        """Helper to generate monthly climate tables"""
        rows = []
        
        sites = [site for site, data in self.processed_data.items() 
                if data.get('monitoring_type') == monitoring]
        
        if not sites:
            return self._empty_table(f"Table {table_id}: Monthly {climate_type.title()} ({monitoring.upper()})")
        
        # Get all unique months
        all_months = set()
        for site in sites:
            site_data = self.processed_data[site]
            monthly_stats = site_data.get('monthly_stats', {})
            all_months.update(monthly_stats.keys())
        
        sorted_months = sorted(list(all_months), key=lambda x: datetime.strptime(x, '%b-%y'))
        
        for site in sites:
            site_data = self.processed_data[site]
            monthly_stats = site_data.get('monthly_stats', {})
            
            for month in sorted_months:
                if month in monthly_stats:
                    month_data = monthly_stats[month]
                    stats_key = f"{climate_type}_stats"
                    stats = month_data.get(stats_key, {})
                    
                    if stats:
                        row = {
                            'Site': site,
                            'Month': month,
                            'Mean': round(stats.get('overall_mean', 0), 2),
                            'Min': round(stats.get('overall_min', 0), 2),
                            'Max': round(stats.get('overall_max', 0), 2),
                            'Day Avg': round(stats.get('day_mean', 0), 2),
                            'Night Avg': round(stats.get('night_mean', 0), 2)
                        }
                        rows.append(row)
        
        df = pd.DataFrame(rows)
        
        return {
            'table_id': table_id,
            'title': f"Table {table_id}: Monthly {climate_type.title()} ({monitoring.title()})",
            'dataframe': df,
            'notes': []
        }
    
    def generate_table_3_13(self) -> Dict:
        """
        Table 3.13: Proportion of sampling period with roosting evidence
        """
        rows = []
        
        cont_sites = [site for site, data in self.processed_data.items() 
                     if data.get('monitoring_type') == 'continuous']
        
        if not cont_sites:
            return self._empty_table("Table 3.13: Roosting Evidence by Month")
        
        # Get all unique months across all sites
        all_months = set()
        for site in cont_sites:
            site_data = self.processed_data[site]
            monthly_stats = site_data.get('monthly_stats', {})
            all_months.update(monthly_stats.keys())
        
        if not all_months:
            return self._empty_table("Table 3.13: Roosting Evidence by Month")
        
        sorted_months = sorted(list(all_months), key=lambda x: datetime.strptime(x, '%b-%y'))
        
        for site in cont_sites:
            site_data = self.processed_data[site]
            monthly_stats = site_data.get('monthly_stats', {})
            
            # Use clean site name
            row = {'Site': site_data['site_name']}
            
            for month in sorted_months:
                if month in monthly_stats:
                    month_data = monthly_stats[month]
                    gb_stats = month_data.get('gb_stats', {})
                    
                    roosting_count = gb_stats.get('roosting_count', 0)
                    sampled_days = gb_stats.get('sampled_days', 0)
                    
                    if sampled_days > 0:
                        pct = int((roosting_count / sampled_days) * 100)
                        row[month] = f"{roosting_count}/{sampled_days} ({pct}%)"
                    else:
                        row[month] = '-'
                else:
                    row[month] = '-'
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        return {
            'table_id': '3.13',
            'title': 'Table 3.13: Roosting Evidence by Month',
            'dataframe': df,
            'notes': ['- = no sampling during this month']
        }
    
    def generate_table_3_14(self) -> Dict:
        """
        Table 3.14: Range of Ghost Bat calls recorded
        """
        rows = []
        
        cont_sites = [site for site, data in self.processed_data.items() 
                     if data.get('monitoring_type') == 'continuous']
        
        if not cont_sites:
            return self._empty_table("Table 3.14: Ghost Bat Call Range by Month")
        
        # Get all unique months
        all_months = set()
        for site in cont_sites:
            site_data = self.processed_data[site]
            monthly_stats = site_data.get('monthly_stats', {})
            all_months.update(monthly_stats.keys())
        
        if not all_months:
            return self._empty_table("Table 3.14: Ghost Bat Call Range by Month")
        
        sorted_months = sorted(list(all_months), key=lambda x: datetime.strptime(x, '%b-%y'))
        
        for site in cont_sites:
            site_data = self.processed_data[site]
            monthly_stats = site_data.get('monthly_stats', {})
            
            # Use clean site name
            row = {'Site': site_data['site_name']}
            
            for month in sorted_months:
                if month in monthly_stats:
                    month_data = monthly_stats[month]
                    gb_stats = month_data.get('gb_stats', {})
                    
                    call_range = gb_stats.get('call_range', '-')
                    row[month] = call_range
                else:
                    row[month] = '-'
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        return {
            'table_id': '3.14',
            'title': 'Table 3.14: Ghost Bat Call Range by Month',
            'dataframe': df,
            'notes': ['- = no sampling during this month; >15 indicates calls exceeded threshold']
        }
    
    def _empty_table(self, title: str) -> Dict:
        """Return an empty table structure"""
        return {
            'table_id': '',
            'title': title,
            'dataframe': pd.DataFrame(),
            'notes': ['No data available for this configuration']
        }