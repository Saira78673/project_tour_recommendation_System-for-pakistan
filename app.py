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
    st.stop()

# ============================================================================
# LOAD BACKEND (CACHED FOR SPEED)
# ============================================================================
@st.cache_resource(ttl=3600)
def load_backend():
    data = DataLoader.load_all_data()
    if not data:
        st.error("Failed to load data. Check your data/ folder.")
        st.stop()
    
    master_df = DataProcessor.process(data)
    master_df = FeatureEngineer.engineer_features(master_df)
    
    # Ensure coordinates are present
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
# CUSTOM CSS & ASSETS
# ============================================================================
@st.cache_data
def get_static_assets():
    assets_dir = Path(__file__).parent / 'assets'
    bg_path = assets_dir / 'bg.jpg'
    video_path = assets_dir / 'travel.mp4'
    
    bg_b64 = ""
    if bg_path.exists():
        with open(bg_path, "rb") as f: bg_b64 = base64.b64encode(f.read()).decode()
            
    video_b64 = ""
    if video_path.exists():
        with open(video_path, "rb") as f: video_b64 = base64.b64encode(f.read()).decode()
            
    return bg_b64, video_b64

if 'assets' not in st.session_state:
    st.session_state.assets = get_static_assets()

bg_b64, video_b64 = st.session_state.assets

st.markdown(f"""
    <style>
    /* Video Background Container */
    #video-bg {{
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        z-index: -2; filter: brightness(1.2); object-fit: cover;
        pointer-events: none; will-change: transform;
    }}
    #bg-fallback {{
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        z-index: -3; background: url('data:image/jpeg;base64,{bg_b64}') no-repeat center center fixed;
        background-size: cover; opacity: 0.2;
    }}
    .video-overlay {{
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(255, 255, 255, 0.2); z-index: -1; pointer-events: none;
    }}
    @media (prefers-color-scheme: dark) {{ .video-overlay {{ background: rgba(0, 0, 0, 0.3); }} }}
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .stAppViewMain, [data-testid="stMain"] {{
        background-color: transparent !important; background-image: none !important;
    }}
    :root {{
        --glass-bg: rgba(255, 255, 255, 0.08); --glass-border: rgba(255, 255, 255, 0.1);
        --text-color: #ffffff; --sidebar-width: 250px;
    }}
    @media (prefers-color-scheme: light) {{
        :root {{ --glass-bg: rgba(255, 255, 255, 0.85); --glass-border: rgba(0, 0, 0, 0.1); --text-color: #000000; }}
    }}
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, [data-testid="stWidgetLabel"] {{
        color: var(--text-color) !important; text-rendering: optimizeSpeed;
    }}
    .block-container {{ padding: 0.5rem !important; max-width: 100% !important; }}
    @media (min-width: 768px) {{ .block-container {{ padding: 2rem !important; max-width: 95% !important; }} }}
    [data-testid="stSidebar"] {{
        min-width: var(--sidebar-width) !important; max-width: var(--sidebar-width) !important;
        background: rgba(255, 255, 255, 0.05) !important; backdrop-filter: blur(5px) !important;
        border-right: 1px solid var(--glass-border) !important;
    }}
    .main-pane, .glass, .sidebar-section {{
        background: var(--glass-bg) !important; backdrop-filter: blur(6px) saturate(120%) !important;
        border-radius: 12px !important; border: 1px solid var(--glass-border) !important;
        padding: 12px !important; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08) !important; margin-bottom: 10px !important;
    }}
    .glass-card {{
        background: rgba(255, 255, 255, 0.1) !important; border-radius: 10px !important;
        border: 1px solid var(--glass-border) !important; padding: 8px !important; margin-bottom: 8px !important;
        display: flex !important; align-items: center !important; gap: 8px !important;
        transition: transform 0.1s ease !important; cursor: pointer;
    }}
    .glass-card:hover {{ background: rgba(255, 255, 255, 0.15) !important; transform: translateY(-1px); }}
    @media (max-width: 768px) {{
        .stButton > button {{ width: 100% !important; }}
        .main-pane, .glass {{ padding: 8px !important; backdrop-filter: blur(4px) !important; }}
    }}
    .match-badge {{ 
        background: linear-gradient(135deg, #00a884, #00ffa2) !important; color: white !important; 
        padding: 4px 8px !important; border-radius: 8px !important; font-size: 10px !important; 
        font-weight: 800 !important; text-align: center !important; box-shadow: 0 4px 8px rgba(0, 168, 132, 0.3);
    }}
    .stButton > button {{ 
        background: rgba(100, 255, 218, 0.1) !important; border: 1px solid #00a884 !important; 
        border-radius: 10px !important; color: var(--text-color) !important; font-weight: 600 !important;
        transition: all 0.2s !important;
    }}
    .stButton > button:hover {{ background: #00a884 !important; color: white !important; border-color: #00ffa2 !important; }}
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
if 'current_page' not in st.session_state: st.session_state.current_page = 'landing'
if 'nav_choice' not in st.session_state: st.session_state.nav_choice = "🏠 Home / Overview"
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'user_name' not in st.session_state: st.session_state.user_name = None
if 'preferences' not in st.session_state: st.session_state.preferences = []
if 'recommendations' not in st.session_state: st.session_state.recommendations = None
if 'selected_destination' not in st.session_state: st.session_state.selected_destination = None

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
@st.cache_data(show_spinner=False)
def get_assets_list():
    assets_dir = Path(__file__).parent / 'assets'
    if not assets_dir.exists(): return []
    try:
        return list(assets_dir.iterdir())
    except: return []

@st.cache_data(show_spinner=False)
def get_destination_image(dest_name, dest_type='Nature'):
    assets_dir = Path(__file__).parent / 'assets'
    all_files = get_assets_list()
    if not all_files: return None
    search_name = dest_name.lower().replace(" ", "").replace("_", "").replace("-", "")
    for file in all_files:
        if file.is_file() and file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
            clean_file_name = file.stem.lower().replace(" ", "").replace("_", "").replace("-", "")
            if clean_file_name == search_name:
                with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    manual_keywords = {
        "Chenab River Bank": ["chenab"], "Bala Hissar Fort": ["balahissar"],
        "PAF Museum Karachi": ["pfmuseum", "pafmuseum"], "Anarkali Bazaar": ["anarkali"],
        "Saidpur Village": ["saidpur"], "Banjosa Lake": ["banjosa"], "Arang Kel": ["arangkel"],
        "Hanna Lake": ["hanna"], "Khaplu Palace": ["khaplu"], "Manthoka Waterfall": ["manthokha"],
        "Rakaposhi View Point": ["rakaposhi"], "Shandur Pass": ["shundur", "shandur"],
        "Taxila Museum": ["taxila"], "Ayubia National Park": ["ayubia"], "Miranjani Top": ["miranjani"],
        "Mushkpuri Top": ["mushkpuri"], "Thandiani": ["thandiani"], "Basho Valley": ["basho"],
        "Khewra Salt Mine": ["khewra", "saltmine"], "Safari Park": ["safari"], "Clifton Beach": ["clifton"],
        "Churna Island": ["churna"], "Rawal Lake": ["rawal"], "Peer Sohawa": ["sohawa", "daman"],
        "Kenjhar Lake": ["kenjhar", "sindh"], "Manchar Lake": ["manchar"]
    }
    keywords = manual_keywords.get(dest_name, [dest_name.lower()])
    for kw in keywords:
        for file in all_files:
            if file.is_file() and file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                fname_clean = file.name.lower().replace(" ", "").replace("_", "").replace("-", "")
                if kw.lower() in fname_clean:
                    with open(file, "rb") as f: return base64.b64encode(f.read()).decode()
    specific_map = {"Peer Sohawa": "daman_e_koh.jpg", "Rawal Lake": "khanpur_dam.jpg"}
    if dest_name in specific_map:
        img_path = assets_dir / specific_map[dest_name]
        if img_path.exists():
            with open(img_path, "rb") as f: return base64.b64encode(f.read()).decode()
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
        {idx_html} {img_html}
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
    if data is None: df = master_df.copy()
    elif isinstance(data, dict): df = pd.DataFrame([data])
    elif isinstance(data, pd.Series): df = data.to_frame().T
    elif isinstance(data, pd.DataFrame): df = data.copy()
    else: return None
    if 'Latitude' in df.columns and 'Longitude' in df.columns:
        map_df = df[['Latitude', 'Longitude', 'Name']].dropna()
        map_df.columns = ['latitude', 'longitude', 'Name']
        return map_df
    return None

def render_map(data=None, height=400):
    map_style = "dark"
    with st.container():
        view_state = pdk.ViewState(latitude=30.3753, longitude=69.3451, zoom=5.0, pitch=0)
        layers = []
        pak_boundary_url = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries/PAK.geo.json"
        # Shining Bulb Glow Layers
        layers.append(pdk.Layer("GeoJsonLayer", pak_boundary_url, stroked=True, filled=False, get_line_color=[255, 255, 255, 40], line_width_min_pixels=12))
        layers.append(pdk.Layer("GeoJsonLayer", pak_boundary_url, stroked=True, filled=False, get_line_color=[255, 255, 255, 80], line_width_min_pixels=7))
        layers.append(pdk.Layer("GeoJsonLayer", pak_boundary_url, stroked=True, filled=False, get_line_color=[255, 255, 255, 160], line_width_min_pixels=4))
        layers.append(pdk.Layer("GeoJsonLayer", pak_boundary_url, stroked=True, filled=True, get_fill_color=[255, 255, 255, 15], get_line_color=[255, 255, 255, 255], line_width_min_pixels=2, opacity=1.0))
        
        map_df = prepare_map_data(data)
        if map_df is not None and not map_df.empty:
            map_df['latitude'] = pd.to_numeric(map_df['latitude'], errors='coerce')
            map_df['longitude'] = pd.to_numeric(map_df['longitude'], errors='coerce')
            map_df = map_df.dropna(subset=['latitude', 'longitude'])
            if not map_df.empty:
                layers.append(pdk.Layer("ScatterplotLayer", map_df, get_position=["longitude", "latitude"], get_color=[255, 0, 0, 255], get_radius=10000, radius_min_pixels=3, radius_max_pixels=6, pickable=True, filled=True, stroked=True, line_width_min_pixels=1, get_line_color=[255, 255, 255, 220]))
        try:
            st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=view_state, map_style=map_style, tooltip={"text": "<b>{{Name}}</b>"}, theme="dark"), use_container_width=True)
        except Exception as e:
            if map_df is not None and not map_df.empty: st.map(map_df)
            else: st.info("Map is currently unavailable.")

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
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center; font-size: calc(1.5rem + 1.5vw);'>Where does your heart want to go?</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
    with col2:
        all_destinations = sorted(master_df['Name'].unique().tolist())
        search_query = st.selectbox("Search destinations", options=[""] + all_destinations, index=0, placeholder="Try 'hiking', 'beaches'...", label_visibility="collapsed")
        if search_query and search_query != "":
            with st.spinner("Analyzing..."):
                exact_match = master_df[master_df['Name'].str.lower() == search_query.lower()]
                if not exact_match.empty:
                    st.session_state.selected_destination = exact_match.iloc[0].to_dict()
                    st.session_state.recommendations = exact_match
                    st.session_state.preferences = [search_query]
                    st.session_state.nav_choice = "🔍 Find the Best Matches"
                    st.session_state.current_page = 'deep_dive'
                    st.rerun()
        btn_cols = st.columns(2)
        with btn_cols[0]:
            if st.button("🔍 Find My Matches", use_container_width=True):
                st.session_state.nav_choice = "🔍 Find the Best Matches"
                if st.session_state.recommendations is not None: st.session_state.current_page = 'results'
                else: st.session_state.current_page = 'preferences'
                st.rerun()
        with btn_cols[1]:
            if st.button("📊 View Analytics", use_container_width=True):
                st.session_state.nav_choice = "📊 Analytics Dashboard"
                st.rerun()
        if st.button("↓ Explore Provinces", use_container_width=True):
            st.session_state.nav_choice = "🗺️ Explore Provinces"
            st.rerun()
    st.markdown("---")
    st.markdown("<h3 style='text-align:center;'>📍 Global Overview</h3>", unsafe_allow_html=True)
    render_map()

def preferences_page():
    st.markdown("<h2 style='text-align:center;'>What are you looking for?</h2>", unsafe_allow_html=True)
    with st.container():
        cols = st.columns(5)
        pref_options = ['Adventure', 'Nature', 'Beach', 'City', 'Historical']
        pref_emojis = ['⛰️', '🌲', '🏝️', '🌆', '🏰']
        for i, (pref, emoji) in enumerate(zip(pref_options, pref_emojis)):
            with cols[i]:
                is_selected = pref in st.session_state.preferences
                border_style = "border: 2px solid #64ffda;" if is_selected else "border: 1px solid rgba(255,255,255,0.1);"
                bg_color = "background: rgba(100,255,218,0.2);" if is_selected else "background: rgba(100,255,218,0.05);"
                st.markdown(f'<div style="{bg_color}{border_style}border-radius:16px;padding:15px;text-align:center;"><div style="font-size:25px;">{emoji}</div><p style="font-weight:600;margin-top:5px;font-size:14px;">{pref}</p></div>', unsafe_allow_html=True)
                btn_label = f"Remove {pref}" if is_selected else f"Select {pref}"
                if st.button(btn_label, key=f"pref_btn_{pref}", use_container_width=True):
                    if is_selected: st.session_state.preferences.remove(pref)
                    else: st.session_state.preferences.append(pref)
                    st.rerun()
    st.markdown("---")
    if st.session_state.preferences:
        st.write(f"Selected: {', '.join(st.session_state.preferences)}")
        if st.button("🚀 Find My Best Matches", use_container_width=True, type="primary"):
            with st.spinner("Finding matches..."):
                results = recommender.recommend(preferences=st.session_state.preferences, top_n=5)
                st.session_state.recommendations = results
                st.session_state.current_page = 'results'
                st.rerun()
    else: st.info("Please select at least one category to get recommendations.")

def results_page():
    st.markdown('<div class="main-pane">', unsafe_allow_html=True)
    col_left, col_center, col_right = st.columns([1, 1.8, 2.2])
    with col_left:
        if st.button("🔍 Back", use_container_width=True):
            st.session_state.current_page = 'preferences'
            st.rerun()
        st.markdown("### Filters")
        safety = st.toggle("Safety Only", value=True)
        budget = st.radio("Budget", ["L", "M", "H"], horizontal=True, index=1)
        budget_map = {'L': 'Low', 'M': 'Medium', 'H': 'High'}
        rec_count = st.slider("Count", 1, 15, 5)
        st.session_state.recommendations = recommender.recommend(preferences=st.session_state.preferences, budget_filter=budget_map.get(budget), safety_only=safety, top_n=rec_count)
    with col_center:
        st.markdown("### Top Matches")
        if st.session_state.recommendations is not None:
            for idx, (_, dest) in enumerate(st.session_state.recommendations.iterrows(), 1):
                match_pct = int(dest.get('FinalScore', 0) * 100) if 'FinalScore' in dest else 95
                st.markdown(destination_card_html(dest, match_pct, idx), unsafe_allow_html=True)
    with col_right:
        st.markdown("### 📍 Location")
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
        st.write(f"**Province:** {dest['Province']}")
        st.write(f"**Category:** {dest['Type']}")
    with col_r:
        st.markdown("### Stats")
        st.metric("Overall Score", f"{dest.get('OverallScore',0):.2f}/5")
        st.metric("Avg Rating", f"{dest.get('AvgRating',0):.1f}/5")
        render_map(dest)

# ============================================================================
# MAIN ROUTER
# ============================================================================
def main():
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
        except: pass
    with st.sidebar:
        st.markdown("<h2 style='color:#64ffda;'>Explore Pakistan</h2>", unsafe_allow_html=True)
        old_nav = st.session_state.nav_choice
        st.session_state.nav_choice = st.radio("Navigation Menu", ["🏠 Home / Overview", "🔍 Find the Best Matches", "🗺️ Explore Provinces", "💎 Deep Driven Destinations", "📊 Analytics Dashboard"], index=["🏠 Home / Overview", "🔍 Find the Best Matches", "🗺️ Explore Provinces", "💎 Deep Driven Destinations", "📊 Analytics Dashboard"].index(st.session_state.nav_choice))
        if st.session_state.nav_choice != old_nav:
            if st.session_state.nav_choice == "🔍 Find the Best Matches":
                if st.session_state.recommendations is not None: st.session_state.current_page = 'results'
                else: st.session_state.current_page = 'preferences'
            st.rerun()
        st.markdown("---")
        if st.session_state.current_user:
            st.write(f"User: {st.session_state.user_name}")
            if st.button("Logout"):
                st.session_state.current_user = None
                st.session_state.user_name = None
                st.rerun()
    if st.session_state.nav_choice == "🏠 Home / Overview": landing_page()
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
                if img_b64: st.image(f"data:image/jpeg;base64,{img_b64}", use_container_width=True)
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
        st.markdown("### 📍 Premium Spots Overview")
        hidden_gems = master_df.nlargest(12, 'OverallScore')
        render_map(hidden_gems)
        st.markdown("---")
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
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Spots", global_stats['total'])
        m2.metric("Avg Quality", f"{global_stats['avg_score']:.2f}")
        m3.metric("Safe Routes", f"{global_stats['safe']}")
        m4.metric("User Rating", f"{global_stats['avg_rating']:.1f} ★")
        st.markdown("---")
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("### 💰 Budget Category Split")
            fig = px.pie(names=list(global_stats['budget_counts'].keys()), values=list(global_stats['budget_counts'].values()), hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("### 🏆 Top Provinces Performance")
            prov_df = pd.DataFrame(list(global_stats['prov_scores'].items()), columns=['Province', 'Score'])
            fig = px.bar(prov_df, x='Province', y='Score', color='Score', color_continuous_scale='Viridis')
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")
        c3, c4 = st.columns([1.5, 1])
        with c3:
            st.markdown("### 🛡️ Safety vs. Popularity Correlation")
            fig = px.scatter(master_df, x='Popularity', y='OverallScore', color='Province', size='AvgRating', hover_name='Name', template='plotly_dark')
            st.plotly_chart(fig, use_container_width=True)
        with c4:
            st.markdown("### 📂 Type Distribution")
            type_counts = master_df['Type'].value_counts()
            fig = px.funnel_area(names=type_counts.index, values=type_counts.values)
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()

