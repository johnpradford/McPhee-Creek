"""
McPhee Wildlife Monitoring Dashboard - Main Application
Biologic Environmental Survey 2025
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from pathlib import Path
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MultipleLocator
import base64
from openpyxl.styles import Font

# Import custom modules
from data_loader import DataLoader
from data_processor import DataProcessor
from table_generator import TableGenerator
from report_exporter import ReportExporter
from microclimate_stacked_chart import MicroclimateStackedChart
from microclimate_dual_axis_chart import MicroclimateDualAxisChart
from roosting_suitability_chart import create_suitability_chart, SPECIES_RANGES

# Page configuration
st.set_page_config(
    page_title="McPhee Wildlife Monitoring Dashboard",
    page_icon="🦇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Biologic Brand Colors from the guide
BIOLOGIC_COLORS = {
    'primary': '#1F4D4D',      # Dark teal
    'secondary': '#577A7A',     # Medium teal
    'light_teal': '#9AAFAF',   # Light teal  
    'lightest': '#C7D3D3',     # Very light teal
    'background': '#E4EAEA',   # Background grey
    'gold': '#AFA96E',         # Gold accent (from 5845 C)
    'white': '#F6F1E3'         # Off-white
}

# Function to load and encode logo
def get_base64_logo(logo_path):
    """Convert logo to base64 for embedding"""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# Custom CSS with Biologic branding
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');
    
    /* Global font */
    html, body, [class*="css"] {{
        font-family: 'Montserrat', sans-serif;
    }}
    
    /* Main header */
    .main-header {{
        font-size: 2.8rem;
        font-weight: 700;
        color: {BIOLOGIC_COLORS['primary']};
        text-align: center;
        margin-bottom: 0.5rem;
        margin-top: 0;
        font-family: 'Montserrat', sans-serif;
    }}
    
    /* Sub header */
    .sub-header {{
        text-align: center;
        color: {BIOLOGIC_COLORS['secondary']};
        margin-bottom: 1rem;
        font-size: 1.2rem;
        font-weight: 400;
    }}
    
    /* Metric cards */
    .metric-card {{
        background-color: {BIOLOGIC_COLORS['background']};
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        border: 1px solid {BIOLOGIC_COLORS['lightest']};
    }}
    
    /* Sidebar styling */
    .css-1d391kg {{
        background-color: {BIOLOGIC_COLORS['background']};
    }}
    
    /* Buttons */
    .stButton > button {{
        background-color: {BIOLOGIC_COLORS['primary']};
        color: white;
        border: none;
        font-weight: 600;
    }}
    
    .stButton > button:hover {{
        background-color: {BIOLOGIC_COLORS['secondary']};
    }}
    
    /* Selectbox and other inputs */
    .stSelectbox > div > div {{
        background-color: white;
        border-color: {BIOLOGIC_COLORS['light_teal']};
    }}
    
    /* Headers */
    h1, h2, h3 {{
        color: {BIOLOGIC_COLORS['primary']};
        font-family: 'Montserrat', sans-serif;
    }}
    
    /* Alert messages */
    .stAlert {{
        background-color: {BIOLOGIC_COLORS['background']};
        border-left: 4px solid {BIOLOGIC_COLORS['gold']};
    }}
    
    /* Tables */
    .dataframe {{
        font-family: 'Montserrat', sans-serif;
    }}
    
    .dataframe thead tr {{
        background-color: {BIOLOGIC_COLORS['primary']} !important;
        color: white !important;
    }}
    
    .dataframe tbody tr:nth-child(even) {{
        background-color: {BIOLOGIC_COLORS['background']};
    }}
    
    /* Logo container styling */
    .logo-container {{
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1rem;
    }}
    
    /* Biologic watermark */
    .biologic-watermark {{
        position: fixed;
        bottom: 10px;
        right: 10px;
        opacity: 0.3;
        z-index: 1000;
    }}
</style>
""", unsafe_allow_html=True)

# Constants
DEFAULT_DATA_PATH = r"W:\2024 2025\24242 HanRoy McPhee Creek Significant Species Monitoring 2025\04_Data"
DEFAULT_FILE = r"23108 HanRoy McPhee Creek Microclimate and Ultrasonic Master Data_V0.2 JR_clean.xlsx"
CONFIG_FILE = "config/dashboard_config.json"

# Initialize session state
def init_session_state():
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'tables_generated' not in st.session_state:
        st.session_state.tables_generated = False
    if 'site_data' not in st.session_state:
        st.session_state.site_data = {}
    if 'config' not in st.session_state:
        st.session_state.config = load_saved_config()

def load_saved_config():
    """Load previously saved configuration"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"Could not load saved config: {e}")
    return {}

def save_config(config):
    """Save configuration for next session"""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2, default=str)
    except Exception as e:
        st.warning(f"Could not save config: {e}")

# Initialize
init_session_state()

# Logo section - create three columns for logos and title
logo_col1, title_col, logo_col2 = st.columns([1.5, 3, 1.5])

with logo_col1:
    # Biologic logo (now on LEFT)
    try:
        if os.path.exists('assets/biologic_logo.png'):
            st.image('assets/biologic_logo.png', width=300)  # Doubled from 150
        else:
            st.write("")  # Empty space if logo not found
    except:
        st.write("")

with title_col:
    # Header with Biologic branding
    st.markdown('<p class="main-header">🦇 McPhee Wildlife Monitoring Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">HanRoy McPhee Creek Significant Species Monitoring 2025</p>', unsafe_allow_html=True)

with logo_col2:
    # HanRoy logo (now on RIGHT)
    try:
        if os.path.exists('assets/hanroy_logo.png'):
            st.image('assets/hanroy_logo.png', width=300)  # Doubled from 150
        else:
            st.write("")  # Empty space if logo not found
    except:
        st.write("")

st.markdown("---")

# Add removable Biologic watermark
if st.sidebar.checkbox("Show Biologic Logo Watermark", value=True):
    biologic_logo_base64 = get_base64_logo('assets/biologic_logo.png')
    if biologic_logo_base64:
        st.markdown(f"""
        <div class="biologic-watermark">
            <img src="data:image/png;base64,{biologic_logo_base64}" width="100">
        </div>
        """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📁 Data Configuration")
    
    # Data source selection
    data_source = st.radio(
        "Select data source:",
        ["Use default path", "Upload file"],
        help="Choose whether to use the default file location or upload a file"
    )
    
    if data_source == "Use default path":
        # Check if default file exists
        default_full_path = os.path.join(DEFAULT_DATA_PATH, DEFAULT_FILE)
        
        if os.path.exists(default_full_path):
            st.success(f"✅ Found: {DEFAULT_FILE}")
            
            if st.button("📂 Load Default File", type="primary"):
                with st.spinner("Loading data..."):
                    try:
                        loader = DataLoader(default_full_path)
                        st.session_state.loader = loader
                        st.session_state.sheet_names = loader.get_sheet_names()
                        st.session_state.data_loaded = True
                        st.success(f"✅ Loaded {len(st.session_state.sheet_names)} sheets")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error loading file: {str(e)}")
        else:
            st.warning(f"⚠️ Default file not found at:\n{default_full_path}")
            st.info("Please ensure the file exists or use 'Upload file' option")
    
    else:
        # File upload
        uploaded_file = st.file_uploader(
            "Upload Raw Data Excel",
            type=['xlsx', 'xls'],
            help="Upload: McPhee Creek Microclimate and Ultrasonic Master Data"
        )
        
        if uploaded_file is not None:
            with st.spinner("Loading uploaded file..."):
                try:
                    loader = DataLoader(uploaded_file)
                    st.session_state.loader = loader
                    st.session_state.sheet_names = loader.get_sheet_names()
                    st.session_state.data_loaded = True
                    st.success(f"✅ Loaded {len(st.session_state.sheet_names)} sheets")
                except Exception as e:
                    st.error(f"Error loading file: {str(e)}")
    
    st.markdown("---")
    
    # Quick stats
    if st.session_state.data_loaded:
        st.metric("Worksheets Found", len(st.session_state.sheet_names))
        
        # Show available sites
        with st.expander("📋 Available Sites"):
            for sheet in st.session_state.sheet_names:
                st.caption(f"• {sheet}")

# Main content
if st.session_state.data_loaded:
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 Configuration", 
        "📊 Generated Tables", 
        "📈 Visualizations",
        "🔍 Audit Reports"
    ])
    
    # TAB 1: Configuration
    with tab1:
        st.header("Monitoring Configuration")
        
        # Monitoring type selection
        monitoring_type = st.radio(
            "Select monitoring type to configure:",
            ["Continuous Monitoring", "Short-term (SSM)", "Both"],
            horizontal=True,
            help="Choose which type of monitoring to analyze"
        )
        
        st.markdown("---")
        
        # Configuration columns
        col1, col2 = st.columns(2)
        
        # CONTINUOUS MONITORING
        if monitoring_type in ["Continuous Monitoring", "Both"]:
            with col1:
                st.subheader("🔄 Continuous Monitoring Sites")
                st.info("Sites with continuous data collection over extended periods")
                
                # Available continuous sites (these are the ones that typically run continuously)
                continuous_sites = []
                for sheet in st.session_state.sheet_names:
                    # Add CMPC sites that are typically continuous
                    if any(site in sheet for site in ['CMPC-03', 'CMPC-08', 'CMPC-10', 'CMPC-25']):
                        continuous_sites.append(sheet)
                
                # Load saved selections
                saved_continuous = st.session_state.config.get('continuous_sites', continuous_sites)
                
                selected_continuous = st.multiselect(
                    "Select continuous sites:",
                    continuous_sites,
                    default=saved_continuous,
                    key="continuous_sites_select"
                )
                
                st.markdown("**Shared Date Range for All Continuous Sites:**")
                cont_col1, cont_col2 = st.columns(2)
                
                # Load saved dates
                saved_cont_start = st.session_state.config.get('continuous_start', '2023-09-21')
                saved_cont_end = st.session_state.config.get('continuous_end', '2024-06-04')
                
                with cont_col1:
                    cont_start = st.date_input(
                        "Start Date",
                        value=pd.to_datetime(saved_cont_start).date(),
                        key="cont_start"
                    )
                with cont_col2:
                    cont_end = st.date_input(
                        "End Date",
                        value=pd.to_datetime(saved_cont_end).date(),
                        key="cont_end"
                    )
                
                if selected_continuous:
                    days = (cont_end - cont_start).days + 1
                    st.success(f"✅ {len(selected_continuous)} sites × {days} days")
                    st.caption(f"Period: {cont_start.strftime('%d-%b-%y')} to {cont_end.strftime('%d-%b-%y')}")
        
        # SSM MONITORING
        if monitoring_type in ["Short-term (SSM)", "Both"]:
            with col2 if monitoring_type == "Both" else col1:
                st.subheader("📍 Short-term (SSM) Sites")
                st.info("Sites with discrete monitoring periods (typically 7-night deployments)")
                
                # All available sites from sheets
                all_possible_ssm = [s for s in st.session_state.sheet_names 
                                   if s.startswith(('CMPC-', 'WMPC-'))]
                
                # Load saved SSM selections
                saved_ssm = st.session_state.config.get('ssm_sites', {})
                saved_ssm_names = list(saved_ssm.keys()) if saved_ssm else ["CMPC-03", "CMPC-08", "CMPC-10"]
                
                selected_ssm = st.multiselect(
                    "Select SSM sites:",
                    all_possible_ssm,
                    default=[s for s in saved_ssm_names if s in all_possible_ssm],
                    key="ssm_sites_select"
                )
                
                if selected_ssm:
                    st.markdown("**Configure date ranges for each SSM site:**")
                    
                    # Store SSM dates
                    ssm_dates = {}
                    
                    with st.expander("📅 Individual Site Date Ranges", expanded=True):
                        for site in selected_ssm:
                            st.markdown(f"**{site}**")
                            site_col1, site_col2 = st.columns(2)
                            
                            # Load saved dates for this site
                            saved_site_data = saved_ssm.get(site, {})
                            default_start = saved_site_data.get('start', '2024-06-10')
                            default_end = saved_site_data.get('end', '2024-06-16')
                            
                            with site_col1:
                                start = st.date_input(
                                    "Start",
                                    value=pd.to_datetime(default_start).date(),
                                    key=f"{site}_ssm_start"
                                )
                            with site_col2:
                                end = st.date_input(
                                    "End",
                                    value=pd.to_datetime(default_end).date(),
                                    key=f"{site}_ssm_end"
                                )
                            
                            ssm_dates[site] = {
                                'start': start,
                                'end': end,
                                'days': (end - start).days + 1
                            }
                            
                            st.caption(f"↳ {(end - start).days + 1} days: {start.strftime('%d-%b-%y')} to {end.strftime('%d-%b-%y')}")
                    
                    total_ssm_days = sum(d['days'] for d in ssm_dates.values())
                    st.success(f"✅ {len(selected_ssm)} sites configured ({total_ssm_days} total sampling days)")
                    
                    # Store in session state
                    st.session_state.ssm_dates = ssm_dates
        
        # Generate button
        st.markdown("---")
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        
        with col_btn2:
            can_generate = False
            
            if monitoring_type == "Continuous Monitoring":
                can_generate = len(selected_continuous) > 0
            elif monitoring_type == "Short-term (SSM)":
                can_generate = len(selected_ssm) > 0
            else:  # Both
                can_generate = len(selected_continuous) > 0 or len(selected_ssm) > 0
            
            if st.button("🚀 Generate All Tables", 
                        type="primary", 
                        width="stretch",
                        disabled=not can_generate):
                
                with st.spinner("Processing data and generating tables..."):
                    try:
                        # Save configuration
                        config = {
                            'continuous_sites': selected_continuous if monitoring_type in ["Continuous Monitoring", "Both"] else [],
                            'continuous_start': str(cont_start) if monitoring_type in ["Continuous Monitoring", "Both"] else None,
                            'continuous_end': str(cont_end) if monitoring_type in ["Continuous Monitoring", "Both"] else None,
                            'ssm_sites': {site: {'start': str(data['start']), 'end': str(data['end'])} 
                                        for site, data in ssm_dates.items()} if monitoring_type in ["Short-term (SSM)", "Both"] else {},
                            'monitoring_type': monitoring_type
                        }
                        
                        save_config(config)
                        st.session_state.config = config
                        
                        # Initialize processor
                        processor = DataProcessor(st.session_state.loader)
                        
                        # Load and process data
                        processed_data = {}
                        
                        # Process continuous sites
                        if monitoring_type in ["Continuous Monitoring", "Both"] and selected_continuous:
                            for site in selected_continuous:
                                # Use composite key to avoid overwriting
                                site_key = f"{site}_continuous"
                                site_data = processor.process_site(
                                    site, 
                                    cont_start, 
                                    cont_end,
                                    monitoring_type="continuous"
                                )
                                processed_data[site_key] = site_data
                        
                        # Process SSM sites
                        if monitoring_type in ["Short-term (SSM)", "Both"] and selected_ssm:
                            for site in selected_ssm:
                                if site in ssm_dates:
                                    # Use composite key for SSM
                                    site_key = f"{site}_ssm"
                                    site_data = processor.process_site(
                                        site,
                                        ssm_dates[site]['start'],
                                        ssm_dates[site]['end'],
                                        monitoring_type="ssm"
                                    )
                                    processed_data[site_key] = site_data
                        
                        st.session_state.processed_data = processed_data
                        
                        # Create master data for bat activity statements
                        master_data_df = processor.create_master_data_for_statements(processed_data)
                        st.session_state.master_data_df = master_data_df
                        
                        # Generate tables
                        table_gen = TableGenerator(processed_data, config)
                        tables = table_gen.generate_all_tables()
                        
                        st.session_state.tables = tables
                        st.session_state.tables_generated = True
                        
                        # Generate audit reports
                        st.session_state.audit_reports = processor.generate_audit_reports(processed_data, config)
                        
                        st.success(f"✅ Successfully generated {len(tables)} tables!")
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"Error generating tables: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
            
            if not can_generate:
                st.warning("⚠️ Please select at least one site to generate tables")
    
    # TAB 2: Generated Tables
    with tab2:
        st.header("Generated Tables")
        
        if st.session_state.tables_generated:
            
            tables = st.session_state.tables
            
            # Table selector with descriptions
            table_options = {
                "Table 2.1 - Climate Summary (SSM)": "2.1",
                "Table 3.2 - Temperature Data (SSM)": "3.2",
                "Table 3.3 - Relative Humidity (SSM)": "3.3",
                "Table 3.4 - Temperature Summary (Continuous)": "3.4",
                "Table 3.5 - Relative Humidity (Continuous)": "3.5",
                "Table 3.6 - PLNB Activity Summary": "3.6",
                "Table 3.7 - PLNB Timing": "3.7",
                "Table 3.8 - Ghost Bat Records Matrix": "3.8",
                "Table 3.9 - Monthly Temperature (SSM)": "3.9",
                "Table 3.10 - Monthly Humidity (SSM)": "3.10",
                "Table 3.11 - Monthly Temperature (Continuous)": "3.11",
                "Table 3.12 - Monthly Humidity (Continuous)": "3.12",
                "Table 3.13 - Roosting Evidence": "3.13",
                "Table 3.14 - Ghost Bat Call Range": "3.14"
            }
            
            # Filter available tables
            available_tables = {k: v for k, v in table_options.items() if v in tables}
            
            if not available_tables:
                st.warning("No tables were generated. Please check your configuration.")
            else:
                selected_table_name = st.selectbox(
                    "Select table to view:",
                    options=list(available_tables.keys()),
                    key="table_selector"
                )
                
                table_id = available_tables[selected_table_name]
                table_data = tables[table_id]
                
                st.markdown("---")
                
                # Display table
                st.subheader(table_data['title'])
                
                if table_data.get('notes'):
                    st.caption(table_data['notes'][0])
                
                df = table_data['dataframe']
                
                # Special formatting for certain tables
                if table_id == "3.8":
                    # Ghost bat matrix - apply color coding
                    st.dataframe(df, width="stretch", hide_index=True, height=400)
                    st.info("🦇 R = Roosting indicated | C = Calls recorded | NC = No calls | - = No sampling")
                else:
                    st.dataframe(df, width="stretch", hide_index=True, height=400)
                
                # Table statistics
                if not df.empty:
                    st.caption(f"📊 {len(df)} rows × {len(df.columns)} columns")
        else:
            st.info("👈 Configure dates and click **Generate All Tables** in the Configuration tab")
            
            st.markdown("### 📋 Available Tables")
            st.markdown("""
            Once generated, you'll be able to view:
            - **Table 2.1**: Daily climate data (temperature, rainfall, humidity, moon phase)
            - **Tables 3.2-3.5**: Temperature and humidity summaries (SSM and Continuous)
            - **Tables 3.6-3.7**: Pilbara Leaf-Nosed Bat activity and timing
            - **Table 3.8**: Ghost Bat ultrasonic records matrix
            - **Tables 3.9-3.12**: Monthly climate summaries
            - **Tables 3.13-3.14**: Ghost Bat roosting and call patterns
            """)
    
    # TAB 3: Visualizations
    with tab3:
        st.header("Data Visualizations")
        
        if st.session_state.tables_generated:
            
            viz_type = st.selectbox(
                "Select visualization:",
                [
                    "PLNB Activity Chart (SSM)",
                    "Continuous Monitoring Charts (Figures 3.1-3.4)",
                    "PLNB Activity by Site",
                    "Temperature Comparison",
                    "Humidity Comparison", 
                    "Ghost Bat Activity Heatmap",
                    "Monthly Call Trends",
                    "Microclimate Stacked Charts (Time Series)",
                    "Roosting Suitability Time Series"
                ]
            )
            
            st.markdown("---")
            
            processed_data = st.session_state.processed_data
            
            if viz_type == "PLNB Activity Chart (SSM)":
                st.subheader("PLNB Call Activity by Recording Night (SSM Sites)")
                
                # Get SSM sites from processed data
                ssm_sites = [site for site, data in processed_data.items() 
                            if data.get('monitoring_type') == 'ssm']
                
                if ssm_sites:
                    # Allow user to select specific SSM site
                    selected_site = st.selectbox(
                        "Select SSM Site:",
                        ssm_sites,
                        format_func=lambda x: x.replace('_ssm', '')
                    )
                    
                    if selected_site:
                        site_data = processed_data[selected_site]
                        df = site_data.get('raw_data', pd.DataFrame())
                        
                        if not df.empty:
                            try:
                                # Get date and PLNB total calls columns
                                date_col = df.columns[0]  # Column A
                                plnb_calls_col = 7  # Column H (plnb_total_calls)
                                
                                # Prepare data
                                chart_data = pd.DataFrame()
                                chart_data['Date'] = pd.to_datetime(df[date_col], errors='coerce')
                                
                                if plnb_calls_col < len(df.columns):
                                    chart_data['PLNB_Calls'] = pd.to_numeric(df.iloc[:, plnb_calls_col], errors='coerce')
                                    
                                    # Remove NaN values and zeros for log scale
                                    chart_data = chart_data.dropna(subset=['Date', 'PLNB_Calls'])
                                    chart_data = chart_data[chart_data['PLNB_Calls'] > 0]
                                    chart_data = chart_data.sort_values('Date')
                                    
                                    # Create the chart with Biologic styling (even if no data)
                                    fig, ax = plt.subplots(figsize=(12, 6))
                                    
                                    # Set background color
                                    fig.patch.set_facecolor('white')
                                    ax.set_facecolor('white')
                                    
                                    if len(chart_data) > 0:
                                        # Plot with Biologic gold color
                                        ax.plot(chart_data['Date'], chart_data['PLNB_Calls'], 
                                               marker='o', markersize=8, 
                                               color=BIOLOGIC_COLORS['gold'], 
                                               markerfacecolor=BIOLOGIC_COLORS['gold'],
                                               markeredgecolor=BIOLOGIC_COLORS['primary'],
                                               markeredgewidth=1.5,
                                               linewidth=2,
                                               label='Chart Area')
                                    else:
                                        # Show empty chart with note
                                        ax.text(0.5, 0.5, 'No calls recorded', 
                                               ha='center', va='center', 
                                               transform=ax.transAxes,
                                               fontsize=12, color=BIOLOGIC_COLORS['secondary'],
                                               alpha=0.7)
                                    
                                    # Set logarithmic y-axis
                                    ax.set_yscale('log')
                                    
                                    # Format x-axis
                                    if len(chart_data) > 0:
                                        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b-%y'))
                                        ax.set_xticks(chart_data['Date'])
                                        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
                                    else:
                                        # For empty chart, show date range from config
                                        ax.set_xlim(pd.Timestamp(site_data['start_date']), 
                                                   pd.Timestamp(site_data['end_date']))
                                        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b-%y'))
                                        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
                                        
                                        # Styling
                                        ax.set_xlabel('Recording night', fontsize=11, fontweight='600', 
                                                    color=BIOLOGIC_COLORS['primary'])
                                        ax.set_ylabel('Number of (log) calls', fontsize=11, fontweight='600',
                                                    color=BIOLOGIC_COLORS['primary'])
                                        ax.set_title(selected_site.replace('_ssm', '').upper(), 
                                                   fontsize=14, fontweight='700',
                                                   color=BIOLOGIC_COLORS['primary'])
                                        
                                        # Grid styling
                                        ax.grid(True, which='major', axis='y', alpha=0.3, 
                                               color=BIOLOGIC_COLORS['light_teal'])
                                        ax.grid(True, which='minor', axis='y', alpha=0.1,
                                               color=BIOLOGIC_COLORS['lightest'])
                                        
                                        # Box styling to match example
                                        for spine in ax.spines.values():
                                            spine.set_edgecolor(BIOLOGIC_COLORS['primary'])
                                            spine.set_linewidth(1.5)
                                        
                                        # Legend
                                        ax.legend(loc='upper left', frameon=True, 
                                                facecolor='white', edgecolor=BIOLOGIC_COLORS['primary'])
                                        
                                        # Set y-axis limits based on data range with validation
                                        if len(chart_data) > 0 and chart_data['PLNB_Calls'].notna().any():
                                            y_min = max(1, chart_data['PLNB_Calls'].min() * 0.5)
                                            y_max = chart_data['PLNB_Calls'].max() * 2
                                            
                                            # Validate that limits are valid numbers
                                            if pd.isna(y_min) or pd.isna(y_max) or np.isinf(y_min) or np.isinf(y_max):
                                                # Use default range if data is invalid
                                                y_min, y_max = 1, 1000
                                            
                                            ax.set_ylim(y_min, y_max)
                                        else:
                                            # Default range if no data
                                            ax.set_ylim(1, 1000)
                                        
                                        # Add Biologic branding
                                        fig.text(0.99, 0.01, 'Biologic Environmental Survey', 
                                                fontsize=8, ha='right', 
                                                color=BIOLOGIC_COLORS['secondary'], alpha=0.7)
                                        
                                        plt.tight_layout()
                                        st.pyplot(fig)
                                        plt.close()
                                        
                                        # Show summary statistics
                                        col1, col2, col3, col4 = st.columns(4)
                                        with col1:
                                            st.metric("Total Nights", len(chart_data) if len(chart_data) > 0 else 0)
                                        with col2:
                                            st.metric("Max Calls", int(chart_data['PLNB_Calls'].max()) if len(chart_data) > 0 else 0)
                                        with col3:
                                            st.metric("Min Calls", int(chart_data['PLNB_Calls'].min()) if len(chart_data) > 0 else 0)
                                        with col4:
                                            st.metric("Avg Calls", int(chart_data['PLNB_Calls'].mean()) if len(chart_data) > 0 else 0)
                                else:
                                    st.warning("PLNB call data column not found in the dataset")
                            except Exception as e:
                                st.error(f"Error generating PLNB chart: {str(e)}")
                                st.info("Please check that your data contains valid PLNB call counts in column H")
                        else:
                            st.warning(f"No data available for {selected_site}")
                else:
                    st.info("No SSM sites found. Please configure SSM sites in the Configuration tab.")
            
            elif viz_type == "Continuous Monitoring Charts (Figures 3.1-3.4)":
                st.subheader("Continuous Ambient and Roost Microclimate Comparison")
                
                # Get continuous sites from config
                continuous_sites = st.session_state.config.get('continuous_sites', [])
                
                if continuous_sites:
                    # Create a figure for each continuous site
                    for idx, site in enumerate(continuous_sites, 1):
                        site_key = f"{site}_continuous"
                        
                        if site_key in processed_data:
                            site_data = processed_data[site_key]
                            df = site_data.get('raw_data', pd.DataFrame())
                            
                            if not df.empty:
                                # Prepare data for plotting
                                plot_df = pd.DataFrame()
                                
                                # Get date column
                                date_col = df.columns[0]
                                plot_df['Date'] = pd.to_datetime(df[date_col])
                                
                                # Calculate Mean Roost Temp (columns V-AC, indices 21-28)
                                roost_temp_cols = [21, 22, 23, 24, 25, 26, 27, 28]
                                roost_temps = []
                                for col_idx in roost_temp_cols:
                                    if col_idx < len(df.columns):
                                        roost_temps.append(pd.to_numeric(df.iloc[:, col_idx], errors='coerce'))
                                if roost_temps:
                                    plot_df['Mean Roost Temp (°C)'] = pd.concat(roost_temps, axis=1).mean(axis=1)
                                
                                # Calculate Mean Roost RH% (columns AD-AK, indices 29-36)
                                roost_rh_cols = [29, 30, 31, 32, 33, 34, 35, 36]
                                roost_rhs = []
                                for col_idx in roost_rh_cols:
                                    if col_idx < len(df.columns):
                                        roost_rhs.append(pd.to_numeric(df.iloc[:, col_idx], errors='coerce'))
                                if roost_rhs:
                                    plot_df['Mean Roost RH%'] = pd.concat(roost_rhs, axis=1).mean(axis=1)
                                
                                # Get Total Rainfall (column S, index 18)
                                if 18 < len(df.columns):
                                    plot_df['Total Rainfall'] = pd.to_numeric(df.iloc[:, 18], errors='coerce')
                                
                                # Calculate Ambient Temp (columns Q-R, indices 16-17)
                                ambient_temp_cols = [16, 17]
                                ambient_temps = []
                                for col_idx in ambient_temp_cols:
                                    if col_idx < len(df.columns):
                                        ambient_temps.append(pd.to_numeric(df.iloc[:, col_idx], errors='coerce'))
                                if ambient_temps:
                                    plot_df['Ambient Temp (°C)'] = pd.concat(ambient_temps, axis=1).mean(axis=1)
                                
                                # Calculate Ambient RH% (columns T-U, indices 19-20)
                                ambient_rh_cols = [19, 20]
                                ambient_rhs = []
                                for col_idx in ambient_rh_cols:
                                    if col_idx < len(df.columns):
                                        ambient_rhs.append(pd.to_numeric(df.iloc[:, col_idx], errors='coerce'))
                                if ambient_rhs:
                                    plot_df['Ambient RH%'] = pd.concat(ambient_rhs, axis=1).mean(axis=1)
                                
                                # Sort by date and remove NaN dates
                                plot_df = plot_df.dropna(subset=['Date'])
                                plot_df = plot_df.sort_values('Date')
                                
                                # Create the chart with Biologic branding
                                fig, ax = plt.subplots(figsize=(14, 6))
                                
                                # Set background color
                                fig.patch.set_facecolor('white')
                                ax.set_facecolor('white')
                                
                                # Plot lines with Biologic color scheme
                                if 'Mean Roost Temp (°C)' in plot_df.columns:
                                    ax.plot(plot_df['Date'], plot_df['Mean Roost Temp (°C)'], 
                                           label='Mean Roost Temp (°C)', 
                                           color=BIOLOGIC_COLORS['primary'], linewidth=1.5)
                                
                                if 'Mean Roost RH%' in plot_df.columns:
                                    ax.plot(plot_df['Date'], plot_df['Mean Roost RH%'], 
                                           label='Mean Roost RH%', 
                                           color=BIOLOGIC_COLORS['secondary'], linewidth=1.5)
                                
                                if 'Total Rainfall' in plot_df.columns:
                                    ax.plot(plot_df['Date'], plot_df['Total Rainfall'], 
                                           label='Total Rainfall', 
                                           color='#E31C79', linewidth=1.5)  # Using a bright accent color
                                
                                if 'Ambient Temp (°C)' in plot_df.columns:
                                    ax.plot(plot_df['Date'], plot_df['Ambient Temp (°C)'], 
                                           label='Ambient Temp (°C)', 
                                           color='#333333', linewidth=1.5)
                                
                                if 'Ambient RH%' in plot_df.columns:
                                    ax.plot(plot_df['Date'], plot_df['Ambient RH%'], 
                                           label='Ambient RH%', 
                                           color=BIOLOGIC_COLORS['light_teal'], linewidth=1.5)
                                
                                # Format x-axis
                                ax.xaxis.set_major_formatter(mdates.DateFormatter('%b/%Y'))
                                ax.xaxis.set_major_locator(mdates.MonthLocator())
                                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', 
                                        fontsize=9, color=BIOLOGIC_COLORS['secondary'])
                                
                                # Format y-axis
                                ax.set_ylim(0, 110)
                                ax.yaxis.set_major_locator(MultipleLocator(10))
                                ax.grid(True, axis='y', alpha=0.3, color=BIOLOGIC_COLORS['lightest'])
                                
                                # Labels and title with Biologic styling
                                ax.set_xlabel('', fontsize=11, fontweight='600', 
                                            color=BIOLOGIC_COLORS['primary'])
                                ax.set_ylabel('', fontsize=11, fontweight='600',
                                            color=BIOLOGIC_COLORS['primary'])
                                ax.set_title(f'Figure 3.{idx}: Continuous ambient and roost microclimate comparison for {site}',
                                           fontsize=12, fontweight='700', color=BIOLOGIC_COLORS['primary'])
                                
                                # Box styling with Biologic colors
                                for spine in ax.spines.values():
                                    spine.set_edgecolor(BIOLOGIC_COLORS['primary'])
                                    spine.set_linewidth(1.5)
                                
                                # Legend with Biologic styling
                                ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), 
                                         ncol=5, frameon=True, fontsize=9,
                                         facecolor='white', edgecolor=BIOLOGIC_COLORS['primary'])
                                
                                # Add Biologic branding
                                fig.text(0.99, 0.01, 'Biologic Environmental Survey', 
                                        fontsize=8, ha='right', 
                                        color=BIOLOGIC_COLORS['secondary'], alpha=0.7)
                                
                                # Tight layout
                                plt.tight_layout()
                                
                                # Display the chart
                                st.pyplot(fig)
                                plt.close()
                                
                                # Add spacing between charts
                                if idx < len(continuous_sites):
                                    st.markdown("---")
                            else:
                                st.warning(f"No data available for {site}")
                        else:
                            st.warning(f"Site {site} not found in processed data")
                else:
                    st.info("No continuous monitoring sites selected. Please configure continuous sites in the Configuration tab.")
            
            elif viz_type == "PLNB Activity by Site":
                st.subheader("Average PLNB Calls per Night by Site")
                
                # Extract PLNB data
                if '3.6' in st.session_state.tables:
                    df = st.session_state.tables['3.6']['dataframe']
                    
                    if not df.empty and 'Average' in df.columns:
                        chart_df = df[['Cave ID', 'Average', 'Category']].copy()
                        chart_df = chart_df.sort_values('Average', ascending=True)
                        
                        st.bar_chart(chart_df.set_index('Cave ID')['Average'], height=400)
                        
                        # Summary stats
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Highest Activity", 
                                   f"{chart_df['Cave ID'].iloc[-1]}", 
                                   f"{chart_df['Average'].iloc[-1]:.1f} calls/night")
                        col2.metric("Lowest Activity", 
                                   f"{chart_df['Cave ID'].iloc[0]}", 
                                   f"{chart_df['Average'].iloc[0]:.1f} calls/night")
                        col3.metric("Mean Activity", 
                                   f"{chart_df['Average'].mean():.1f} calls/night")
                else:
                    st.info("Generate tables first to view this visualization")
            
            elif viz_type == "Temperature Comparison":
                st.subheader("Day vs Night Temperature by Site")
                
                if '3.2' in st.session_state.tables:
                    df = st.session_state.tables['3.2']['dataframe']
                    st.bar_chart(df.set_index('Caves')[['Day Min (°C)', 'Day Max (°C)']], height=400)
                else:
                    st.info("Generate SSM tables first to view this visualization")
            
            elif viz_type == "Microclimate Stacked Charts (Time Series)":
                st.subheader("Microclimate Suitability Over Time")
                
                # Get continuous sites
                continuous_sites = st.session_state.config.get('continuous_sites', [])
                
                if continuous_sites:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        selected_cave = st.selectbox(
                            "Select Cave:",
                            continuous_sites,
                            key="stacked_cave_select"
                        )
                    
                    with col2:
                        selected_species = st.selectbox(
                            "Select Species:",
                            ["Ghost Bat", "PLNB"],
                            key="stacked_species_select"
                        )
                    
                    if st.button("Generate Stacked Chart", key="gen_stacked"):
                        with st.spinner(f"Generating stacked chart for {selected_cave} - {selected_species}..."):
                            try:
                                # Get the site data
                                site_key = f"{selected_cave}_continuous"
                                if site_key in processed_data:
                                    site_data = processed_data[site_key]
                                    raw_df = site_data.get('raw_data', pd.DataFrame())
                                    
                                    if not raw_df.empty:
                                        # Chart type selector
                                        chart_type = st.radio(
                                            "Select Chart Type:",
                                            ["Stacked Area Charts", "Dual-Axis Line Chart"],
                                            help="Stacked charts show proportion of time in each category. Dual-axis shows actual temp/humidity values together."
                                        )
                                        
                                        # ===== STACKED AREA CHARTS =====
                                        if chart_type == "Stacked Area Charts":
                                            # Create stacked chart generator
                                            stacked_gen = MicroclimateStackedChart()
                                            
                                            # Generate chart
                                            fig = stacked_gen.generate_stacked_chart(
                                                raw_df=raw_df,
                                                cave_name=selected_cave,
                                                species=selected_species,
                                                start_date=site_data['start_date'],
                                                end_date=site_data['end_date'],
                                                output_path=None
                                            )
                                            
                                            if fig:
                                                # Display the figure
                                                st.pyplot(fig)
                                                plt.close(fig)
                                                
                                                # Download button
                                                from io import BytesIO
                                                buf = BytesIO()
                                                fig.savefig(buf, format='png', dpi=600, bbox_inches='tight', 
                                                           facecolor='white', transparent=False)
                                                buf.seek(0)
                                                
                                                st.download_button(
                                                    label=f"📥 Download Chart ({selected_cave}_{selected_species}.png)",
                                                    data=buf,
                                                    file_name=f"StackedChart_{selected_cave}_{selected_species}.png",
                                                    mime="image/png"
                                                )
                                                
                                                # Interpretation guide
                                                with st.expander("ℹ️ How to Read This Stacked Chart"):
                                                    # Get species requirements for display
                                                    if selected_species == "Ghost Bat":
                                                        temp_opt = "23-28°C"
                                                        rh_opt = "50-100%"
                                                    else:  # PLNB
                                                        temp_opt = "28-32°C"
                                                        rh_opt = "85-100%"
                                                    
                                                    st.markdown(f"""
                                                    **Optimal Ranges for {selected_species}:**
                                                    - **Temperature:** {temp_opt}
                                                    - **Humidity:** {rh_opt}
                                                    
                                                    **Chart Layout:**
                                                    - Three charts side-by-side (Temperature | Humidity | Combined)
                                                    - X-axis: Months (time progression)
                                                    - Y-axis: Percentage of readings (0-100%)
                                                    - Colored layers show proportion of time in each suitability category
                                                    
                                                    **Color Guide (Best to Worst):**
                                                    - 🟢 **Green**: Optimal (within species requirements)
                                                    - 🟡 **Yellow**: Marginal (within ±10% buffer zone)
                                                    - 🟠 **Orange**: Suboptimal (±10-20% out)
                                                    - 🟠 **Dark Orange**: Poor (±20-30% out)
                                                    - 🔴 **Red-Orange**: Unsuitable (±30-40% out)
                                                    - 🔴 **Dark Red**: Highly unsuitable (>±40% out)
                                                    
                                                    **Reading the Charts:**
                                                    - **Left (Temperature):** Shows temperature suitability with °C ranges in legend
                                                    - **Middle (Humidity):** Shows humidity suitability with % ranges in legend
                                                    - **Right (Combined):** Shows overall suitability (worst of temp and humidity)
                                                    - More green = better habitat quality
                                                    - Compare left and middle to identify limiting factor
                                                    - Combined chart shows when BOTH parameters are suitable
                                                    
                                                    **Interpretation Examples:**
                                                    - **All green:** Excellent habitat throughout monitoring period
                                                    - **Temperature green, Humidity red:** Humidity is the limiting factor
                                                    - **Both showing red:** Both parameters need management attention
                                                    - **Seasonal patterns:** Color changes month-to-month show seasonal variation
                                                    
                                                    **For Reports:**
                                                    - Image sized at 42cm × 16cm for A3 landscape
                                                    - 600 DPI ensures crisp printing
                                                    - Leave space below for interpretation text in Word
                                                    """)
                                            else:
                                                st.error("Failed to generate stacked chart")
                                        
                                        # ===== DUAL-AXIS LINE CHART =====
                                        elif chart_type == "Dual-Axis Line Chart":
                                            try:
                                                # Create dual-axis chart generator
                                                dual_gen = MicroclimateDualAxisChart()
                                                
                                                # Generate chart
                                                fig = dual_gen.generate_dual_axis_chart(
                                                    raw_df=raw_df,
                                                    cave_name=selected_cave,
                                                    species=selected_species,
                                                    start_date=site_data['start_date'],
                                                    end_date=site_data['end_date'],
                                                    output_path=None
                                                )
                                                
                                                if fig:
                                                    # Display the figure
                                                    st.pyplot(fig)
                                                    plt.close(fig)
                                                    
                                                    # Download button
                                                    from io import BytesIO
                                                    buf = BytesIO()
                                                    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight',
                                                               facecolor='white', transparent=False)
                                                    buf.seek(0)
                                                    
                                                    st.download_button(
                                                        label=f"📥 Download Dual-Axis Chart",
                                                        data=buf,
                                                        file_name=f"DualAxisChart_{selected_cave}_{selected_species}.png",
                                                        mime="image/png"
                                                    )
                                                    
                                                    # Interpretation guide
                                                    with st.expander("ℹ️ How to Read This Dual-Axis Chart"):
                                                        if selected_species == "Ghost Bat":
                                                            temp_opt = "23-28°C"
                                                            rh_opt = "50-100%"
                                                        else:  # PLNB
                                                            temp_opt = "28-32°C"
                                                            rh_opt = "85-100%"
                                                        
                                                        st.markdown(f"""
                                                        **Dual-Axis Line Chart:**
                                                        
                                                        **Optimal Ranges for {selected_species}:**
                                                        - **Temperature:** {temp_opt}
                                                        - **Humidity:** {rh_opt}
                                                        
                                                        **How to Read:**
                                                        - **Left Y-axis (Teal):** Temperature in °C
                                                        - **Right Y-axis (Secondary Teal):** Humidity in %
                                                        - **Solid teal line:** Roost temperature
                                                        - **Dashed teal line:** Roost humidity
                                                        - **Background zones:** Semi-transparent colored bands
                                                          - 🟢 Green = Optimal range
                                                          - 🟡 Yellow = Marginal (±10%)
                                                          - 🟠 Orange = Suboptimal (±20%)
                                                          - 🔴 Red = Unsuitable (>±20%)
                                                        
                                                        **Benefits:**
                                                        - See both parameters together on one chart
                                                        - Actual temperature and humidity values visible
                                                        - Easy to identify which parameter is limiting
                                                        - Zones help visualize suitability ranges
                                                        """)
                                                else:
                                                    st.error("Failed to generate dual-axis chart")
                                            except Exception as e:
                                                st.error(f"Error generating dual-axis chart: {str(e)}")
                                                st.exception(e)
                                    else:
                                        st.warning(f"No data available for {selected_cave}")
                                else:
                                    st.warning(f"Site {selected_cave} not found in processed data")
                                    
                            except Exception as e:
                                st.error(f"Error generating stacked chart: {str(e)}")
                                st.exception(e)
                    
                    # Batch generation option
                    st.markdown("---")
                    st.subheader("Batch Generation")
                    
                    if st.button("Generate All Stacked Charts", key="gen_all_stacked"):
                        with st.spinner("Generating stacked charts for all sites and species..."):
                            try:
                                import tempfile
                                import zipfile
                                import os
                                
                                stacked_gen = MicroclimateStackedChart()
                                
                                # Create temporary directory
                                with tempfile.TemporaryDirectory() as temp_dir:
                                    generated_files = []
                                    
                                    # Generate for each continuous site and both species
                                    for site in continuous_sites:
                                        site_key = f"{site}_continuous"
                                        if site_key in processed_data:
                                            site_data = processed_data[site_key]
                                            raw_df = site_data.get('raw_data', pd.DataFrame())
                                            
                                            if not raw_df.empty:
                                                for species in ["Ghost Bat", "PLNB"]:
                                                    try:
                                                        output_path = os.path.join(
                                                            temp_dir,
                                                            f"StackedChart_{site}_{species}.png"
                                                        )
                                                        
                                                        fig = stacked_gen.generate_stacked_chart(
                                                            raw_df=raw_df,
                                                            cave_name=site,
                                                            species=species,
                                                            start_date=site_data['start_date'],
                                                            end_date=site_data['end_date'],
                                                            output_path=output_path
                                                        )
                                                        
                                                        if fig:
                                                            generated_files.append(output_path)
                                                            plt.close(fig)
                                                    except Exception as e:
                                                        st.warning(f"Error generating {site} - {species}: {str(e)}")
                                    
                                    if generated_files:
                                        # Create zip file
                                        zip_path = os.path.join(temp_dir, "stacked_charts.zip")
                                        with zipfile.ZipFile(zip_path, 'w') as zipf:
                                            for file_path in generated_files:
                                                zipf.write(file_path, os.path.basename(file_path))
                                        
                                        # Read zip file
                                        with open(zip_path, 'rb') as f:
                                            zip_data = f.read()
                                        
                                        st.success(f"✅ Generated {len(generated_files)} stacked charts!")
                                        
                                        st.download_button(
                                            label=f"📥 Download All Charts (ZIP - {len(generated_files)} files)",
                                            data=zip_data,
                                            file_name=f"McPhee_StackedCharts_{datetime.now().strftime('%Y%m%d')}.zip",
                                            mime="application/zip"
                                        )
                                        
                                        # Show list of generated files
                                        with st.expander("Generated Files"):
                                            for file_path in generated_files:
                                                st.text(f"✓ {os.path.basename(file_path)}")
                                    else:
                                        st.warning("No charts were generated. Check that you have continuous monitoring data.")
                                        
                            except Exception as e:
                                st.error(f"Error in batch generation: {str(e)}")
                                st.exception(e)
                else:
                    st.info("No continuous monitoring sites configured. Please configure continuous sites in the Configuration tab.")
            
            elif viz_type == "Roosting Suitability Time Series":
                st.subheader("🌡️ Roosting Suitability Time Series")
                st.markdown("""
                Time-series visualisation showing roosting condition suitability with smooth colour transitions.
                
                **Three-tier suitability:**
                - 🟢 **Optimal:** Within species requirements
                - 🟡 **Marginal:** Within 15% buffer of optimal
                - 🔴 **Unsuitable:** >15% outside optimal range
                
                **Combined suitability:** Both temperature AND humidity must be suitable.
                """)
                
                # Get continuous sites only
                continuous_sites = {k: v for k, v in st.session_state.processed_data.items() 
                                   if v.get('monitoring_type') == 'continuous'}
                
                if continuous_sites:
                    st.markdown("### 🎯 Configuration")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Site selection
                        site_options = {}
                        for site_key, site_data in continuous_sites.items():
                            site_name = site_data.get('site_name', site_key.replace('_continuous', ''))
                            site_options[site_name] = site_key
                        
                        selected_site = st.selectbox(
                            "Select site:",
                            options=list(site_options.keys()),
                            key="roost_suit_site"
                        )
                    
                    with col2:
                        # Species selection
                        species = st.selectbox(
                            "Select species:",
                            options=list(SPECIES_RANGES.keys()),
                            key="roost_suit_species"
                        )
                    
                    # Date range selection
                    st.markdown("### 📅 Date Range")
                    
                    if selected_site:
                        site_key = site_options[selected_site]
                        site_data = st.session_state.processed_data[site_key]
                        
                        # Get default dates from site data
                        default_start = site_data.get('start_date')
                        default_end = site_data.get('end_date')
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            start_date = st.date_input(
                                "Start date:",
                                value=default_start,
                                key="roost_suit_start"
                            )
                        with col2:
                            end_date = st.date_input(
                                "End date:",
                                value=default_end,
                                key="roost_suit_end"
                            )
                        
                        # Resolution option
                        resolution = st.radio(
                            "Data resolution:",
                            options=['daily', '3hourly'],
                            format_func=lambda x: 'Daily means (smoother)' if x == 'daily' else '3-hourly readings (more detail)',
                            horizontal=True,
                            key="roost_suit_resolution"
                        )
                        
                        st.markdown("---")
                        
                        # Generate button
                        if st.button("📊 Generate Roosting Suitability Chart", type="primary", key="gen_roost_suit"):
                            with st.spinner("Generating roosting suitability chart..."):
                                try:
                                    raw_df = site_data.get('full_raw_data', site_data.get('raw_data'))
                                    
                                    if raw_df is not None and not raw_df.empty:
                                        import tempfile
                                        with tempfile.TemporaryDirectory() as tmpdir:
                                            output_path = f"{tmpdir}/roosting_suitability_{selected_site}.png"
                                            
                                            fig = create_suitability_chart(
                                                raw_df=raw_df,
                                                cave_name=selected_site,
                                                species=species,
                                                start_date=start_date,
                                                end_date=end_date,
                                                output_path=output_path,
                                                resolution=resolution
                                            )
                                            
                                            if fig:
                                                st.image(output_path, use_container_width=True)
                                                
                                                # Download button
                                                with open(output_path, 'rb') as f:
                                                    st.download_button(
                                                        label="⬇️ Download Roosting Suitability Chart (PNG)",
                                                        data=f.read(),
                                                        file_name=f"roosting_suitability_{selected_site}_{species.replace(' ', '_')}.png",
                                                        mime="image/png",
                                                        key="download_roost_suit"
                                                    )
                                                
                                                st.success(f"✅ Chart generated for {selected_site} ({species})")
                                                plt.close(fig)
                                            else:
                                                st.warning("No data available for the selected date range.")
                                    else:
                                        st.warning("No data available for selected site.")
                                
                                except Exception as e:
                                    st.error(f"Error generating chart: {e}")
                                    import traceback
                                    st.code(traceback.format_exc())
                else:
                    st.info("No continuous monitoring sites configured. Please load data and configure continuous sites first.")
            
            else:
                st.info(f"📊 {viz_type} visualization - Coming soon")
                st.markdown("*Additional visualizations will be added in future updates*")
                
        else:
            st.info("👈 Generate tables first to view visualizations")
    
    # TAB 4: Audit Reports
    with tab4:
        st.header("Quality Control & Audit Reports")
        
        if st.session_state.tables_generated:
            
            audit_reports = st.session_state.audit_reports
            
            # Date coverage audit
            st.subheader("📅 Date Coverage Summary")
            if 'date_coverage' in audit_reports:
                st.dataframe(
                    audit_reports['date_coverage'],
                    width="stretch",
                    hide_index=True
                )
            
            st.markdown("---")
            
            # Data quality checks
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("✅ Data Quality Checks")
                if 'quality_checks' in audit_reports:
                    st.dataframe(
                        audit_reports['quality_checks'],
                        width="stretch",
                        hide_index=True
                    )
            
            with col2:
                st.subheader("⚠️ Missing Data Summary")
                if 'missing_data' in audit_reports:
                    st.dataframe(
                        audit_reports['missing_data'],
                        width="stretch",
                        hide_index=True
                    )
            
            st.markdown("---")
            
            # Overall status
            if audit_reports.get('all_checks_passed', True):
                st.success("✅ All quality checks passed - Data is ready for reporting")
            else:
                st.warning("⚠️ Some quality issues detected - Review the audit reports above")
                
        else:
            st.info("👈 Generate tables first to view audit reports")
    
    # Export section (always visible at bottom when tables are generated)
    if st.session_state.tables_generated:
        st.markdown("---")
        st.header("📥 Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Export All Tables to Excel", key="export_tables"):
                with st.spinner("Creating Excel workbook..."):
                    try:
                        exporter = ReportExporter()
                        excel_file = exporter.export_to_excel(
                            tables=st.session_state.tables,
                            audit_reports=st.session_state.audit_reports,
                            config=st.session_state.config,
                            processed_data=st.session_state.get('processed_data', {}),
                            master_data_df=st.session_state.get('master_data_df')
                        )
                        
                        st.download_button(
                            label="⬇️ Download Complete Excel Report (Tables + Charts)",
                            data=excel_file,
                            file_name=f"McPhee_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_tables"
                        )
                    except Exception as e:
                        st.error(f"Error creating Excel file: {str(e)}")
        
        # Remove the old separate charts export button - charts are now included in the main export above
        # The Export Tables button now creates native Excel charts, not PNG images
        
        with col2:
            st.info("📊 The Export Tables button above now includes native Excel charts - no separate export needed!")

else:
    # Welcome screen
    st.info("👈 **Get Started:** Load your data file from the sidebar")
    
    st.markdown("### 🦇 About This Dashboard")
    st.markdown("""
    This interactive dashboard automates the generation of wildlife monitoring reports for:
    
    **Species Monitored:**
    - 🦇 **Pilbara Leaf-Nosed Bats (PLNB)** - Activity patterns, call timing, roosting behavior
    - 🦇 **Ghost Bats** - Ultrasonic records, presence/absence, roosting indicators
    
    **Data Collected:**
    - 🌡️ **Microclimate**: Temperature and relative humidity (3-hour intervals)
    - 🌧️ **Weather**: Rainfall, BoM data
    - 🌙 **Astronomical**: Moon illumination, civil twilight times
    
    **Output:**
    - 📊 **14 Automated Tables** covering all monitoring requirements
    - 📈 **Interactive Visualizations** for data exploration
    - 🔍 **Quality Control Audits** ensuring data integrity
    - 📥 **Excel Export** for reporting and archival
    """)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tables", "14", help="Automated table generation")
    with col2:
        st.metric("Continuous Sites", "4", help="Long-term monitoring")
    with col3:
        st.metric("SSM Sites", "12+", help="Short-term surveys")
    with col4:
        st.metric("Data Points", "1000s", help="Per monitoring period")
    
    st.markdown("---")
    st.markdown("### 🚀 Quick Start")
    st.markdown("""
    1. **Load Data**: Use the default path or upload your Excel file
    2. **Configure**: Select sites and enter date ranges
    3. **Generate**: Click the generate button to process all tables
    4. **Export**: Download your complete report as Excel
    """)

# Footer
st.markdown("---")
col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
with col_f1:
    st.caption("© Biologic Environmental Survey 2025")
with col_f2:
    st.caption(f"Dashboard v1.0.0")
with col_f3:
    if st.session_state.data_loaded:
        st.caption(f"✅ Data loaded")
    else:
        st.caption("⏳ Waiting for data")
