"""
Microclimate Dual-Axis Line Chart - Temperature and Humidity Together
Shows actual temp and RH% values on dual y-axes with suitability zone backgrounds
Biologic Environmental Survey branding
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class MicroclimateDualAxisChart:
    """Generates dual-axis line charts with temperature and humidity together"""
    
    def __init__(self):
        # Biologic brand colors (for lines, fonts, and styling)
        self.BIOLOGIC_TEAL = '#1F4D4D'        # Dark teal - for text and primary line
        self.BIOLOGIC_SECONDARY = '#577A7A'   # Medium teal - for secondary line
        self.BIOLOGIC_GOLD = '#D4AF37'        # Gold - for accents
        
        # Suitability zone colors (semi-transparent/muted)
        self.ZONE_COLORS = {
            'optimal': '#4A7C59',        # Green
            'marginal': '#FFD700',       # Yellow
            'suboptimal': '#FFA500',     # Orange
            'unsuitable': '#CD5C5C'      # Red
        }
        
        # Species requirements
        self.species_ranges = {
            'Ghost Bat': {
                'temp_min': 23, 'temp_max': 28,
                'rh_min': 50, 'rh_max': 100
            },
            'PLNB': {
                'temp_min': 28, 'temp_max': 32,
                'rh_min': 85, 'rh_max': 100
            }
        }
    
    def calculate_zone_ranges(self, min_optimal, max_optimal, value_type='temp'):
        """
        Calculate the ranges for each colored zone
        
        Returns dict with zones and their y-value ranges
        """
        # Calculate zone boundaries based on percentage out of range
        range_width = max_optimal - min_optimal
        
        # For temperature, extend zones
        if value_type == 'temp':
            marginal_width = range_width * 0.10
            suboptimal_width = range_width * 0.20
            extension = 10  # Extra space beyond unsuitable
        else:  # humidity
            marginal_width = range_width * 0.10
            suboptimal_width = range_width * 0.20
            extension = 20
        
        zones = {
            'unsuitable_low': (min_optimal - suboptimal_width - extension, 
                              min_optimal - suboptimal_width),
            'suboptimal_low': (min_optimal - suboptimal_width, 
                              min_optimal - marginal_width),
            'marginal_low': (min_optimal - marginal_width, min_optimal),
            'optimal': (min_optimal, max_optimal),
            'marginal_high': (max_optimal, max_optimal + marginal_width),
            'suboptimal_high': (max_optimal + marginal_width, 
                               max_optimal + suboptimal_width),
            'unsuitable_high': (max_optimal + suboptimal_width, 
                               max_optimal + suboptimal_width + extension)
        }
        
        return zones
    
    def plot_zone_backgrounds(self, ax, temp_zones, rh_zones, alpha=0.25):
        """
        Plot colored horizontal bands for BOTH temperature and humidity zones
        Uses semi-transparent colors so zones are visible but not overwhelming
        """
        # Map zone names to colors
        zone_color_map = {
            'unsuitable_low': self.ZONE_COLORS['unsuitable'],
            'suboptimal_low': self.ZONE_COLORS['suboptimal'],
            'marginal_low': self.ZONE_COLORS['marginal'],
            'optimal': self.ZONE_COLORS['optimal'],
            'marginal_high': self.ZONE_COLORS['marginal'],
            'suboptimal_high': self.ZONE_COLORS['suboptimal'],
            'unsuitable_high': self.ZONE_COLORS['unsuitable']
        }
        
        # Temperature zones on left y-axis
        for zone_name, (y_min, y_max) in temp_zones.items():
            color = zone_color_map[zone_name]
            ax.axhspan(y_min, y_max, 
                      color=color, 
                      alpha=alpha,
                      zorder=1)
    
    def generate_dual_axis_chart(self, raw_df, cave_name, species, 
                                 start_date, end_date, output_path=None):
        """
        Generate dual-axis line chart showing temperature and humidity together
        
        Args:
            raw_df: DataFrame with raw site data
            cave_name: Name of the site
            species: 'Ghost Bat' or 'PLNB'
            start_date: Start date
            end_date: End date
            output_path: Path to save PNG (optional)
            
        Returns:
            matplotlib figure object
        """
        print(f"\n{'='*70}")
        print(f"Generating dual-axis chart: {cave_name} - {species}")
        print(f"{'='*70}")
        
        # Get species requirements
        species_req = self.species_ranges[species]
        
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
        
        # Get daily mean temperature and humidity
        # Using roost values: Column Y (index 24) for temp, Column AG (index 32) for RH
        dates = df[date_col]
        roost_temp = pd.to_numeric(df.iloc[:, 24], errors='coerce')  # roost_temp_mean
        roost_rh = pd.to_numeric(df.iloc[:, 32], errors='coerce')    # roost_rh_mean
        
        # Calculate zone ranges
        temp_zones = self.calculate_zone_ranges(
            species_req['temp_min'], 
            species_req['temp_max'], 
            'temp'
        )
        rh_zones = self.calculate_zone_ranges(
            species_req['rh_min'], 
            species_req['rh_max'], 
            'rh'
        )
        
        # Set up Montserrat font
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Montserrat', 'Arial', 'DejaVu Sans']
        
        # Create figure
        fig, ax1 = plt.subplots(figsize=(14, 7))
        fig.patch.set_facecolor('white')
        
        # Plot temperature zones on background (semi-transparent)
        self.plot_zone_backgrounds(ax1, temp_zones, rh_zones, alpha=0.25)
        
        # ==================== LEFT Y-AXIS (TEMPERATURE) ====================
        # Plot temperature line
        line1 = ax1.plot(dates, roost_temp, 
                        color=self.BIOLOGIC_TEAL,
                        linewidth=2.5,
                        label='Roost Temperature',
                        zorder=3)
        
        # Set temperature y-axis
        ax1.set_xlabel('Month', fontsize=12, fontweight='bold', 
                      color=self.BIOLOGIC_TEAL, family='Montserrat')
        ax1.set_ylabel('Temperature (°C)', fontsize=12, fontweight='bold',
                      color=self.BIOLOGIC_TEAL, family='Montserrat')
        
        # Set y-axis limits to show all zones
        temp_y_min = min(temp_zones.values(), key=lambda x: x[0])[0]
        temp_y_max = max(temp_zones.values(), key=lambda x: x[1])[1]
        ax1.set_ylim(temp_y_min, temp_y_max)
        
        # Style left y-axis (temperature)
        ax1.tick_params(axis='y', labelcolor=self.BIOLOGIC_TEAL, labelsize=10)
        ax1.spines['left'].set_color(self.BIOLOGIC_TEAL)
        ax1.spines['left'].set_linewidth(2)
        
        # ==================== RIGHT Y-AXIS (HUMIDITY) ====================
        ax2 = ax1.twinx()  # Create second y-axis
        
        # Plot humidity line
        line2 = ax2.plot(dates, roost_rh,
                        color=self.BIOLOGIC_SECONDARY,
                        linewidth=2.5,
                        label='Roost Humidity',
                        linestyle='--',
                        zorder=3)
        
        ax2.set_ylabel('Relative Humidity (%)', fontsize=12, fontweight='bold',
                      color=self.BIOLOGIC_SECONDARY, family='Montserrat')
        
        # Set humidity y-axis limits
        rh_y_min = max(0, min(rh_zones.values(), key=lambda x: x[0])[0])
        rh_y_max = min(100, max(rh_zones.values(), key=lambda x: x[1])[1])
        ax2.set_ylim(rh_y_min, rh_y_max)
        
        # Style right y-axis (humidity)
        ax2.tick_params(axis='y', labelcolor=self.BIOLOGIC_SECONDARY, labelsize=10)
        ax2.spines['right'].set_color(self.BIOLOGIC_SECONDARY)
        ax2.spines['right'].set_linewidth(2)
        
        # ==================== X-AXIS FORMATTING ====================
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b-%y'))
        ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right', 
                fontsize=10, color=self.BIOLOGIC_TEAL)
        
        # ==================== TITLE ====================
        title_text = f'{cave_name} - {species}\nMicroclimate Conditions (Temperature & Humidity)'
        ax1.set_title(title_text, fontsize=14, fontweight='bold', 
                     color=self.BIOLOGIC_TEAL, pad=20, family='Montserrat')
        
        # ==================== STYLING ====================
        # Remove top and bottom spines
        ax1.spines['top'].set_visible(False)
        ax2.spines['top'].set_visible(False)
        ax1.spines['bottom'].set_color(self.BIOLOGIC_TEAL)
        ax1.spines['bottom'].set_linewidth(1)
        
        # Add subtle grid for x-axis only
        ax1.grid(True, axis='x', linestyle='--', alpha=0.3, linewidth=0.5, 
                color=self.BIOLOGIC_TEAL)
        ax1.set_axisbelow(True)
        
        # ==================== LEGEND ====================
        # Combine legends from both axes
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc='upper left', fontsize=11, 
                  framealpha=0.95, edgecolor=self.BIOLOGIC_TEAL)
        
        # ==================== ZONE LEGEND ====================
        # Add text explanation of zones at bottom
        zone_text = (f'Background Zones: Green = Optimal ({species_req["temp_min"]}-{species_req["temp_max"]}°C, '
                    f'{species_req["rh_min"]}-{species_req["rh_max"]}%) | '
                    f'Yellow = Marginal (±10%) | Orange = Suboptimal (±20%) | Red = Unsuitable')
        
        fig.text(0.5, 0.02, zone_text, ha='center', fontsize=9, 
                style='italic', color=self.BIOLOGIC_TEAL, family='Montserrat')
        
        plt.tight_layout(rect=[0, 0.05, 1, 0.98])
        
        # Save if output path provided
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight',
                       facecolor='white', transparent=False)
            print(f"✅ Saved: {output_path}")
        
        return fig
    
    def generate_all_dual_axis_charts(self, processed_data, output_dir='/mnt/user-data/outputs'):
        """Generate dual-axis charts for all continuous monitoring sites"""
        import os
        
        print(f"\n{'='*70}")
        print(f"GENERATING DUAL-AXIS MICROCLIMATE CHARTS")
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
                filename = f"DualAxisChart_{cave_simple.replace(' ', '_')}_{species.replace(' ', '_')}.png"
                filepath = os.path.join(output_dir, filename)
                
                try:
                    self.generate_dual_axis_chart(
                        raw_df, cave_simple, species,
                        start_date, end_date, filepath
                    )
                    generated_count += 1
                    plt.close('all')
                except Exception as e:
                    print(f"❌ Error generating {filename}: {e}")
                    import traceback
                    traceback.print_exc()
        
        print(f"\n{'='*70}")
        print(f"✅ Generated {generated_count} dual-axis charts")
        print(f"{'='*70}\n")
        
        return generated_count


# Example usage
if __name__ == "__main__":
    chart_generator = MicroclimateDualAxisChart()
    print("Dual-axis microclimate chart module loaded successfully")
    print("This shows temperature and humidity together on one chart with dual y-axes")
