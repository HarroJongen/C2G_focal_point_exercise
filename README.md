# C2G_focal_point_exercise
Streamlit app to explore spatial vulnerability to floods, heat stress, and disengagement from nature. Users can adjust exposure, sensitivity, and adaptive capacity weights and instantly visualize how vulnerability patterns change across neighbourhoods using GeoPackage input data.

# Vulnerability Weights Explorer (Streamlit)
Interactive Streamlit app to explore how **component weights** (Exposure, Sensitivity, Adaptive capacity) affect neighbourhood‑level **vulnerability maps** for different hazards using a **GeoPackage** input.

---

## What this app does

- Loads a **GeoPackage** uploaded via the sidebar and reads the `Vulnerability` layer  
- Detects which hazards are available based on required component columns  
- Lets you select a hazard and adjust **Exposure / Sensitivity / Adaptive capacity** weights  
- Automatically normalizes weights over available components  
- Computes a combined vulnerability score:  
  **Vulnerability = Exposure + Sensitivity − Adaptive capacity**
- Visualizes:
  - Component maps (Exposure, Sensitivity, Adaptive capacity)
  - Combined vulnerability map
  - Top 5 most vulnerable neighbourhoods

---

## Requirements

- Python 3.9+
- Packages:
  - `streamlit`
  - `geopandas`
  - `pandas`
  - `numpy`
  - `plotly`

> Installing GeoPandas may require GDAL / GEOS / PROJ system dependencies.

---

## Installation

```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows

pip install streamlit geopandas pandas numpy plotly
