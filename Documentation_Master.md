# 🌏 Smart Tour Recommender System - Master Documentation

---

# Part 1: Project Overview (README)

A high-performance, visually stunning recommendation system for exploring Pakistan. This system uses machine learning and advanced data processing to suggest the best destinations based on user preferences, budget, and safety.

## 🚀 Key Features
*   **Smart Recommendations**: Hybrid recommendation engine (Content-based + Collaborative Filtering).
*   **Dynamic UI**: Modern "Glassmorphism" interface with a video background and theme-aware components.
*   **Interactive Maps**: Real-time map visualization with exact location markers that follow your system's dark/light theme.
*   **Deep Dive Insights**: Detailed views for each destination including ratings, reviews, and high-quality image previews.
*   **Analytics Dashboard**: Advanced data visualizations showing tourism trends, budget distributions, and safety scores.
*   **Province Exploration**: Dedicated section to explore Pakistan's diverse regions (Punjab, Sindh, KPK, Balochistan, etc.).

## 🛠️ Technology Stack
*   **Frontend**: Streamlit (Python-based Web Framework)
*   **Mapping**: Pydeck (High-performance spatial rendering)
*   **Charts**: Plotly Express & Seaborn
*   **Data Processing**: Pandas & NumPy
*   **Machine Learning**: Scikit-learn (TF-IDF, Cosine Similarity, NMF)

## 📁 Project Structure
*   `app.py`: The main Streamlit application and UI logic.
*   `raw1.py`: The backend engine (Data Loader, ML Models, User Auth).
*   `assets/`: Folder containing destination images and background video.
*   `data/`: CSV datasets containing information about destinations, users, and ratings.
*   `outputs/`: Generated charts and reports.

---

# Part 2: Execution Guide (How to Run)

Follow these steps to set up and run the application on your local machine.

## 1. Prerequisites
Ensure you have **Python 3.8 or higher** installed. You can check your version by running:
```bash
python --version
```

## 2. Install Dependencies
Navigate to the project directory and install the required Python libraries using pip:
```bash
pip install streamlit pandas numpy pydeck plotly scikit-learn matplotlib seaborn
```

## 3. Run the Application
Start the Streamlit server by running the following command in your terminal:
```bash
streamlit run app.py
```

## 4. Access the App
Once the command is executed, a local URL will be provided (usually `http://localhost:8501`). The app should open automatically in your default web browser.

---

# Part 3: Technical Project Proposal

## 1. Executive Summary
The **Smart Tour Recommender System** is an intelligent, web-based application designed to provide personalized tourism recommendations across Pakistan. Utilizing machine learning, advanced data processing, and a modern "Glassmorphism" web interface, the system analyzes user preferences, destination characteristics, and historical data to suggest optimal travel experiences.

## 2. Project Overview
### Objective
To build a high-performance, visually immersive recommendation engine that matches tourists with Pakistani destinations based on:
- **Personal Preferences**: Adventure, Nature, Beach, City, and Historical sites.
- **Dynamic Constraints**: Budget (Low, Medium, High) and Safety ratings.
- **Data-Driven Insights**: Overall destination scores and community ratings.

### Current Scope
- **Interactive Web UI**: A professional-grade frontend built with Streamlit.
- **Data Engine**: Advanced processing of multiple CSV datasets (Destinations, Users, Reviews, etc.).
- **ML Logic**: Hybrid recommendation model using TF-IDF and Cosine Similarity.
- **Geospatial Mapping**: Real-time map rendering with precise coordinate markers.

## 3. Technology Stack
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend UI** | Streamlit | Modern web interface with dynamic routing. |
| **Styling** | Custom CSS / Glassmorphism | Aesthetic "glass" cards, blur effects, and video backgrounds. |
| **Data Processing** | Pandas, NumPy | Core data manipulation and feature engineering. |
| **Machine Learning** | Scikit-learn | TF-IDF Vectorization and Similarity computations. |
| **Mapping** | Pydeck | High-performance 3D/2D spatial visualizations. |
| **Visualizations** | Plotly Express | Interactive, high-fidelity analytics charts. |
| **Backend Logic** | Python 3.10+ | Consolidated object-oriented engine (`raw1.py`). |

## 4. Frontend & User Experience (Deep Dive)
- **Immersive Visuals**: High-resolution video background of Pakistan's landscapes with a dynamic light/dark mode compatible overlay.
- **Glassmorphism Design**: UI elements (cards, sidebars, buttons) use translucent backgrounds with Gaussian blur and subtle borders.
- **Interactive Maps**: Powered by Pydeck, the map automatically adjusts its style (Dark/Light) to match the system theme.
- **Dynamic Routing**: A sidebar-based navigation system allows users to switch between sections without reloading.
- **Multimedia Integration**: Seamless rendering of images using Base64 encoding.

## 5. Feature-by-Feature: How it Works (Step-by-Step)

### A. Hybrid Recommendation Engine
1.  **Data Ingestion**: Loads 1,000+ records from `PK_Destinations.csv`.
2.  **Tagging**: Creates "Content Tags" by combining Category, Province, and Description.
3.  **Vectorization**: Uses **TF-IDF** to convert tags into mathematical vectors.
4.  **Preference Matching**: Uses **Cosine Similarity** to match user query vectors with destination vectors.
5.  **Weighted Scoring**: Factors in quality scores (Rating, Popularity, History).

### B. Interactive Geospatial Mapping
1.  **Coordinate Extraction**: Pulls Lat/Lon from the database.
2.  **Layer Creation**: Uses Pydeck's ScatterplotLayer for markers.
3.  **Auto-Adaptive Styling**: Detects Dark/Light mode and switches map skin instantly.
4.  **Dynamic Zooming**: Calibrated to **Zoom Level 6.5** for single destination focus.

### C. Analytics & Data Visualization
1.  **Aggregation**: Groups data by Province/Budget using Pandas.
2.  **Visual Rendering**: Uses Plotly for Pie, Bar, and Scatter charts.
3.  **Real-Time Updates**: UI re-calculates charts instantly as sidebar filters change.

### D. Advanced "Glassmorphism" UI
1.  **Layered Background**: 4K video loop + translucent readability overlay.
2.  **Glass Effect**: Applies `backdrop-filter: blur(20px)` for a frosted glass aesthetic.
3.  **Responsive Grid**: Scales to fit any device or window size.

## 6. System Architecture (Technical Pipeline)
1.  **Input Layer**: Sidebar interactions (Preferences/Budget).
2.  **Logic Layer (`raw1.py`)**: `RecommendationEngine` processes filters and similarity.
3.  **Visual Layer (`app.py`)**: Data rendered as HTML "Glass Cards" and Pydeck markers.
4.  **Feedback Loop**: "Deep Dive" triggers instant state updates.

## 7. Conclusion
The **Smart Tour Recommender System** combines sophisticated machine learning with a cutting-edge web frontend to provide a seamless, "alive" experience that makes exploring Pakistan's beauty both easy and visually delightful.
