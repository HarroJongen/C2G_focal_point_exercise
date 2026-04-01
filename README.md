# C2G_focal_point_exercise
Streamlit app to explore spatial vulnerability to floods, heat stress, and disengagement from nature. Users can adjust exposure, sensitivity, and adaptive capacity weights and instantly visualize how vulnerability patterns change across neighbourhoods using GeoPackage input data.

What this app does
-Loads a GeoPackage uploaded via the sidebar and reads the Vulnerability layer.
-Detects which hazards are available based on required component columns, and lets you pick one hazard at a time.
-Lets you adjust Exposure / Sensitivity / Adaptive capacity weights with sliders and automatically normalizes weights over the available components.
-Computes a combined vulnerability score as:
Vulnerability = Exposure + Sensitivity − Adaptive capacity (with normalized weights).

-Visualizes:
Component maps (Exposure / Sensitivity / Adaptive capacity)
Combined vulnerability map
“Top 5 most vulnerable neighbourhoods” list
