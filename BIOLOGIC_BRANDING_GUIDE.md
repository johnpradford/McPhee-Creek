# McPhee Dashboard - Biologic Branding & PLNB Chart Update
## Implementation Guide - October 2025

## Overview of Updates

This update transforms your dashboard with professional Biologic Environmental Survey branding and adds a new PLNB activity chart for SSM sites.

## New Features

### 1. **Biologic Brand Implementation**
- **Color Palette**: Full Biologic color scheme applied throughout
  - Primary: Dark Teal (#1F4D4D)
  - Secondary: Medium Teal (#577A7A)
  - Light Teal (#9AAFAF)
  - Background Grey (#E4EAEA)
  - Gold Accent (#AFA96E)
  
- **Typography**: Montserrat font family
- **Professional styling** across all elements

### 2. **Logo Updates**
- **Reversed positioning**: Biologic logo on LEFT, HanRoy logo on RIGHT
- **2x larger size**: Increased from 150px to 300px width
- **Optional watermark**: Removable Biologic logo watermark (checkbox in sidebar)

### 3. **PLNB Activity Chart (NEW)**
Recreates the SSM site activity charts with:
- **Logarithmic Y-axis** for handling wide ranges of call counts
- **Date formatting**: DD-MMM-YY on X-axis
- **Biologic gold color** for data points and lines
- **Professional chart styling** matching brand guidelines
- **Site-specific charts** for each SSM location
- **Summary statistics** displayed below each chart

### 4. **Enhanced Continuous Monitoring Charts**
- Updated with Biologic color scheme
- Professional chart borders and styling
- Branded legends and labels
- Biologic footer on all charts

### 5. **Excel Export Branding**
- Biologic colors in table headers
- Professional formatting
- Brand colors throughout
- Biologic footer on each sheet

## Files to Update

Replace these files in your `04_Data` folder:

1. **mcphee_app.py** - Complete Biologic branding and PLNB chart
2. **report_exporter.py** - Excel export with Biologic colors
3. **requirements.txt** - Includes matplotlib dependency
4. **INSTALL_FIRST.bat** - Updated with matplotlib

## Installation Instructions

### Step 1: Install Dependencies
Run the updated INSTALL_FIRST.bat or manually:
```bash
pip install matplotlib --break-system-packages
```

### Step 2: Replace Files
1. Backup your existing files (recommended)
2. Replace `mcphee_app.py` with the new version
3. Replace `report_exporter.py` with the new version

### Step 3: Logo Setup
Ensure your `assets` folder contains:
- `biologic_logo.png` (now displays on LEFT)
- `hanroy_logo.png` (now displays on RIGHT)

## Using the New Features

### Viewing PLNB Activity Charts
1. Navigate to **Visualizations** tab
2. Select **"PLNB Activity Chart (SSM)"** from dropdown
3. Choose an SSM site
4. Chart automatically displays with:
   - Logarithmic scale
   - Date labels (DD-MMM-YY)
   - Biologic gold data points
   - Summary statistics

### Chart Features
- **Auto-scaling**: Y-axis adjusts to data range
- **Log scale**: Handles sites with 1-10,000+ calls
- **Professional styling**: Matches Biologic brand guidelines
- **Export ready**: Charts can be saved/exported

### Continuous Monitoring Charts
Now feature:
- Biologic teal color scheme
- Professional borders
- Branded legends
- Consistent styling

## Visual Changes

### Dashboard Header
- Larger logos (300px width)
- Biologic logo on left
- HanRoy logo on right
- Montserrat font throughout
- Teal color scheme

### Tables
- Teal headers
- Alternating row colors
- Professional borders
- Biologic color scheme

### Charts
- Biologic gold for PLNB activity
- Teal gradient for continuous monitoring
- Professional axes and labels
- Branded footers

## Customization Options

### Watermark Toggle
- Sidebar checkbox: "Show Biologic Logo Watermark"
- Displays semi-transparent logo in bottom-right
- Can be turned on/off as needed

### Color Reference
```python
BIOLOGIC_COLORS = {
    'primary': '#1F4D4D',      # Dark teal
    'secondary': '#577A7A',     # Medium teal
    'light_teal': '#9AAFAF',    # Light teal  
    'lightest': '#C7D3D3',      # Very light teal
    'background': '#E4EAEA',    # Background grey
    'gold': '#AFA96E',          # Gold accent
    'white': '#F6F1E3'          # Off-white
}
```

## Troubleshooting

### Charts not displaying?
- Ensure matplotlib is installed
- Check that data has been loaded
- Verify SSM sites are configured

### Logos not showing?
- Check `assets` folder exists
- Verify logo files are present
- Ensure correct file names

### PLNB chart empty?
- Verify SSM sites have data
- Check date ranges are correct
- Ensure column H contains PLNB call data

## Technical Details

### PLNB Activity Chart
- **Data source**: Column H (plnb_total_calls)
- **Date source**: Column A (date)
- **Scale**: Logarithmic (base 10)
- **Filtering**: By SSM site and date range
- **Zero handling**: Zeros removed for log scale

### Continuous Charts
- **Mean Roost Temp**: Average of columns V-AC
- **Mean Roost RH%**: Average of columns AD-AK
- **Total Rainfall**: Column S
- **Ambient Temp**: Average of columns Q-R
- **Ambient RH%**: Average of columns T-U

## Benefits of Updates

1. **Professional appearance** matching Biologic brand standards
2. **Better data visualization** with logarithmic scaling
3. **Consistent branding** across all outputs
4. **Enhanced readability** with proper typography
5. **Export-ready** charts and reports
6. **Client-ready** presentations

## Support

For issues or questions:
1. Check this implementation guide
2. Verify all files are updated
3. Ensure matplotlib is installed
4. Check data format matches specifications

The dashboard now presents a fully professional, branded interface consistent with Biologic Environmental Survey's visual identity standards.
