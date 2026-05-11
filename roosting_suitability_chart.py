"""
Roosting Suitability Chart Module
=================================
Creates time-series charts showing roosting condition suitability over time
with smooth colour transitions (green/yellow/red) similar to the stock chart style.

Three vertically stacked charts per site:
1. Temperature suitability
2. Humidity suitability
3. Combined suitability (both conditions must be met)

Output: A3 landscape, 900 DPI
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from matplotlib.collections import PolyCollection
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Union
import warnings
warnings.filterwarnings('ignore')


# =============================================================================
# BIOLOGIC DESIGN CONSTANTS
# =============================================================================

BIOLOGIC_COLORS = {
    'primary_teal': '#1F4D4D',
    'secondary_teal': '#577A7A',
    'gold': '#D4AF37',
    'green': '#4A7C59',
    'text': '#333333',
    'grid': '#E0E0E0',
}

# Three-tier suitability colours with smooth transitions
SUITABILITY_COLORS = {
    'optimal': '#2E8B57',      # Sea green (rich green)
    'marginal': '#FFD700',     # Gold/yellow
    'unsuitable': '#CD5C5C',   # Indian red
}

# Species requirements
SPECIES_RANGES = {
    'Ghost Bat': {
        'temp_min': 23, 'temp_max': 28,
        'rh_min': 50, 'rh_max': 100
    },
    'PLNB': {
        'temp_min': 28, 'temp_max': 32,
        'rh_min': 85, 'rh_max': 100
    }
}


# =============================================================================
# COLOUR MAPPING FUNCTIONS
# =============================================================================

def create_smooth_colormap():
    """
    Create a smooth colour gradient: Red -> Yellow -> Green
    Returns a colormap that transitions nicely between unsuitable -> marginal -> optimal
    """
    # Define colour stops: unsuitable (red) -> marginal (yellow) -> optimal (green)
    colors = [
        (0.0, SUITABILITY_COLORS['unsuitable']),   # 0% suitability = red
        (0.5, SUITABILITY_COLORS['marginal']),     # 50% suitability = yellow
        (1.0, SUITABILITY_COLORS['optimal']),      # 100% suitability = green
    ]
    
    # Extract positions and colours
    positions = [c[0] for c in colors]
    hex_colors = [c[1] for c in colors]
    
    # Convert hex to RGB
    rgb_colors = [mcolors.hex2color(c) for c in hex_colors]
    
    # Create the colormap
    cmap = mcolors.LinearSegmentedColormap.from_list(
        'suitability', 
        list(zip(positions, rgb_colors)),
        N=256
    )
    
    return cmap


def calculate_suitability_score(value: float, min_val: float, max_val: float) -> float:
    """
    Calculate suitability score (0-1) for a given value.
    
    Returns:
        1.0 = Optimal (within range)
        0.5 = Marginal (within 15% buffer)
        0.0 = Unsuitable (>15% outside range)
        
    Smooth interpolation between tiers.
    """
    if pd.isna(value):
        return np.nan
    
    # Within optimal range
    if min_val <= value <= max_val:
        return 1.0
    
    # Calculate distance from nearest boundary
    if value < min_val:
        distance = min_val - value
        boundary = min_val
    else:
        distance = value - max_val
        boundary = max_val
    
    # Calculate percentage deviation
    pct_deviation = (distance / boundary) * 100 if boundary > 0 else 0
    
    # Three-tier with smooth transitions:
    # 0-5% out: Mostly optimal (0.9-1.0)
    # 5-15% out: Marginal zone (0.5-0.9)
    # 15-30% out: Transitioning to unsuitable (0.1-0.5)
    # >30% out: Unsuitable (0.0-0.1)
    
    if pct_deviation <= 5:
        # Near optimal - slight yellow tinge
        return 1.0 - (pct_deviation / 5) * 0.1  # 1.0 to 0.9
    elif pct_deviation <= 15:
        # Marginal zone - yellow
        return 0.9 - ((pct_deviation - 5) / 10) * 0.4  # 0.9 to 0.5
    elif pct_deviation <= 30:
        # Transitioning to unsuitable - orange to red
        return 0.5 - ((pct_deviation - 15) / 15) * 0.4  # 0.5 to 0.1
    else:
        # Highly unsuitable - deep red
        return max(0.0, 0.1 - ((pct_deviation - 30) / 20) * 0.1)  # 0.1 to 0.0


def get_tier_label(score: float) -> str:
    """Get the tier label for a suitability score"""
    if score >= 0.7:
        return 'Optimal'
    elif score >= 0.3:
        return 'Marginal'
    else:
        return 'Unsuitable'


# =============================================================================
# DATA PROCESSING
# =============================================================================

def process_microclimate_data(
    raw_df: pd.DataFrame,
    start_date: date,
    end_date: date,
    species: str = 'Ghost Bat',
    resolution: str = 'daily'
) -> Tuple[pd.DataFrame, Dict]:
    """
    Process raw microclimate data into daily/3-hourly suitability scores.
    
    Parameters
    ----------
    raw_df : pd.DataFrame
        Raw data with columns V-AC (temp) and AD-AK (RH)
    start_date : date
        Start of analysis period
    end_date : date
        End of analysis period
    species : str
        'Ghost Bat' or 'PLNB'
    resolution : str
        'daily' for daily means, '3hourly' for raw readings
    
    Returns
    -------
    Tuple[pd.DataFrame, Dict]
        DataFrame with datetime, temp, rh, temp_score, rh_score, combined_score
        Dict with processing statistics
    """
    # Get species requirements
    species_req = SPECIES_RANGES[species]
    
    # Column indices
    temp_indices = list(range(21, 29))  # V-AC
    rh_indices = list(range(29, 37))    # AD-AK
    
    # Time labels for 3-hourly readings
    time_hours = [21, 0, 3, 6, 9, 12, 15, 18]
    
    # Process data
    df = raw_df.copy()
    date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
    
    # Filter by date range
    mask = (df[date_col].dt.date >= start_date) & (df[date_col].dt.date <= end_date)
    df = df[mask].copy()
    
    if df.empty:
        return pd.DataFrame(), {'error': 'No data in date range'}
    
    records = []
    
    for _, row in df.iterrows():
        base_date = row[date_col]
        if pd.isna(base_date):
            continue
        
        # Extract 8 readings per day
        for i, (temp_idx, rh_idx) in enumerate(zip(temp_indices, rh_indices)):
            if temp_idx < len(row) and rh_idx < len(row):
                temp_val = pd.to_numeric(row.iloc[temp_idx], errors='coerce')
                rh_val = pd.to_numeric(row.iloc[rh_idx], errors='coerce')
                
                # Calculate timestamp
                hour = time_hours[i]
                if hour < 12 and i > 0:  # Next day for 00:00, 03:00, 06:00, 09:00
                    timestamp = base_date + pd.Timedelta(days=1, hours=hour)
                else:
                    timestamp = base_date + pd.Timedelta(hours=hour)
                
                # Calculate suitability scores
                temp_score = calculate_suitability_score(
                    temp_val, species_req['temp_min'], species_req['temp_max']
                )
                rh_score = calculate_suitability_score(
                    rh_val, species_req['rh_min'], species_req['rh_max']
                )
                
                # Combined score: minimum of both (must satisfy BOTH conditions)
                if pd.notna(temp_score) and pd.notna(rh_score):
                    combined_score = min(temp_score, rh_score)
                else:
                    combined_score = np.nan
                
                records.append({
                    'datetime': timestamp,
                    'temperature': temp_val,
                    'humidity': rh_val,
                    'temp_score': temp_score,
                    'rh_score': rh_score,
                    'combined_score': combined_score
                })
    
    result_df = pd.DataFrame(records)
    
    if result_df.empty:
        return pd.DataFrame(), {'error': 'No valid readings extracted'}
    
    # Sort by datetime
    result_df = result_df.sort_values('datetime').reset_index(drop=True)
    
    # Aggregate to daily if requested
    if resolution == 'daily':
        result_df['date'] = result_df['datetime'].dt.date
        daily_df = result_df.groupby('date').agg({
            'temperature': 'mean',
            'humidity': 'mean',
            'temp_score': 'mean',
            'rh_score': 'mean',
            'combined_score': 'mean'
        }).reset_index()
        daily_df['datetime'] = pd.to_datetime(daily_df['date'])
        result_df = daily_df.drop(columns=['date'])
    
    # Calculate statistics
    stats = {
        'total_records': len(result_df),
        'date_range': f"{result_df['datetime'].min().strftime('%d/%m/%Y')} - {result_df['datetime'].max().strftime('%d/%m/%Y')}",
        'temp_mean': result_df['temperature'].mean(),
        'temp_range': f"{result_df['temperature'].min():.1f} - {result_df['temperature'].max():.1f}°C",
        'rh_mean': result_df['humidity'].mean(),
        'rh_range': f"{result_df['humidity'].min():.1f} - {result_df['humidity'].max():.1f}%",
        'pct_optimal_temp': (result_df['temp_score'] >= 0.7).sum() / len(result_df) * 100,
        'pct_optimal_rh': (result_df['rh_score'] >= 0.7).sum() / len(result_df) * 100,
        'pct_optimal_combined': (result_df['combined_score'] >= 0.7).sum() / len(result_df) * 100,
    }
    
    return result_df, stats


# =============================================================================
# CHART GENERATION
# =============================================================================

def create_suitability_chart(
    raw_df: pd.DataFrame,
    cave_name: str,
    species: str,
    start_date: date,
    end_date: date,
    output_path: Optional[Union[str, Path]] = None,
    resolution: str = 'daily'
) -> Optional[plt.Figure]:
    """
    Create a roosting suitability chart with three vertically stacked panels.
    
    Parameters
    ----------
    raw_df : pd.DataFrame
        Raw microclimate data
    cave_name : str
        Name of the cave/site
    species : str
        'Ghost Bat' or 'PLNB'
    start_date : date
        Start of analysis period
    end_date : date
        End of analysis period
    output_path : Optional[Union[str, Path]]
        Path to save the figure
    resolution : str
        'daily' for daily means, '3hourly' for raw readings
    
    Returns
    -------
    Optional[plt.Figure]
        The figure object, or None if no data
    """
    print(f"\n{'='*70}")
    print(f"Generating roosting suitability chart: {cave_name} - {species}")
    print(f"Period: {start_date} to {end_date}")
    print(f"{'='*70}")
    
    # Process data
    data_df, stats = process_microclimate_data(
        raw_df, start_date, end_date, species, resolution
    )
    
    if data_df.empty:
        print(f"  ❌ No data available: {stats.get('error', 'Unknown error')}")
        return None
    
    print(f"  ✓ {stats['total_records']} records processed")
    print(f"  ✓ Date range: {stats['date_range']}")
    print(f"  ✓ Temperature: {stats['temp_range']} (mean: {stats['temp_mean']:.1f}°C)")
    print(f"  ✓ Humidity: {stats['rh_range']} (mean: {stats['rh_mean']:.1f}%)")
    
    # Get species requirements for axis labels
    species_req = SPECIES_RANGES[species]
    
    # Setup figure - A3 landscape (420mm x 297mm = 16.54" x 11.69")
    plt.rcParams['figure.dpi'] = 150
    plt.rcParams['savefig.dpi'] = 900
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Montserrat', 'DejaVu Sans', 'Arial']
    plt.rcParams['font.size'] = 9
    
    # A3 landscape dimensions
    fig_width = 16.54  # inches
    fig_height = 11.69  # inches
    
    # Don't share x-axis so all three charts show date labels
    fig, axes = plt.subplots(3, 1, figsize=(fig_width, fig_height), 
                             sharex=False, gridspec_kw={'hspace': 0.35})
    
    # Get colourmap
    cmap = create_smooth_colormap()
    
    # Common x-axis data
    dates = data_df['datetime'].values
    
    # =========================================================================
    # CHART 1: TEMPERATURE SUITABILITY
    # =========================================================================
    ax1 = axes[0]
    temp_values = data_df['temperature'].values
    temp_scores = data_df['temp_score'].values
    
    _plot_suitability_panel(
        ax1, dates, temp_values, temp_scores, cmap,
        title=f'Temperature Suitability',
        ylabel='Temperature (°C)',
        optimal_range=(species_req['temp_min'], species_req['temp_max']),
        value_type='temp'
    )
    
    # =========================================================================
    # CHART 2: HUMIDITY SUITABILITY
    # =========================================================================
    ax2 = axes[1]
    rh_values = data_df['humidity'].values
    rh_scores = data_df['rh_score'].values
    
    _plot_suitability_panel(
        ax2, dates, rh_values, rh_scores, cmap,
        title=f'Relative Humidity Suitability',
        ylabel='Relative Humidity (%)',
        optimal_range=(species_req['rh_min'], species_req['rh_max']),
        value_type='rh'
    )
    
    # =========================================================================
    # CHART 3: COMBINED SUITABILITY
    # =========================================================================
    ax3 = axes[2]
    combined_scores = data_df['combined_score'].values
    
    _plot_combined_suitability_panel(
        ax3, dates, combined_scores, cmap,
        title='Combined Roosting Suitability',
        ylabel='Suitability Index'
    )
    
    # Format x-axis on bottom chart
    ax3.tick_params(axis='x', rotation=45)
    
    # Main title
    fig.suptitle(
        f'{cave_name} - {species} Roosting Suitability Analysis\n'
        f'{start_date.strftime("%d %B %Y")} to {end_date.strftime("%d %B %Y")}',
        fontsize=14, fontweight='bold', color=BIOLOGIC_COLORS['primary_teal'],
        y=0.98
    )
    
    # Add legend
    _add_suitability_legend(fig, species_req)
    
    # Add Biologic branding
    fig.text(0.99, 0.008, 'Biologic Environmental Survey', 
            ha='right', va='bottom', fontsize=8, style='italic',
            color=BIOLOGIC_COLORS['primary_teal'])
    
    # Add summary statistics box - new format
    summary_text = (
        f"Summary: °C optimal for {stats['pct_optimal_temp']:.0f}% of readings  |  "
        f"RH% optimal for {stats['pct_optimal_rh']:.0f}% of readings  |  "
        f"°C and RH% optimal simultaneously for {stats['pct_optimal_combined']:.0f}% of readings"
    )
    fig.text(0.5, 0.025, summary_text, 
            ha='center', va='bottom', fontsize=9, fontweight='bold',
            color=BIOLOGIC_COLORS['text'],
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                     edgecolor=BIOLOGIC_COLORS['grid'], alpha=0.95))
    
    # Add explanatory note for combined chart
    note_text = (
        "Note: Combined suitability shows the percentage of readings where BOTH temperature AND humidity "
        "were within suitable ranges for roosting. A reading is only considered 'optimal' if both conditions are met simultaneously."
    )
    fig.text(0.5, 0.005, note_text, 
            ha='center', va='bottom', fontsize=7, style='italic',
            color=BIOLOGIC_COLORS['secondary_teal'])
    
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    
    # Save if path provided
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=900, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        print(f"  ✅ Saved: {output_path}")
    
    return fig


def _plot_suitability_panel(
    ax: plt.Axes,
    dates: np.ndarray,
    values: np.ndarray,
    scores: np.ndarray,
    cmap,
    title: str,
    ylabel: str,
    optimal_range: Tuple[float, float],
    value_type: str = 'temp'
):
    """
    Plot a single suitability panel with coloured fill based on suitability.
    """
    import matplotlib.dates as mdates
    
    # Convert dates to matplotlib format
    dates_num = mdates.date2num(pd.to_datetime(dates))
    
    # Create segments for colour-coded fill
    # We'll fill from bottom to the value line, coloured by suitability score
    
    # Plot the filled area with gradient colours - SOLID FILL
    for i in range(len(dates_num) - 1):
        if pd.notna(values[i]) and pd.notna(values[i+1]):
            # Get colour based on average score of segment
            avg_score = (scores[i] + scores[i+1]) / 2 if pd.notna(scores[i]) and pd.notna(scores[i+1]) else 0.5
            color = cmap(avg_score)
            
            # Fill polygon - SOLID (no transparency)
            ax.fill_between(
                [dates_num[i], dates_num[i+1]],
                [0, 0],
                [values[i], values[i+1]],
                color=color,
                alpha=1.0,
                linewidth=0
            )
    
    # Plot the value line on top - COLOURED BY SUITABILITY and THICKER
    for i in range(len(dates_num) - 1):
        if pd.notna(values[i]) and pd.notna(values[i+1]):
            avg_score = (scores[i] + scores[i+1]) / 2 if pd.notna(scores[i]) and pd.notna(scores[i+1]) else 0.5
            line_color = cmap(avg_score)
            ax.plot(
                [dates_num[i], dates_num[i+1]], 
                [values[i], values[i+1]], 
                color=line_color,
                linewidth=2.5,
                solid_capstyle='round'
            )
    
    # Add optimal range reference lines
    ax.axhline(y=optimal_range[0], color=BIOLOGIC_COLORS['green'], 
              linestyle='--', linewidth=1.5, alpha=0.8, label=f'Optimal min ({optimal_range[0]})')
    ax.axhline(y=optimal_range[1], color=BIOLOGIC_COLORS['green'], 
              linestyle='--', linewidth=1.5, alpha=0.8, label=f'Optimal max ({optimal_range[1]})')
    
    # Shade optimal zone lightly
    ax.axhspan(optimal_range[0], optimal_range[1], 
              alpha=0.1, color=BIOLOGIC_COLORS['green'], zorder=0)
    
    # Style the axis
    ax.set_ylabel(ylabel, fontweight='bold', fontsize=10, color=BIOLOGIC_COLORS['text'])
    ax.set_title(title, fontweight='bold', fontsize=11, color=BIOLOGIC_COLORS['primary_teal'], pad=10)
    
    # Set y-axis limits with padding
    y_min = np.nanmin(values) - 2 if np.any(pd.notna(values)) else 0
    y_max = np.nanmax(values) + 2 if np.any(pd.notna(values)) else 100
    ax.set_ylim(max(0, y_min), y_max)
    
    # Format x-axis - SHOW DATES ON ALL CHARTS (abbreviated)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax.tick_params(axis='x', rotation=45, labelsize=7)
    
    # Grid
    ax.grid(True, axis='y', linestyle='--', alpha=0.3, color=BIOLOGIC_COLORS['grid'])
    ax.set_axisbelow(True)
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(BIOLOGIC_COLORS['secondary_teal'])
    ax.spines['bottom'].set_color(BIOLOGIC_COLORS['secondary_teal'])


def _plot_combined_suitability_panel(
    ax: plt.Axes,
    dates: np.ndarray,
    scores: np.ndarray,
    cmap,
    title: str,
    ylabel: str
):
    """
    Plot the combined suitability panel showing the suitability index (0-100).
    Combined score = minimum of temperature and humidity scores.
    This means BOTH conditions must be suitable for the reading to be considered optimal.
    """
    import matplotlib.dates as mdates
    
    # Convert dates to matplotlib format
    dates_num = mdates.date2num(pd.to_datetime(dates))
    
    # Convert scores to percentage (0-100)
    scores_pct = scores * 100
    
    # Create colour-coded fill - SOLID FILL
    for i in range(len(dates_num) - 1):
        if pd.notna(scores[i]) and pd.notna(scores[i+1]):
            avg_score = (scores[i] + scores[i+1]) / 2
            color = cmap(avg_score)
            
            ax.fill_between(
                [dates_num[i], dates_num[i+1]],
                [0, 0],
                [scores_pct[i], scores_pct[i+1]],
                color=color,
                alpha=1.0,
                linewidth=0
            )
    
    # Plot the line on top - COLOURED BY SUITABILITY and THICKER
    for i in range(len(dates_num) - 1):
        if pd.notna(scores[i]) and pd.notna(scores[i+1]):
            avg_score = (scores[i] + scores[i+1]) / 2
            line_color = cmap(avg_score)
            ax.plot(
                [dates_num[i], dates_num[i+1]], 
                [scores_pct[i], scores_pct[i+1]], 
                color=line_color,
                linewidth=2.5,
                solid_capstyle='round'
            )
    
    # Add tier reference lines
    ax.axhline(y=70, color=BIOLOGIC_COLORS['green'], 
              linestyle='--', linewidth=1.5, alpha=0.8, label='Optimal threshold (70%)')
    ax.axhline(y=30, color=SUITABILITY_COLORS['unsuitable'], 
              linestyle='--', linewidth=1.5, alpha=0.8, label='Unsuitable threshold (30%)')
    
    # Shade zones
    ax.axhspan(70, 100, alpha=0.1, color=BIOLOGIC_COLORS['green'], zorder=0)
    ax.axhspan(30, 70, alpha=0.1, color=SUITABILITY_COLORS['marginal'], zorder=0)
    ax.axhspan(0, 30, alpha=0.1, color=SUITABILITY_COLORS['unsuitable'], zorder=0)
    
    # Style the axis - NO SUBTITLE
    ax.set_ylabel(ylabel, fontweight='bold', fontsize=10, color=BIOLOGIC_COLORS['text'])
    ax.set_xlabel('Date', fontweight='bold', fontsize=10, color=BIOLOGIC_COLORS['text'])
    ax.set_title(title, fontweight='bold', fontsize=11, color=BIOLOGIC_COLORS['primary_teal'], pad=10)
    
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 30, 50, 70, 100])
    ax.set_yticklabels(['0%\n(Unsuitable)', '30%', '50%', '70%', '100%\n(Optimal)'])
    
    # Format x-axis - SHOW DATES (abbreviated)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax.tick_params(axis='x', rotation=45, labelsize=7)
    
    # Grid
    ax.grid(True, axis='y', linestyle='--', alpha=0.3, color=BIOLOGIC_COLORS['grid'])
    ax.set_axisbelow(True)
    
    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(BIOLOGIC_COLORS['secondary_teal'])
    ax.spines['bottom'].set_color(BIOLOGIC_COLORS['secondary_teal'])


def _add_suitability_legend(fig: plt.Figure, species_req: Dict):
    """Add a legend explaining the colour coding and thresholds."""
    from matplotlib.patches import Patch
    
    # Create legend elements - SOLID colours (no transparency)
    legend_elements = [
        Patch(facecolor=SUITABILITY_COLORS['optimal'], alpha=1.0, 
              edgecolor='darkgreen', linewidth=2,
              label=f"Optimal: Temp {species_req['temp_min']}-{species_req['temp_max']}°C, RH ≥{species_req['rh_min']}%"),
        Patch(facecolor=SUITABILITY_COLORS['marginal'], alpha=1.0, 
              edgecolor='goldenrod', linewidth=2,
              label='Marginal: Within 15% buffer of optimal range'),
        Patch(facecolor=SUITABILITY_COLORS['unsuitable'], alpha=1.0, 
              edgecolor='darkred', linewidth=2,
              label='Unsuitable: >15% outside optimal range'),
    ]
    
    # Add legend to figure
    fig.legend(handles=legend_elements, 
              loc='upper right', 
              bbox_to_anchor=(0.99, 0.96),
              framealpha=0.95,
              fontsize=9,
              title='Suitability Categories',
              title_fontsize=10)


# =============================================================================
# BATCH GENERATION
# =============================================================================

def generate_all_suitability_charts(
    processed_data: Dict,
    output_dir: Union[str, Path] = '/mnt/user-data/outputs',
    species: str = 'Ghost Bat'
) -> int:
    """
    Generate roosting suitability charts for all continuous monitoring sites.
    
    Parameters
    ----------
    processed_data : Dict
        Dictionary of processed site data
    output_dir : Union[str, Path]
        Directory to save output files
    species : str
        Species to analyse ('Ghost Bat' or 'PLNB')
    
    Returns
    -------
    int
        Number of charts generated
    """
    import os
    
    print(f"\n{'='*70}")
    print(f"GENERATING ROOSTING SUITABILITY CHARTS")
    print(f"{'='*70}")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get continuous monitoring sites
    continuous_sites = [site for site, data in processed_data.items() 
                       if data.get('monitoring_type') == 'continuous']
    
    print(f"Found {len(continuous_sites)} continuous monitoring sites")
    
    generated_count = 0
    
    for site_key in continuous_sites:
        site_data = processed_data[site_key]
        raw_df = site_data.get('full_raw_data', site_data.get('raw_data'))
        
        if raw_df is None or raw_df.empty:
            print(f"Skipping {site_key} - no data")
            continue
        
        cave_name = site_data.get('site_name', site_key.replace('_continuous', ''))
        start_date = site_data.get('start_date')
        end_date = site_data.get('end_date')
        
        if not start_date or not end_date:
            print(f"Skipping {site_key} - no date range")
            continue
        
        # Generate filename
        filename = f"RoostingSuitability_{cave_name.replace(' ', '_')}_{species.replace(' ', '_')}.png"
        filepath = output_dir / filename
        
        try:
            fig = create_suitability_chart(
                raw_df, cave_name, species,
                start_date, end_date, filepath
            )
            if fig:
                generated_count += 1
                plt.close(fig)
        except Exception as e:
            print(f"Error generating {filename}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*70}")
    print(f"✅ Generated {generated_count} roosting suitability charts")
    print(f"{'='*70}\n")
    
    return generated_count


# =============================================================================
# MODULE INFO
# =============================================================================

if __name__ == '__main__':
    print("Roosting Suitability Chart Module")
    print("=" * 45)
    print("\nFeatures:")
    print("  • Three-tier suitability with smooth colour transitions")
    print("  • Three vertically stacked charts (Temp, RH, Combined)")
    print("  • A3 landscape output at 900 DPI")
    print("  • Biologic Environmental Survey styling")
    print("\nUsage:")
    print("  from roosting_suitability_chart import create_suitability_chart")
    print("  fig = create_suitability_chart(raw_df, 'CMRC-13', 'Ghost Bat', start, end, 'output.png')")
