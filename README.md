# AgriAttribute

> **Biological Yield Attribution & Farmer Decision Platform**  
> Built for **Syngenta Biologicals & ANNAM.AI — Hack Core 2026** (Problem Statement 07)  
> **Team:** Team 15 BHOOMI  
> **Members:** Soham Kadu ([@soham0777](https://github.com/soham0777)), Bhakti Ajay Kadam ([@Bhakti2709](https://github.com/Bhakti2709)), Singireddy Prabhumitrareddy ([@prabhumitra123-debug](https://github.com/prabhumitra123-debug))  
> **Target Organization:** [annam-iitrpr](https://github.com/annam-iitrpr)  
> **Current Repository:** [soham0777/hack-core-ps07-agriattribute](https://github.com/soham0777/hack-core-ps07-agriattribute)  

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=soham0777/hack-core-ps07-agriattribute&branch=main&mainModule=app.py)

---

### 🚀 Zero-Setup Live Cloud Access
The platform is 100% cloud-ready. You do not need to install Python, configure environments, or run local servers:
- **1-Click Streamlit Cloud Launch:** [Launch AgriAttribute on Streamlit Cloud](https://share.streamlit.io/deploy?repository=soham0777/hack-core-ps07-agriattribute&branch=main&mainModule=app.py)
- **Live Interactive Demo:** Anyone can access the full interactive suite in real-time. All AI attribution, disease diagnosis, Agmarknet 2.0 telemetry, and live weather run instantly in the browser.

## The Problem We Wanted to Solve

Indian farmers are increasingly adopting biological crop inputs (like Syngenta Quantis or Isabion) to combat climate stress, erratic monsoons, and extreme heatwaves. However, at harvest time, one critical question remains unanswered:

> *"Did my yield improve because of the biological product I paid for, or was it just favorable monsoon rain and good soil?"*

Traditional agricultural apps either give generic advice or dump raw statistical charts that make little sense to a farmer standing in a field with a budget smartphone. We built **AgriAttribute** to solve this: a fast, touch-friendly, multilingual platform that mathematically isolates the biological yield boost from weather and soil factors, connects directly with live APMC mandi prices and government MSP benchmarks, and translates complex data science into plain language and actionable rupees per acre.

---

## Key Features

### 1. Today's Field Decisions & Weather
- **Live Local Weather:** Real-time temperature, humidity, wind velocity, and cloud cover powered by OpenWeatherMap with automatic 3-key failover to prevent downtime.
- **Spray Safety Window:** Automatically evaluates wind shear to warn farmers if spraying biologicals would cause droplet drift or if conditions are optimal (< 15 km/h).
- **Interactive District Map:** Interactive Leaflet map showing local weather radar overlays, crop distribution, and district contingency baselines.
- **5-Day Agro-Met Forecast:** Daily expected highs, lows, and precipitation probabilities so farmers can plan irrigation and applications in advance.

### 2. Counterfactual Yield & ROI Calculator
- **"Act vs. Do Nothing" Comparison:** Compares predicted harvest with biological treatment against an untreated control field under the exact same weather and soil conditions.
- **SHAP Causal Attribution:** Uses an XGBoost regressor ($R^2 = 0.998$) with SHAP TreeExplainer to decompose yield into four clear slices:
  - Biological boost ($\Delta Y$)
  - Monsoon weather contribution
  - Baseline soil fertility
  - Base regional yield
- **Plain-Language Financials:** Calculates gross revenue gain, product cost, net profit (₹/acre), and ROI percentage.
- **1-Click WhatsApp Sharing & PDF:** Farmers can share their ROI summary directly on WhatsApp with local farmer groups or download a printable A4 advisory report.

### 3. Agmarknet 2.0 Mandi Prices & MSP Tracker
- **Live APMC Spot Prices:** Real wholesale prices across 24 major Indian commodities (Soybean, Cotton, Paddy, Wheat, Mustard, Onion, etc.).
- **Government MSP Comparison:** Flags whether current mandi prices are trading at a premium or discount relative to the official CACP 2024–25 Minimum Support Price.
- **Sell vs. Hold Recommendations:** Evaluates 72-hour price momentum to help farmers decide whether to sell at the local mandi immediately or hold stock under warehouse receipts.

### 4. Leaf Disease Scanner (LeafVision)
- **Fast CPU Diagnosis:** Optimized vision foundation model that diagnoses leaf diseases in under 30 ms on standard CPU hardware without requiring an expensive cloud GPU.
- **Visual Lesion Segmentation:** Highlights infected areas, calculates chlorosis and necrotic tissue percentages, and estimates potential crop loss.
- **Balanced Prescriptions:** Recommends both approved chemical interventions (CIBRC dosage ratios) and regenerative biological pathways (*Trichoderma viride*, *Pseudomonas fluorescens*, Neem oil).
- **Built-in Sample Gallery:** Includes pre-loaded leaf samples (Soybean, Cotton, Rice, Onion, Healthy) for demonstration and testing.

### 5. Soil Health Card & Fertilizer Calculator
- **DAC&FW Soil Standards:** Calibrated with the Indian Government's 12-parameter Soil Health Card standards across 5 major agro-climatic zones (Deccan Vertisols, Indo-Gangetic Alluvium, Red Soils, etc.).
- **Bag-Level Fertilizer Plan:** Recommends exact bag quantities of Urea, DAP, and MOP tailored to the farmer's target yield, helping reduce chemical over-application while restoring microbial health.

### 6. Farm Journal & Multilingual AI Assistant
- **Cloud Farm Memory:** Synchronizes field logs, diagnostic history, and application records with a Supabase PostgreSQL cloud database.
- **Export to Excel:** Generates a clean, multi-sheet `.xlsx` spreadsheet for farm bookkeeping or loan applications.
- **Multimodal AI Assistant:** Powered by Google Gemini 2.5 Flash. Farmers can ask questions by typing, speaking via voice note, or uploading a field photo. Works in English, Hindi, Marathi, and Telugu.

---

## Practical Engineering Decisions

During development, we made several conscious engineering trade-offs based on real-world farming constraints:

1. **Why we built an Adaptive Device View Mode:**  
   Budget Android smartphones are the primary device used in rural India. Farmers often struggle to read small 13-14px fonts in bright outdoor sunlight. We implemented an adaptive typography engine right at the top of the interface:
   - `📱 Mobile Phone (Large Font)`: Scales base fonts to 18.5px, increases button heights to 56px, and enlarges navigation tabs to 60px for easy thumb taps.
   - `💻 Laptop / Desktop`: Standard compact desktop view.
   - `📟 Tablet Mode`: Balanced 17px view for field extension workers with tablets.

2. **Why we implemented 3-Key API Failover for Weather:**  
   Free-tier weather APIs frequently hit rate limits during hackathons and testing. Instead of letting the app fail, `openweather_service.py` automatically detects HTTP 429 or connection timeouts and seamlessly rotates through a pool of 3 distinct API keys with zero user disruption.

3. **Edge Vision over Cloud Vision:**  
   Cellular connectivity in agricultural fields can be intermittent. Rather than sending heavy image payloads to expensive cloud GPU endpoints, we optimized our foliar diagnosis pipeline to run locally on the CPU in under 30 ms.

4. **Zero-Sidebar, Touch-First Interface:**  
   Sidebars on mobile devices often collapse into a hamburger menu that non-technical users struggle to find. We moved all critical controls—Device Mode, Language Selector, Location, and Navigation Tabs—into the main full-width flow so everything is visible and accessible in one glance.

---

## Tech Stack

- **Frontend & App Engine:** Python 3.10+, Streamlit (custom responsive CSS, Plotly charts, Leaflet GIS)
- **Machine Learning & Attribution:** XGBoost Regressor, SHAP (TreeExplainer), Scikit-Learn
- **Computer Vision:** PyTorch / Torchvision, Pillow (lesion color masking, HSV thresholding)
- **Multilingual AI:** Google Gemini 2.5 Flash API (multimodal audio/image reasoning)
- **Cloud Database:** Supabase (PostgreSQL 15 + PostGIS)
- **Data & APIs:** OpenWeatherMap REST API, Agmarknet daily mandi feeds, DAC&FW Soil Health Card benchmarks, CACP MSP 2024-25 gazette data
- **Export Engines:** FPDF2 (printable A4 PDF dossiers), OpenPyXL (multi-sheet Excel workbooks), WhatsApp deep-linking

---

## Project Structure

```text
hack-core-ps07-agriattribute/
├── app.py                         # Main Streamlit application (Tabs 1 to 6)
├── localization.py                # Translations for English, Hindi, Marathi, Telugu
├── openweather_service.py         # Resilient weather engine with 3-key failover
├── gemini_service.py              # Multimodal Gemini 2.5 assistant (voice, text, image)
├── leafvision_engine.py           # On-device leaf disease diagnosis & lesion analysis
├── agmarknet_engine.py            # Mandi wholesale prices & MSP comparison
├── pricing_and_soil_engine.py     # Soil Health Card 12-parameter fertilizer calculator
├── interactive_map_service.py     # Interactive Leaflet weather & crop map
├── supabase_client.py             # Cloud database connection & Excel ledger exporter
├── pdf_report.py                  # Downloadable printable A4 advisory PDF generator
├── retrain_pipeline.py            # Drag-and-drop CSV model retraining pipeline
├── train_model.py                 # Initial XGBoost and SHAP model training script
├── data_generator.py              # Calibrated 12-crop Indian agricultural trial dataset
├── requirements.txt               # Pinned Python dependencies
├── .env.example                   # Template for API keys
├── README.md                      # This file
├── assets/leaf_samples/           # Test leaf photos for offline disease diagnosis
├── data/                          # Agmarknet mandi report CSV and field trial data
├── docs/                          # Technical documentation and database schema
│   ├── SYSTEM_ARCHITECTURE.md     # Detailed architecture, math, and data sources
│   ├── RESOURCES_DOSSIER.md       # Complete catalog of all datasets, APIs, and models
│   └── supabase_schema.sql        # Supabase PostgreSQL table definitions
└── models/                        # Serialized ML models
    ├── model.pkl                  # Trained XGBoost yield model
    └── shap_explainer.pkl         # Trained SHAP TreeExplainer
```

---

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/soham0777/hack-core-ps07-agriattribute.git
cd hack-core-ps07-agriattribute
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Linux / macOS:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables (Optional but recommended)
Create a `.env` file in the project root:
```ini
GEMINI_API_KEY=your_gemini_api_key_here
OPENWEATHER_API_KEY=your_openweather_api_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
```
*(Note: If API keys are not provided, the platform automatically switches to cached local telemetry and fallback logic without crashing.)*

### 5. Launch the application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8505`.

---

## Data Sources & Official Citations

All agricultural data in this platform is grounded in official Indian Government publications:
- **Agmarknet (DMI, MoA&FW):** Daily modal wholesale spot prices from state APMCs.
- **Commission for Agricultural Costs & Prices (CACP):** 2024–25 Minimum Support Price schedules.
- **Soil Health Card Scheme (DAC&FW):** 12-parameter soil nutrient benchmarks.
- **India Meteorological Department (IMD Mausam):** Regional rainfall normals and stress thresholds.
- **ICAR-CRIDA:** District Agricultural Contingency Plans for Vidarbha and the Deccan Plateau.
- **SHAP Research Citation:** Lundberg et al., *Nature Machine Intelligence* (2020).

For a complete itemized list of every formula, dataset, and statutory standard, see [`docs/RESOURCES_DOSSIER.md`](./docs/RESOURCES_DOSSIER.md).

---

## The Team

Built with genuine passion for Indian agriculture by **Team 15 BHOOMI**:
- **Soham Kadu** ([@soham0777](https://github.com/soham0777)) — Team Lead & Machine Learning Architecture
- **Bhakti Ajay Kadam** ([@Bhakti2709](https://github.com/Bhakti2709)) — Agronomic Research & UI Design
- **Singireddy Prabhumitrareddy** ([@prabhumitra123-debug](https://github.com/prabhumitra123-debug)) — Backend Engineering & Cloud Database

*Syngenta Biologicals & ANNAM.AI Hack Core 2026 — Problem Statement 07 (Yield Attribution and ROI Predictor)*
