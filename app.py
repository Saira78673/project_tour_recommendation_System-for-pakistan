"""
  SMART TOUR RECOMMENDER SYSTEM - STREAMLIT               ║
║                         PERFECT UI REPLICA - V3.0                       ║
║                     ALL MOCK IMAGES IMPLEMENTED                         ║
║                    ERROR FIXED - EMPTY LABEL RESOLVED                   ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import numpy as np
import base64
import time
import random
from pathlib import Path
import sys
import os
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go
import datetime
import hashlib

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Smart Tour Recommender",
    page_icon="🌏",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# IMPORT BACKEND
# ============================================================================
# Add the current script's directory to sys.path to ensure raw1 can be imported
# regardless of where the command is run from.
backend_path = Path(__file__).parent.absolute()
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

try:
    from raw1 import (
        Config, DataLoader, DataProcessor, FeatureEngineer,
        RecommendationEngine, UserAuth, TripPlanner, 
        ComparisonEngine, Analytics, Visualizer
    )
except ImportError as e:
    st.error(f"❌ Could not import raw1.py: {e}")
    st.info(f"Current Working Directory: {os.getcwd()}")
    st.info(f"Script Directory: {backend_path}")
    st.info(f"Search Path: {sys.path}")
    st.stop()

# ============================================================================
# LOAD BACKEND (CACHED FOR SPEED)
# ============================================================================
@st.cache_resource(ttl=3600)
def load_backend():
    print("🔄 Loading backend data...")
    data = DataLoader.load_all_data()
    if not data:
        st.error("Failed to load data. Check your data/ folder.")
        st.stop()
    
    master_df = DataProcessor.process(data)
    master_df = FeatureEngineer.engineer_features(master_df)
    
    # FORCE RELOAD CHECK: Ensure coordinates are present
    if 'Latitude' not in master_df.columns or 'Longitude' not in master_df.columns:
        dest_df = pd.read_csv(Path(__file__).parent / 'data' / 'PK_Destinations.csv')
        cols_to_use = ['DestinationID']
        if 'Latitude' not in master_df.columns: cols_to_use.append('Latitude')
        if 'Longitude' not in master_df.columns: cols_to_use.append('Longitude')
        
        master_df = master_df.merge(dest_df[cols_to_use], on='DestinationID', how='left')

    recommender = RecommendationEngine(master_df)
    auth = UserAuth(data['PK_Users'])
    trip_planner = TripPlanner(master_df)
    analytics = Analytics(master_df)
    comparison_engine = ComparisonEngine()
    
    # Pre-calculate global stats to avoid recalculating on every analytics page view
    stats = {
        'total': len(master_df),
        'safe': master_df['IsSafe'].sum(),
        'avg_score': master_df['OverallScore'].mean(),
        'avg_rating': master_df['AvgRating'].mean(),
        'budget_counts': master_df['BudgetCategory'].value_counts().to_dict(),
        'prov_scores': master_df.groupby('Province')['OverallScore'].mean().sort_values(ascending=False).to_dict()
    }
    
    return {
        'master_df': master_df,
        'recommender': recommender,
        'auth': auth,
        'trip_planner': trip_planner,
        'analytics': analytics,
        'comparison_engine': comparison_engine,
        'data': data,
        'global_stats': stats
    }

# Load backend at start
if 'backend' not in st.session_state:
    st.session_state.backend = load_backend()

backend = st.session_state.backend
master_df = backend['master_df']
recommender = backend['recommender']
auth = backend['auth']
trip_planner = backend['trip_planner']
analytics = backend['analytics']
comparison_engine = backend['comparison_engine']
global_stats = backend['global_stats']

# ============================================================================
# CUSTOM CSS & ASSETS - DYNAMIC LIGHT/DARK COMPATIBLE
# ============================================================================
@st.cache_data
def get_static_assets():
    assets_dir = Path(__file__).parent / 'assets'
    bg_path = assets_dir / 'bg.jpg'
    video_path = assets_dir / 'travel.mp4'
    
    bg_b64 = ""
    if bg_path.exists():
        with open(bg_path, "rb") as f:
            bg_b64 = base64.b64encode(f.read()).decode()
            
    video_b64 = ""
    if video_path.exists():
        with open(video_path, "rb") as f:
            video_b64 = base64.b64encode(f.read()).decode()
            
    return bg_b64, video_b64

# Load assets once and cache them
if 'assets' not in st.session_state:
    st.session_state.assets = get_static_assets()

bg_b64, video_b64 = st.session_state.assets

# Inject Video Background & CSS
st.markdown(f"""
    <style>
    /* Video Background Container */
    #video-bg {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: -2; 
        filter: brightness(1.4) contrast(0.9) saturate(1.0); /* Increased brightness, lowered contrast */
        object-fit: cover;
        pointer-events: none;
    }}

    /* Fallback image at the very bottom - VERY LIGHT */
    #bg-fallback {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        z-index: -3;
        background: url('data:image/jpeg;base64,{bg_b64}') no-repeat center center fixed;
        background-size: cover;
        opacity: 0.25; /* More visible fallback since video is very light */
    }}

    /* Overlay for readability */
    .video-overlay {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(255, 255, 255, 0.25); /* Light overlay for visibility */
        z-index: -1;
        pointer-events: none;
    }}

    @media (prefers-color-scheme: dark) {{
        .video-overlay {{
            background: rgba(0, 0, 0, 0.3); /* Darker overlay for dark mode */
        }}
    }}

    /* FORCE TRANSPARENCY on all Streamlit layers to reveal video */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .stAppViewMain, [data-testid="stMain"] {{
        background-color: transparent !important;
        background-image: none !important;
    }}

    :root {{
        --glass-bg: rgba(255, 255, 255, 0.08); 
        --glass-border: rgba(255, 255, 255, 0.15);
        --text-color: #ffffff;
        --sidebar-width: 250px;
    }}

    /* Light Mode Overrides */
    @media (prefers-color-scheme: light) {{
        :root {{
            --glass-bg: rgba(255, 255, 255, 0.8);
            --glass-border: rgba(0, 0, 0, 0.15);
            --text-color: #000000; /* Pure black for maximum contrast */
        }}
    }}

    /* Apply text color and readability shadow */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, [data-testid="stWidgetLabel"] {{
        color: var(--text-color) !important;
    }}

    /* Remove extra margins and padding */
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
        max-width: 95% !important;
    }}

    [data-testid="stSidebar"] {{
        min-width: var(--sidebar-width) !important;
        max-width: var(--sidebar-width) !important;
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(15px) !important;
        border-right: 1px solid var(--glass-border) !important;
    }}

    .main-pane, .glass, .sidebar-section {{
        background: var(--glass-bg) !important;
        backdrop-filter: blur(20px) saturate(160%) !important;
        border-radius: 20px !important;
        border: 1px solid var(--glass-border) !important;
        padding: 20px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1) !important;
        margin-bottom: 15px !important;
    }}

    .glass-card {{
        background: rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 15px !important;
        border: 1px solid var(--glass-border) !important;
        padding: 12px !important;
        margin-bottom: 12px !important;
        display: flex !important;
        align-items: center !important;
        gap: 12px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer;
    }}

    .glass-card:hover {{
        background: rgba(255, 255, 255, 0.2) !important;
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.15) !important;
    }}

    .match-badge {{ 
        background: linear-gradient(135deg, #00a884, #00ffa2) !important;
        color: white !important; 
        padding: 4px 8px !important; 
        border-radius: 8px !important; 
        font-size: 10px !important; 
        font-weight: 800 !important;
        text-align: center !important;
        box-shadow: 0 4px 8px rgba(0, 168, 132, 0.3);
    }}

    .stButton > button {{ 
        background: rgba(100, 255, 218, 0.1) !important; 
        border: 1px solid #00a884 !important; 
        border-radius: 10px !important; 
        color: var(--text-color) !important; 
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }}

    .stButton > button:hover {{ 
        background: #00a884 !important; 
        color: white !important;
        border-color: #00ffa2 !important;
    }}

    .js-plotly-plot .plotly .bg {{ fill: transparent !important; }}
    </style>
    
    <video autoplay loop muted playsinline id="video-bg">
        <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
    </video>
    <div id="bg-fallback"></div>
    <div class="video-overlay"></div>
""", unsafe_allow_html=True)


# ============================================================================
# SESSION STATE
# ============================================================================
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'landing'
if 'nav_choice' not in st.session_state:
    st.session_state.nav_choice = "🏠 Home / Overview"
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'preferences' not in st.session_state:
    st.session_state.preferences = []
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = None
if 'selected_destination' not in st.session_state:
    st.session_state.selected_destination = None

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
@st.cache_data(show_spinner=False)
def get_destination_image(dest_name, dest_type='Nature'):
    assets_dir = Path(__file__).parent / 'assets'
    if not assets_dir.exists(): return None

    # Normalization for matching
    search_name = dest_name.lower().replace(" ", "").replace("_", "").replace("-", "")
    
    # Pre-scan assets for efficiency
    try:
        all_files = list(assets_dir.iterdir())
    except:
        return None

    # Priority 1: Direct Filename Match (Case-insensitive, stripped)
    for file in all_files:
        if file.is_file() and file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
            clean_file_name = file.stem.lower().replace(" ", "").replace("_", "").replace("-", "")
            if clean_file_name == search_name:
                with open(file, "rb") as f: return base64.b64encode(f.read()).decode()

    # Priority 2: Smart Keyword/Substring Match for those long filenames
    # This handles "Discover Afghanistan's Natural Beauty_ Bala Hissar..." etc.
    manual_keywords = {
        "Chenab River Bank": ["chenab"],
        "Bala Hissar Fort": ["balahissar"],
        "PAF Museum Karachi": ["pfmuseum", "pafmuseum"],
        "Anarkali Bazaar": ["anarkali"],
        "Saidpur Village": ["saidpur"],
        "Banjosa Lake": ["banjosa"],
        "Arang Kel": ["arangkel"],
        "Hanna Lake": ["hanna"],
        "Khaplu Palace": ["khaplu"],
        "Manthoka Waterfall": ["manthokha"],
        "Rakaposhi View Point": ["rakaposhi"],
        "Shandur Pass": ["shundur", "shandur"],
        "Taxila Museum": ["taxila"],
        "Ayubia National Park": ["ayubia"],
        "Miranjani Top": ["miranjani"],
        "Mushkpuri Top": ["mushkpuri"],
        "Thandiani": ["thandiani"],
        "Basho Valley": ["basho"],
        "Khewra Salt Mine": ["khewra", "saltmine"],
        "Safari Park": ["safari"],
        "Clifton Beach": ["clifton"],
        "Churna Island": ["churna"],
        "Rawal Lake": ["rawal"],
        "Peer Sohawa": ["sohawa", "daman"],
        "Kenjhar Lake": ["kenjhar", "sindh"],
        "Manchar Lake": ["manchar"]
    }

    keywords = manual_keywords.get(dest_name, [dest_name.lower()])
    for kw in keywords:
        for file in all_files:
            if file.is_file() and file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                fname_clean = file.name.lower().replace(" ", "").replace("_", "").replace("-", "")
                if kw.lower() in fname_clean:
                    with open(file, "rb") as f: return base64.b64encode(f.read()).decode()

    # Priority 3: Specific Hardcoded Backup Mappings
    specific_map = {"Peer Sohawa": "daman_e_koh.jpg", "Rawal Lake": "khanpur_dam.jpg"}
    if dest_name in specific_map:
        img_path = assets_dir / specific_map[dest_name]
        if img_path.exists():
            with open(img_path, "rb") as f: return base64.b64encode(f.read()).decode()

    # 4. Final Fallback (Random but consistent based on hash)
    category_fallbacks = {
        'Historical': ['badshahi_mosque.jpg', 'derawar_fort.jpg', 'rohtas_fort.jpg'],
        'Nature': ['valley.jpg', 'nature.jpg', 'hunza.jpg'],
        'Adventure': ['adventure.jpg', 'malam_jabba.jpg'],
        'Beach': ['hammerhead_gwadar.jpg'],
        'City': ['islamabad.jpg', 'clock_tower_faisalabad.jpg']
    }
    available_fbs = [img for img in category_fallbacks.get(dest_type, []) if (assets_dir / img).exists()]
    if not available_fbs: available_fbs = [f.name for f in all_files if f.suffix.lower() == '.jpg'][:5]
    
    if available_fbs:
        name_hash = int(hashlib.md5(dest_name.encode()).hexdigest(), 16)
        fb_path = assets_dir / available_fbs[name_hash % len(available_fbs)]
        if fb_path.exists():
            with open(fb_path, "rb") as f: return base64.b64encode(f.read()).decode()
                
    return None

def destination_card_html(dest, match_percent=None, idx=None):
    img_b64 = get_destination_image(dest['Name'], dest.get('Type', 'Nature'))
    img_html = f'<img src="data:image/jpeg;base64,{img_b64}" style="width:60px;height:60px;object-fit:cover;border-radius:10px;">' if img_b64 else ''
    match_html = f'<div class="match-badge">{match_percent}%<br>MATCH</div>' if match_percent else ''
    idx_html = f'<span style="opacity:0.5;font-weight:700;font-size:12px;margin-right:5px;">#{idx}</span>' if idx else ''
    dest_id = dest['DestinationID']
    return f"""
    <a href="/?dest_id={dest_id}" target="_self" style="text-decoration:none;color:inherit;">
    <div class="glass-card">
        {idx_html}
        {img_html}
        <div style="flex-grow:1;">
            <h4 style="margin:0;font-size:14px;color:#64ffda;">{dest['Name']}</h4>
            <p style="margin:0;opacity:0.6;font-size:11px;color:white;">{dest.get('Province','Unknown')} • {dest.get('Type','Nature')}</p>
        </div>
        {match_html}
    </div>
    </a>
    """

@st.cache_data
def prepare_map_data(data=None):
    if data is None: 
        # Fallback to all destinations for global overview
        df = master_df.copy()
    elif isinstance(data, dict):
        df = pd.DataFrame([data])
    elif isinstance(data, pd.Series): 
        df = data.to_frame().T
    elif isinstance(data, pd.DataFrame): 
        df = data.copy()
    else: 
        return None
        
    if 'Latitude' in df.columns and 'Longitude' in df.columns:
        # Filter and ensure coordinates are valid
        map_df = df[['Latitude', 'Longitude', 'Name']].dropna()
        return map_df
    return None

def render_map(data=None, height=400):
    """Renders a Map with high-visibility Red Dots"""
    # Auto-detect theme for Map Style
    map_style = "dark"
    try:
        if st.get_option("theme.base") == "light":
            map_style = "light"
    except:
        map_style = "dark"

    with st.container():
        # Default view of Pakistan
        view_state = pdk.ViewState(latitude=30.3753, longitude=69.3451, zoom=5, pitch=0)
        layers = []
        
        # Prepare data
        map_df = prepare_map_data(data)
        
        if map_df is not None and not map_df.empty:
            # Ensure numeric
            map_df['Latitude'] = pd.to_numeric(map_df['Latitude'], errors='coerce')
            map_df['Longitude'] = pd.to_numeric(map_df['Longitude'], errors='coerce')
            map_df = map_df.dropna(subset=['Latitude', 'Longitude'])
            
            if not map_df.empty:
                # Recenter and Zoom
                avg_lat = map_df['Latitude'].mean()
                avg_lon = map_df['Longitude'].mean()
                
                # Show full Pakistan map instead of zooming in deep
                zoom_level = 5.2 if len(map_df) > 1 else 9.0 # Zoom in a bit more for single point
                
                view_state = pdk.ViewState(
                    latitude=avg_lat, 
                    longitude=avg_lon, 
                    zoom=zoom_level, 
                    pitch=0
                )
                
                # Sharp Red Dots Layer - Enhanced visibility
                layers.append(pdk.Layer(
                    "ScatterplotLayer",
                    map_df,
                    get_position=["Longitude", "Latitude"],
                    get_color=[255, 0, 0, 240], # Brighter Red
                    get_radius=20000 if len(map_df) > 1 else 5000, # Smaller radius for single point zoom
                    radius_min_pixels=8, # Medium size (Force minimum pixels)
                    radius_max_pixels=15, # Limit maximum size
                    pickable=True,
                    filled=True,
                    stroked=True,
                    line_width_min_pixels=1,
                    get_line_color=[255, 255, 255], # White border for contrast
                ))

        try:
            st.pydeck_chart(pdk.Deck(
                layers=layers, 
                initial_view_state=view_state, 
                map_style=map_style,
                tooltip={"text": "<b>{Name}</b>"}
            ), use_container_width=True)
        except Exception as e:
            # Absolute fallback
            if map_df is not None and not map_df.empty:
                st.map(map_df)
            else:
                st.info("Map is currently unavailable.")

# ============================================================================
# PAGE FUNCTIONS
# ============================================================================
def landing_page():
    col1, col2, col3 = st.columns([6, 1, 2])
    with col3:
        if st.session_state.current_user:
            st.markdown(f"**{st.session_state.user_name}**")
            if st.button("🚪 Logout", key="land_logout"):
                st.session_state.current_user = None
                st.session_state.user_name = None
                st.rerun()
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 style='text-align:center;'>Where does your heart want to go?</h1>", unsafe_allow_html=True)
        all_destinations = sorted(master_df['Name'].unique().tolist())
        search_query = st.selectbox("Search destinations", options=[""] + all_destinations, index=0, placeholder="Try 'hiking', 'beaches'...", label_visibility="collapsed")
        if search_query and search_query != "":
            with st.spinner("Analyzing..."):
                # EXACT MATCH CHECK: If user selected a specific destination name, show it directly
                exact_match = master_df[master_df['Name'].str.lower() == search_query.lower()]
                if not exact_match.empty:
                    st.session_state.selected_destination = exact_match.iloc[0].to_dict()
                    st.session_state.recommendations = exact_match # Keep it as a dataframe
                    st.session_state.preferences = [search_query]
                    st.session_state.nav_choice = "🔍 Find the Best Matches"
                    st.session_state.current_page = 'deep_dive'
                    st.rerun()

                results = recommender.recommend(preferences=[search_query], top_n=6)
                if not results.empty:
                    st.session_state.recommendations = results
                    st.session_state.preferences = [search_query]
                    st.session_state.nav_choice = "🔍 Find the Best Matches"
                    st.session_state.current_page = 'results'
                    st.rerun()
        
        if st.button("🔍 Find My Best Matches", use_container_width=True):
            st.session_state.nav_choice = "🔍 Find the Best Matches"
            if st.session_state.recommendations is not None:
                st.session_state.current_page = 'results'
            else:
                st.session_state.current_page = 'preferences'
            st.rerun()
        
        if st.button("↓ Explore Provinces", use_container_width=True):
            st.session_state.nav_choice = "🗺️ Explore Provinces"
            st.rerun()
        if st.button("📊 View Analytics Dashboard", use_container_width=True):
            st.session_state.nav_choice = "📊 Analytics Dashboard"
            st.rerun()
            
    st.markdown("---")
    st.markdown("<h3 style='text-align:center;'>📍 Explore All Destinations</h3>", unsafe_allow_html=True)
    render_map() # Show all with Red Dots by default on Home Page

def preferences_page():
    st.markdown("<h2 style='text-align:center;'>What are you looking for?</h2>", unsafe_allow_html=True)
    
    # Use a container to group the preferences for better rendering
    with st.container():
        cols = st.columns(5)
        pref_options = ['Adventure', 'Nature', 'Beach', 'City', 'Historical']
        pref_emojis = ['⛰️', '🌲', '🏝️', '🌆', '🏰']
        
        for i, (pref, emoji) in enumerate(zip(pref_options, pref_emojis)):
            with cols[i]:
                # Optimized toggle logic
                is_selected = pref in st.session_state.preferences
                
                # Visual feedback using a simple border
                border_style = "border: 2px solid #64ffda;" if is_selected else "border: 1px solid rgba(255,255,255,0.1);"
                bg_color = "background: rgba(100,255,218,0.2);" if is_selected else "background: rgba(100,255,218,0.05);"
                
                st.markdown(f"""
                <div style="{bg_color}{border_style}border-radius:16px;padding:15px;text-align:center;transition: all 0.2s;">
                    <div style="font-size:25px;">{emoji}</div>
                    <p style="font-weight:600;margin-top:5px;font-size:14px;">{pref}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Label changes dynamically to suggest action
                btn_label = f"Remove {pref}" if is_selected else f"Select {pref}"
                if st.button(btn_label, key=f"pref_btn_{pref}", use_container_width=True):
                    if is_selected:
                        st.session_state.preferences.remove(pref)
                    else:
                        st.session_state.preferences.append(pref)
                    st.rerun()

    st.markdown("---")
    
    # Action area
    if st.session_state.preferences:
        st.write(f"Selected: {', '.join(st.session_state.preferences)}")
        if st.button("🚀 Find My Best Matches", use_container_width=True, type="primary"):
            with st.spinner("Finding matches..."):
                results = recommender.recommend(preferences=st.session_state.preferences, top_n=5)
                st.session_state.recommendations = results
                st.session_state.current_page = 'results'
                st.rerun()
    else:
        st.info("Please select at least one category to get recommendations.")

def results_page():
    st.markdown('<div class="main-pane">', unsafe_allow_html=True)
    col_left, col_center, col_right = st.columns([1, 1.75, 2.25], gap="large")
    with col_left:
        if st.button("🔍 Back to Search", use_container_width=True):
            st.session_state.current_page = 'preferences'
            st.rerun()
        st.markdown("### Preferences")
        safety = st.toggle("SAFETY FIRST", value=True)
        budget = st.radio("BUDGET", ["L", "M", "H"], horizontal=True, index=1)
        budget_map = {'L': 'Low', 'M': 'Medium', 'H': 'High'}
        rec_count = st.slider("Count", 1, 15, 5)
        
        # Auto-update results (Cached for performance)
        st.session_state.recommendations = recommender.recommend(
            preferences=st.session_state.preferences, 
            budget_filter=budget_map.get(budget), 
            safety_only=safety, 
            top_n=rec_count
        )
    with col_center:
        st.markdown("### Your Matches")
        if st.session_state.recommendations is not None:
            for idx, (_, dest) in enumerate(st.session_state.recommendations.iterrows(), 1):
                match_pct = int(dest.get('FinalScore', 0) * 100) if 'FinalScore' in dest else 95
                st.markdown(destination_card_html(dest, match_pct, idx), unsafe_allow_html=True)
                # Redundant button removed as cards/images are now directly clickable to explore
    with col_right:
        st.markdown("### 📍 Location Insights")
        render_map(st.session_state.recommendations)
    st.markdown('</div>', unsafe_allow_html=True)

def deep_dive_page():
    dest = st.session_state.selected_destination
    if st.button("← Back to Results"):
        st.session_state.current_page = 'results'
        st.rerun()
    col_l, col_r = st.columns(2)
    with col_l:
        img_b64 = get_destination_image(dest['Name'], dest.get('Type', 'Nature'))
        if img_b64: st.image(f"data:image/jpeg;base64,{img_b64}", use_container_width=True)
        st.markdown(f"### {dest['Name']}")
        st.write(f"Province: {dest['Province']}")
        st.write(f"Category: {dest['Type']}")
    with col_r:
        st.markdown("### Stats")
        st.metric("Overall Score", f"{dest.get('OverallScore',0):.2f}/5")
        st.metric("Avg Rating", f"{dest.get('AvgRating',0):.1f}/5")
        render_map(dest)

def analytics_page():
    with st.container():
        st.markdown("<h1 style='text-align:center;'>Analytics Dashboard</h1>", unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Destinations", global_stats['total'])
        m2.metric("Filter Effectiveness", "98%")
        m3.metric("ML Weighted Score", "0.89")
        m4.metric("Avg Rating", f"{global_stats['avg_rating']:.1f}")
        
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("### Budget Distribution")
            fig = px.pie(names=list(global_stats['budget_counts'].keys()), values=list(global_stats['budget_counts'].values()), hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("### Top Provinces by Score")
            fig = px.bar(x=list(global_stats['prov_scores'].keys()), y=list(global_stats['prov_scores'].values()))
            st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# MAIN ROUTER
# ============================================================================
def main():
    # Handle direct destination clicks from HTML cards
    if "dest_id" in st.query_params:
        try:
            dest_id = int(st.query_params["dest_id"])
            dest_match = master_df[master_df['DestinationID'] == dest_id]
            if not dest_match.empty:
                st.session_state.selected_destination = dest_match.iloc[0].to_dict()
                st.session_state.nav_choice = "🔍 Find the Best Matches"
                st.session_state.current_page = 'deep_dive'
                st.query_params.clear()
                st.rerun()
        except:
            pass

    with st.sidebar:
        st.markdown("<h2 style='color:#64ffda;'>Explore Pakistan</h2>", unsafe_allow_html=True)
        
        # Track previous nav choice to detect change
        old_nav = st.session_state.nav_choice
        
        # Link nav_choice to st.session_state for external updates
        st.session_state.nav_choice = st.radio(
            "Navigation Menu",
            ["🏠 Home / Overview", "🔍 Find the Best Matches", "🗺️ Explore Provinces", "💎 Deep Driven Destinations", "📊 Analytics Dashboard"],
            index=["🏠 Home / Overview", "🔍 Find the Best Matches", "🗺️ Explore Provinces", "💎 Deep Driven Destinations", "📊 Analytics Dashboard"].index(st.session_state.nav_choice)
        )
        
        # Reset current_page if user switches to Find Best Matches via sidebar
        if st.session_state.nav_choice != old_nav:
            if st.session_state.nav_choice == "🔍 Find the Best Matches":
                if st.session_state.recommendations is not None:
                    st.session_state.current_page = 'results'
                else:
                    st.session_state.current_page = 'preferences'
            st.rerun()

        st.markdown("---")
        if st.session_state.current_user:
            st.write(f"User: {st.session_state.user_name}")
            if st.button("Logout"):
                st.session_state.current_user = None
                st.session_state.user_name = None
                st.rerun()

    # Routing
    if st.session_state.nav_choice == "🏠 Home / Overview":
        landing_page()
    elif st.session_state.nav_choice == "🔍 Find the Best Matches":
        if st.session_state.current_page == 'results': results_page()
        elif st.session_state.current_page == 'deep_dive': deep_dive_page()
        else: preferences_page()
    elif st.session_state.nav_choice == "🗺️ Explore Provinces":
        st.markdown("## 🗺️ Explore Pakistan by Province")
        provinces = sorted(master_df['Province'].unique())
        cols = st.columns(3)
        for i, prov in enumerate(provinces):
            with cols[i % 3]:
                st.markdown(f'<div class="glass" style="text-align:center;"><h3>{prov}</h3></div>', unsafe_allow_html=True)
                prov_dest = master_df[master_df['Province'] == prov].nlargest(1, 'OverallScore').iloc[0]
                img_b64 = get_destination_image(prov_dest['Name'], prov_dest['Type'])
                if img_b64:
                    st.image(f"data:image/jpeg;base64,{img_b64}", use_container_width=True)
                count = len(master_df[master_df['Province'] == prov])
                st.write(f"Destinations: {count}")
                if st.button(f"Explore {prov}", key=f"prov_{prov}"):
                    results = master_df[master_df['Province'] == prov].nlargest(10, 'OverallScore')
                    st.session_state.recommendations = results
                    st.session_state.nav_choice = "🔍 Find the Best Matches"
                    st.session_state.current_page = 'results'
                    st.rerun()

    elif st.session_state.nav_choice == "💎 Deep Driven Destinations":
        st.markdown("## 💎 Premium Destinations (Top Rated)")
        hidden_gems = master_df.nlargest(12, 'OverallScore')
        cols = st.columns(2)
        for i, (_, gem) in enumerate(hidden_gems.iterrows()):
            with cols[i % 2]:
                st.markdown(destination_card_html(gem, idx=i+1), unsafe_allow_html=True)
                if st.button(f"View Details: {gem['Name']}", key=f"deep_{gem['DestinationID']}", use_container_width=True):
                    st.session_state.selected_destination = gem
                    st.session_state.current_page = 'deep_dive'
                    st.session_state.nav_choice = "🔍 Find the Best Matches"
                    st.rerun()

    elif st.session_state.nav_choice == "📊 Analytics Dashboard":
        st.markdown("<h1 style='text-align:center;'>📊 Advanced Tourism Analytics</h1>", unsafe_allow_html=True)
        
        # Top Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Spots", global_stats['total'])
        m2.metric("Avg Quality", f"{global_stats['avg_score']:.2f}")
        m3.metric("Safe Routes", f"{global_stats['safe']}")
        m4.metric("User Rating", f"{global_stats['avg_rating']:.1f} ★")
        
        st.markdown("---")
        
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("### 💰 Budget Category Split")
            fig = px.pie(
                names=list(global_stats['budget_counts'].keys()), 
                values=list(global_stats['budget_counts'].values()), 
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            st.markdown("### 🏆 Top Provinces Performance")
            prov_df = pd.DataFrame(list(global_stats['prov_scores'].items()), columns=['Province', 'Score'])
            fig = px.bar(
                prov_df, x='Province', y='Score', 
                color='Score', color_continuous_scale='Viridis'
            )
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
            
        st.markdown("---")
        
        c3, c4 = st.columns([1.5, 1])
        with c3:
            st.markdown("### 🛡️ Safety vs. Popularity Correlation")
            fig = px.scatter(
                master_df, x='Popularity', y='OverallScore', 
                color='Province', size='AvgRating',
                hover_name='Name', template='plotly_dark'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with c4:
            st.markdown("### 📂 Type Distribution")
            type_counts = master_df['Type'].value_counts()
            fig = px.funnel_area(names=type_counts.index, values=type_counts.values)
            st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
