"""
Microclimate Stacked Area Chart - Monthly Time Series
Shows proportion of time in different suitability categories
Similar to car colors chart style
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class MicroclimateStackedChart:
    """Generates stacked area charts showing suitability over time"""
    
    def __init__(self):
        # Biologic colors
        self.BIOLOGIC_TEAL = '#1F4D4D'
        self.BIOLOGIC_GOLD = '#D4AF37'
        self.BIOLOGIC_GREEN = '#4A7C59'
        
        # Suitability color scheme (matches heat maps)
        self.COLORS = {
            'optimal': '#4A7C59',        # Green
            'marginal': '#FFD700',       # Yellow
            'suboptimal': '#FFA500',     # Orange
            'poor': '#FF8C00',           # Dark Orange
            'unsuitable': '#CD5C5C',     # Red-Orange
            'highly_unsuitable': '#8B0000'  # Dark Red
        }
        
        # Species requirements
        self.species_ranges = {
            'Ghost Bat': {
                'temp_min': 23, 'temp_max': 28,
                'rh_min': 50, 'rh_max': 102
            },
            'PLNB': {
                'temp_min': 28, 'temp_max': 32,
                'rh_min': 85, 'rh_max': 102
            }
        }
    
    def categorize_reading(self, value, min_val, max_val):
        """Categorize a reading into suitability categories"""
        if pd.isna(value):
            return None
        
        # In optimal range
        if min_val <= value <= max_val:
            return 'optimal'
        
        # Calculate percentage out of range
        if value < min_val:
            distance = min_val - value
            boundary = min_val
        else:
            distance = value - max_val
            boundary = max_val
        
        pct_out = (distance / boundary) * 100 if boundary > 0 else 0
        
        if pct_out <= 10:
            return 'marginal'
        elif pct_out <= 20:
            return 'suboptimal'
        elif pct_out <= 30:
            return 'poor'
        elif pct_out <= 40:
            return 'unsuitable'
        else:
            return 'highly_unsuitable'
    
    def calculate_range_labels(self, min_val, max_val, value_type='temp'):
        """Calculate numeric ranges for optimal only, ± for others"""
        ranges = {}
        
        # Optimal - show actual ranges
        if value_type == 'temp':
            ranges['optimal'] = f"{min_val}-{max_val}°C"
        else:  # For RH, cap max at 100%
            display_max = min(max_val, 100)
            ranges['optimal'] = f"{min_val}-{display_max}%"
        
        # All others - just show ± percentage
        ranges['marginal'] = "±10%"
        ranges['suboptimal'] = "±10-20%"
        ranges['poor'] = "±20-30%"
        ranges['unsuitable'] = "±30-40%"
        ranges['highly_unsuitable'] = ">±40%"
        
        return ranges
    
    def generate_stacked_chart(self, raw_df, cave_name, species, 
                               start_date, end_date, output_path=None):
        """
        Generate THREE stacked area charts with months on x-axis
        1. Temperature suitability
        2. Humidity suitability  
        3. Combined suitability
        """
        print(f"\n{'='*70}")
        print(f"Generating stacked chart: {cave_name} - {species}")
        print(f"{'='*70}")
        
        # Get species requirements
        species_req = self.species_ranges[species]
        
        # Temperature columns: V-AC (indices 21-28)
        temp_indices = list(range(21, 29))
        # RH columns: AD-AK (indices 29-36)
        rh_indices = list(range(29, 37))
        
        # Process data
        df = raw_df.copy()
        date_col = df.columns[0]
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Filter by date range
        mask = (df[date_col].dt.date >= start_date) & (df[date_col].dt.date <= end_date)
        df = df[mask].copy()
        
        if df.empty:
            print("No data in date range")
            return None
        
        # Add month column
        df['Month'] = df[date_col].dt.to_period('M')
        
        # Calculate monthly category counts for TEMPERATURE and HUMIDITY separately
        monthly_temp_data = []
        monthly_rh_data = []
        monthly_combined_data = []
        
        for month in sorted(df['Month'].unique()):
            month_df = df[df['Month'] == month]
            
            # Collect all temperature readings
            temp_readings = []
            for idx in temp_indices:
                if idx < len(df.columns):
                    vals = pd.to_numeric(month_df.iloc[:, idx], errors='coerce').dropna()
                    temp_readings.extend(vals.tolist())
            
            # Collect all humidity readings
            rh_readings = []
            for idx in rh_indices:
                if idx < len(df.columns):
                    vals = pd.to_numeric(month_df.iloc[:, idx], errors='coerce').dropna()
                    rh_readings.extend(vals.tolist())
            
            # Categorize each reading
            temp_categories = [self.categorize_reading(t, species_req['temp_min'], 
                                                      species_req['temp_max']) 
                             for t in temp_readings]
            rh_categories = [self.categorize_reading(r, species_req['rh_min'], 
                                                    species_req['rh_max']) 
                           for r in rh_readings]
            
            # Count each category for TEMPERATURE
            temp_counts = {
                'optimal': temp_categories.count('optimal'),
                'marginal': temp_categories.count('marginal'),
                'suboptimal': temp_categories.count('suboptimal'),
                'poor': temp_categories.count('poor'),
                'unsuitable': temp_categories.count('unsuitable'),
                'highly_unsuitable': temp_categories.count('highly_unsuitable')
            }
            temp_total = sum(temp_counts.values())
            if temp_total > 0:
                temp_pcts = {k: (v / temp_total) * 100 for k, v in temp_counts.items()}
                temp_pcts['month'] = month
                monthly_temp_data.append(temp_pcts)
            
            # Count each category for HUMIDITY
            rh_counts = {
                'optimal': rh_categories.count('optimal'),
                'marginal': rh_categories.count('marginal'),
                'suboptimal': rh_categories.count('suboptimal'),
                'poor': rh_categories.count('poor'),
                'unsuitable': rh_categories.count('unsuitable'),
                'highly_unsuitable': rh_categories.count('highly_unsuitable')
            }
            rh_total = sum(rh_counts.values())
            if rh_total > 0:
                rh_pcts = {k: (v / rh_total) * 100 for k, v in rh_counts.items()}
                rh_pcts['month'] = month
                monthly_rh_data.append(rh_pcts)
            
            # For COMBINED suitability, take the worst (most restrictive) category
            combined_categories = []
            for i in range(min(len(temp_categories), len(rh_categories))):
                if temp_categories[i] and rh_categories[i]:
                    severity_order = ['optimal', 'marginal', 'suboptimal', 
                                    'poor', 'unsuitable', 'highly_unsuitable']
                    temp_severity = severity_order.index(temp_categories[i])
                    rh_severity = severity_order.index(rh_categories[i])
                    worst_idx = max(temp_severity, rh_severity)
                    combined_categories.append(severity_order[worst_idx])
            
            combined_counts = {
                'optimal': combined_categories.count('optimal'),
                'marginal': combined_categories.count('marginal'),
                'suboptimal': combined_categories.count('suboptimal'),
                'poor': combined_categories.count('poor'),
                'unsuitable': combined_categories.count('unsuitable'),
                'highly_unsuitable': combined_categories.count('highly_unsuitable')
            }
            combined_total = sum(combined_counts.values())
            if combined_total > 0:
                combined_pcts = {k: (v / combined_total) * 100 for k, v in combined_counts.items()}
                combined_pcts['month'] = month
                monthly_combined_data.append(combined_pcts)
        
        if not monthly_temp_data or not monthly_rh_data or not monthly_combined_data:
            print("No valid monthly data")
            return None
        
        temp_df = pd.DataFrame(monthly_temp_data).sort_values('month')
        rh_df = pd.DataFrame(monthly_rh_data).sort_values('month')
        combined_df = pd.DataFrame(monthly_combined_data).sort_values('month')
        
        print(f"Processing {len(temp_df)} months")
        
        # Calculate range labels with actual numbers
        temp_ranges = self.calculate_range_labels(species_req['temp_min'], 
                                                   species_req['temp_max'], 'temp')
        rh_ranges = self.calculate_range_labels(species_req['rh_min'], 
                                                species_req['rh_max'], 'rh')
        
        # Create figure with 3 subplots SIDE BY SIDE for A3 landscape
        plt.rcParams['figure.dpi'] = 600  # Reduced from 900 to prevent memory errors
        plt.rcParams['savefig.dpi'] = 600
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Montserrat', 'DejaVu Sans', 'Arial']
        plt.rcParams['font.size'] = 7
        
        # A3 landscape - wider and less tall for better proportions
        # 42cm wide × 16cm tall
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(42/2.54, 16/2.54))
        
        # Add main title at top
        fig.suptitle(f'{cave_name} - {species}', 
                    fontweight='bold', fontsize=11, color=self.BIOLOGIC_TEAL, y=0.98)
        
        # Stack from bottom to top (worst to best)
        categories = ['highly_unsuitable', 'unsuitable', 'poor', 
                     'suboptimal', 'marginal', 'optimal']
        
        # Legend order (reversed - best to worst for display)
        legend_categories = ['optimal', 'marginal', 'suboptimal', 
                            'poor', 'unsuitable', 'highly_unsuitable']
        
        # ===== TEMPERATURE CHART (LEFT) =====
        x = range(len(temp_df))
        x_labels = [m.strftime('%b-%y') for m in temp_df['month']]
        
        y_stack = np.zeros(len(temp_df))
        for category in categories:
            y_values = temp_df[category].values
            ax1.fill_between(x, y_stack, y_stack + y_values,
                           color=self.COLORS[category],
                           alpha=0.9,
                           label=f"{category.replace('_', ' ').title()} ({temp_ranges[category]})",
                           edgecolor='white',
                           linewidth=0.3)
            y_stack += y_values
        
        ax1.set_xlim(0, len(temp_df) - 1)
        ax1.set_ylim(0, 100)
        ax1.set_xlabel('Month', fontweight='bold', fontsize=8)
        ax1.set_ylabel('Percentage of readings', fontweight='bold', fontsize=8)
        ax1.set_title('Temperature Suitability',
                     fontweight='bold', fontsize=9, color=self.BIOLOGIC_TEAL, pad=10)
        ax1.set_xticks(x[::max(1, len(x)//8)])  # Show ~8 labels max
        ax1.set_xticklabels([x_labels[i] for i in range(0, len(x), max(1, len(x)//8))], 
                           rotation=45, ha='right', fontsize=6)
        ax1.set_yticks([0, 20, 40, 60, 80, 100])
        ax1.set_yticklabels(['0%', '20%', '40%', '60%', '80%', '100%'], fontsize=6)
        ax1.grid(True, alpha=0.3, linestyle='--', linewidth=0.5, axis='y')
        ax1.set_axisbelow(True)
        
        # Get handles and labels, then reorder
        handles, labels = ax1.get_legend_handles_labels()
        # Reverse order for legend display (best to worst)
        handles_ordered = handles[::-1]
        labels_ordered = labels[::-1]
        
        # Legend - 2 columns to avoid overlap
        ax1.legend(handles_ordered, labels_ordered, 
                  loc='upper center', bbox_to_anchor=(0.5, -0.18),
                  ncol=2, fontsize=10, framealpha=0.95, columnspacing=2.0,
                  handlelength=2.0, handletextpad=0.8)
        
        # ===== HUMIDITY CHART (MIDDLE) =====
        x_rh = range(len(rh_df))
        x_rh_labels = [m.strftime('%b-%y') for m in rh_df['month']]
        
        y_stack_rh = np.zeros(len(rh_df))
        for category in categories:
            y_values = rh_df[category].values
            ax2.fill_between(x_rh, y_stack_rh, y_stack_rh + y_values,
                           color=self.COLORS[category],
                           alpha=0.9,
                           label=f"{category.replace('_', ' ').title()} ({rh_ranges[category]})",
                           edgecolor='white',
                           linewidth=0.3)
            y_stack_rh += y_values
        
        ax2.set_xlim(0, len(rh_df) - 1)
        ax2.set_ylim(0, 100)
        ax2.set_xlabel('Month', fontweight='bold', fontsize=8)
        ax2.set_ylabel('Percentage of readings', fontweight='bold', fontsize=8)
        ax2.set_title('Humidity Suitability',
                     fontweight='bold', fontsize=9, color=self.BIOLOGIC_TEAL, pad=10)
        ax2.set_xticks(x_rh[::max(1, len(x_rh)//8)])
        ax2.set_xticklabels([x_rh_labels[i] for i in range(0, len(x_rh), max(1, len(x_rh)//8))], 
                           rotation=45, ha='right', fontsize=6)
        ax2.set_yticks([0, 20, 40, 60, 80, 100])
        ax2.set_yticklabels(['0%', '20%', '40%', '60%', '80%', '100%'], fontsize=6)
        ax2.grid(True, alpha=0.3, linestyle='--', linewidth=0.5, axis='y')
        ax2.set_axisbelow(True)
        
        # Get handles and labels, then reorder
        handles, labels = ax2.get_legend_handles_labels()
        handles_ordered = handles[::-1]
        labels_ordered = labels[::-1]
        
        # Legend - 2 columns to avoid overlap
        ax2.legend(handles_ordered, labels_ordered,
                  loc='upper center', bbox_to_anchor=(0.5, -0.18),
                  ncol=2, fontsize=10, framealpha=0.95, columnspacing=2.0,
                  handlelength=2.0, handletextpad=0.8)
        
        # ===== COMBINED CHART (RIGHT) =====
        x_comb = range(len(combined_df))
        x_comb_labels = [m.strftime('%b-%y') for m in combined_df['month']]
        
        y_stack_comb = np.zeros(len(combined_df))
        for category in categories:
            y_values = combined_df[category].values
            ax3.fill_between(x_comb, y_stack_comb, y_stack_comb + y_values,
                           color=self.COLORS[category],
                           alpha=0.9,
                           label=f"{category.replace('_', ' ').title()}",
                           edgecolor='white',
                           linewidth=0.3)
            y_stack_comb += y_values
        
        ax3.set_xlim(0, len(combined_df) - 1)
        ax3.set_ylim(0, 100)
        ax3.set_xlabel('Month', fontweight='bold', fontsize=8)
        ax3.set_ylabel('Percentage of readings', fontweight='bold', fontsize=8)
        ax3.set_title('Combined Suitability',
                     fontweight='bold', fontsize=9, color=self.BIOLOGIC_TEAL, pad=10)
        ax3.set_xticks(x_comb[::max(1, len(x_comb)//8)])
        ax3.set_xticklabels([x_comb_labels[i] for i in range(0, len(x_comb), max(1, len(x_comb)//8))], 
                           rotation=45, ha='right', fontsize=6)
        ax3.set_yticks([0, 20, 40, 60, 80, 100])
        ax3.set_yticklabels(['0%', '20%', '40%', '60%', '80%', '100%'], fontsize=6)
        ax3.grid(True, alpha=0.3, linestyle='--', linewidth=0.5, axis='y')
        ax3.set_axisbelow(True)
        
        # Get handles and labels, then reorder
        handles, labels = ax3.get_legend_handles_labels()
        handles_ordered = handles[::-1]
        labels_ordered = labels[::-1]
        
        # Legend - 2 columns to avoid overlap
        ax3.legend(handles_ordered, labels_ordered,
                  loc='upper center', bbox_to_anchor=(0.5, -0.18),
                  ncol=2, fontsize=10, framealpha=0.95, columnspacing=2.0,
                  handlelength=2.0, handletextpad=0.8)
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])  # Leave space for suptitle
        
        # Save if output path provided
        if output_path:
            plt.savefig(output_path, dpi=600, bbox_inches='tight', 
                       facecolor='white', transparent=False)
            print(f"Saved: {output_path}")
        
        return fig
    
    def generate_all_stacked_charts(self, processed_data, output_dir='/mnt/user-data/outputs'):
        """Generate stacked charts for all continuous monitoring sites"""
        import os
        
        print(f"\n{'='*70}")
        print(f"GENERATING MICROCLIMATE STACKED AREA CHARTS")
        print(f"{'='*70}")
        
        # Get continuous monitoring sites
        continuous_sites = [site for site, data in processed_data.items() 
                           if data.get('monitoring_type') == 'continuous']
        
        print(f"Found {len(continuous_sites)} continuous monitoring sites")
        
        generated_count = 0
        
        for site_key in continuous_sites:
            site_data = processed_data[site_key]
            raw_df = site_data.get('raw_data')
            
            if raw_df is None or raw_df.empty:
                print(f"Skipping {site_key} - no data")
                continue
            
            cave_name = site_data.get('site_name', site_key)
            # Simplify cave name
            if '-' in cave_name:
                cave_simple = cave_name.split('-')[0] + ' ' + cave_name.split('-')[1]
            else:
                cave_simple = cave_name
            cave_simple = cave_simple.title()
            
            start_date = site_data.get('start_date')
            end_date = site_data.get('end_date')
            
            # Generate for both species
            for species in ['Ghost Bat', 'PLNB']:
                filename = f"StackedChart_{cave_simple.replace(' ', '_')}_{species.replace(' ', '_')}.png"
                filepath = os.path.join(output_dir, filename)
                
                try:
                    self.generate_stacked_chart(
                        raw_df, cave_simple, species, 
                        start_date, end_date, filepath
                    )
                    generated_count += 1
                    plt.close('all')
                except Exception as e:
                    print(f"Error generating {filename}: {e}")
                    import traceback
                    traceback.print_exc()
        
        print(f"\n{'='*70}")
        print(f"✅ Generated {generated_count} stacked area charts")
        print(f"{'='*70}\n")
        
        return generated_count
