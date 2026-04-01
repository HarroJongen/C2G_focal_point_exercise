import streamlit as st
import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.express as px
from pathlib import Path
import tempfile
import shutil

st.set_page_config(layout="wide")
st.title("Vulnerability weights exercise")

COMPONENT_INDICATORS = {
    "Floods": {
        "Exposure": ["Average flood depth"],
        "Sensitivity": ["People below 6 or over 65 years", "Critical infrastructure"],
        "Adaptive capacity": ["Household purchasing power", "Average distance to a hospital"],
    },
    "Heat": {
        "Exposure": [
            "Number of hours above 30 degrees per year",
            "Number of nights exceeding 20 degrees per year",
        ],
        "Sensitivity": ["People below 6 or over 65 years", "Average distance to a hospital"],
        "Adaptive capacity": ["Household purchasing power", "People over 65 years living alone"],
    },
    "Disengagements from nature": {
        "Exposure": ["Distance to green"],
        "Sensitivity": [
            "Population density",
            "Large green area per person",
            "Cultural ecosystem services from green",
        ],
        "Adaptive capacity": ["Landscape diversity", "Green diversity"],
    },
}

@st.cache_data
def load_layer(path, layer):
    gdf = gpd.read_file(path, layer=layer)
    if gdf.crs is None:
        raise ValueError("Layer has no CRS. Please set it in the GeoPackage.")
    return gdf.to_crs(4326)

def ensure_local_path(uploaded_file):
    if uploaded_file is None:
        return None
    suffix = Path(uploaded_file.name).suffix
    tmpdir = tempfile.mkdtemp(prefix="st_gpkg_")
    tmp_path = Path(tmpdir) / f"uploaded{suffix}"
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(uploaded_file, f)
    return str(tmp_path)

def transparentify(fig):
    fig.update_geos(
        projection_scale=1,          # keep correct scale
        fitbounds="locations",
        visible=False,
        showcountries=False,
        showcoastlines=False,
        showland=False,
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend_title_text="",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.05,
            xanchor="center",
            x=0.5,
            entrywidth=80,
            entrywidthmode="pixels",
            itemsizing="constant",
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
            borderwidth=1,
            font=dict(size=14),

        ),
    )
    return fig


def classify_series(s, labels, invert=False):
    x = pd.to_numeric(s, errors="coerce")
    if invert:
        x = -x
    try:
        cats = pd.qcut(x, q=5, labels=labels, duplicates="drop")
        if hasattr(cats, "cat") and len(cats.cat.categories) == len(labels):
            return pd.Categorical(cats, categories=labels, ordered=True)
    except Exception:
        pass
    if not np.isfinite(x).any() or x.min() == x.max():
        mid = labels[len(labels)//2]
        return pd.Categorical([mid]*len(x), categories=labels, ordered=True)
    bins = np.linspace(x.min(), x.max(), 6)
    cats = pd.cut(x, bins=bins, labels=labels, include_lowest=True, duplicates="drop")
    return pd.Categorical(cats, categories=labels, ordered=True)


reds5 = {
    0: "#fee5d9",
    1: "#fcae91",
    2: "#fb6a4a",
    3: "#de2d26",
    4: "#a50f15",
}

def make_color_map(labels):
    return {lbl: reds5[i] for i, lbl in enumerate(labels)}

def available_indicators(gdf, indicators):
    return [c for c in indicators if c in gdf.columns]

up = st.sidebar.file_uploader("Upload a GeoPackage", type=["gpkg"])
gpkg_path = ensure_local_path(up) if up else None

if not gpkg_path:
    st.warning("Please upload a GeoPackage to continue.")
    st.stop()

try:
    gdf = load_layer(gpkg_path, "Vulnerability")
except Exception as e:
    st.error(f"Geopackage not found or format not recognized: {e}")
    st.stop()

HAZARD_COLUMNS = {
    "Floods": [
        "Exposure for floods",
        "Sensitivity for floods",
        "Adaptive capacity for floods",
    ],
    "Heat": [
        "Exposure for heat",
        "Sensitivity for heat",
        "Adaptive capacity for heat",
    ],
    "Disengagement from nature": [
        "Exposure for disengagement from nature",
        "Sensitivity for disengagement from nature",
        "Adaptive capacity for disengagement from nature",
    ],
}

available_hazards, missing_by_hazard = [], {}
for hz, cols in HAZARD_COLUMNS.items():
    miss = [c for c in cols if c not in gdf.columns]
    if len(miss) == 0:
        available_hazards.append(hz)
    else:
        missing_by_hazard[hz] = miss

st.sidebar.header("Hazard & component weights")

if not available_hazards:
    st.warning(
        "No complete hazard found in the uploaded layer. "
        "The layer 'Vulnerability' must contain Exposure, Sensitivity, and Adaptive capacity for at least one hazard."
    )
    with st.expander("Missing columns per hazard"):
        for hz, miss in missing_by_hazard.items():
            st.write(f"**{hz}** missing: {miss}")
    st.stop()

hazard = st.sidebar.selectbox("Select vulnerability type", options=available_hazards, index=0)

exposure_w = st.sidebar.slider("Exposure", 0.0, 1.0, 0.33, 0.01)
sensitivity_w = st.sidebar.slider("Sensitivity ", 0.0, 1.0, 0.33, 0.01)
adaptive_w = st.sidebar.slider("Adaptive capacity", 0.0, 1.0, 0.34, 0.01)

gdf_vuln = gdf.copy()
exp_col, sen_col, ada_col = HAZARD_COLUMNS[hazard]
gdf_vuln["Exposure"] = gdf_vuln[exp_col]
gdf_vuln["Sensitivity"] = gdf_vuln[sen_col]
gdf_vuln["Adaptive"] = gdf_vuln[ada_col]

weights = {"Exposure": exposure_w, "Sensitivity": sensitivity_w, "Adaptive": adaptive_w}
available = {k: (not gdf_vuln[k].isna().all()) for k in ["Exposure", "Sensitivity", "Adaptive"]}
w_sum_avail = sum(weights[k] for k, ok in available.items() if ok)
if w_sum_avail == 0:
    cnt = sum(available.values())
    w_norm = {k: (1.0 / cnt if available[k] else 0.0) if cnt > 0 else 0.0 for k in weights}
else:
    w_norm = {k: (weights[k] / w_sum_avail if available[k] else 0.0) for k in weights}

gdf_vuln["Vulnerability"] = (
    w_norm["Exposure"] * gdf_vuln["Exposure"]
    + w_norm["Sensitivity"] * gdf_vuln["Sensitivity"]
    - w_norm["Adaptive"] * gdf_vuln["Adaptive"]
)

st.sidebar.markdown(
    "**Weights:**  \n"
    f"- Exposure: {w_norm['Exposure']:.2f}  \n"
    f"- Sensitivity: {w_norm['Sensitivity']:.2f}  \n"
    f"- Adaptive capacity: {w_norm['Adaptive']:.2f}"
)


with st.sidebar:
    st.markdown("### Indicators used")
    comps = COMPONENT_INDICATORS[hazard]

    for comp, indicators in comps.items():
        avail = [c for c in indicators if c in gdf.columns]
        if avail:
            st.markdown(f"**{comp}**")
            for col in avail:
                st.markdown(f"- {col}")


gdf_plot = gdf_vuln.reset_index(drop=True).copy()
if "name" not in gdf_plot.columns:
    gdf_plot["name"] = np.arange(len(gdf_plot))
gdf_plot["__pid__"] = gdf_plot.index.astype(str)
geojson = gdf_plot.set_index("__pid__").geometry.__geo_interface__

labels_vuln = ["Least vulnerable", "Less vulnerable", "Vulnerable", "More vulnerable", "Most vulnerable"]
labels_expo = ["Least exposed", "Less exposed", "Exposed", "More exposed", "Most exposed"]
labels_sens = ["Least sensitive", "Less sensitive", "Sensitive", "More sensitive", "Most sensitive"]
labels_adap = ["Highest capacity", "Higher capacity", "Capacity", "Lower capacity", "Lowest capacity"]

cmap_vuln = make_color_map(labels_vuln)
cmap_expo = make_color_map(labels_expo)
cmap_sens = make_color_map(labels_sens)
cmap_adap = make_color_map(labels_adap)

gdf_plot["Vuln_class"] = classify_series(gdf_plot["Vulnerability"], labels_vuln, invert=False)
gdf_plot["Exposure_class"] = classify_series(gdf_plot["Exposure"], labels_expo, invert=False)
gdf_plot["Sensitivity_class"] = classify_series(gdf_plot["Sensitivity"], labels_sens, invert=False)
gdf_plot["Adaptive_class"] = classify_series(gdf_plot["Adaptive"], labels_adap, invert=True)

left, right = st.columns([0.5, 1], gap="small")

with left:
    st.subheader("Components")

    figE = px.choropleth(
        gdf_plot,
        geojson=geojson,
        locations="__pid__",
        color="Exposure_class",
        category_orders={"Exposure_class": labels_expo},
        color_discrete_map=cmap_expo,
        hover_data={"name": True, "Exposure_class": True},
    )
    figE.update_traces(marker_line_color="rgba(0,0,0,0)", marker_line_width=0)
    st.plotly_chart(transparentify(figE), use_container_width=True)

    figS = px.choropleth(
        gdf_plot,
        geojson=geojson,
        locations="__pid__",
        color="Sensitivity_class",
        category_orders={"Sensitivity_class": labels_sens},
        color_discrete_map=cmap_sens,
        hover_data={"name": True, "Sensitivity_class": True},
    )
    figS.update_traces(marker_line_color="rgba(0,0,0,0)", marker_line_width=0)
    st.plotly_chart(transparentify(figS), use_container_width=True)
    

    figA = px.choropleth(
        gdf_plot,
        geojson=geojson,
        locations="__pid__",
        color="Adaptive_class",
        category_orders={"Adaptive_class": labels_adap},
        color_discrete_map=cmap_adap,
        hover_data={"name": True, "Adaptive_class": True},
    )
    figA.update_traces(marker_line_color="rgba(0,0,0,0)", marker_line_width=0)
    st.plotly_chart(transparentify(figA), use_container_width=True)

with right:
    st.subheader("Vulnerability (exposure + sensitivity − adaptive capacity)")
    figV = px.choropleth(
        gdf_plot,
        geojson=geojson,
        locations="__pid__",
        color="Vuln_class",
        category_orders={"Vuln_class": labels_vuln},
        color_discrete_map=cmap_vuln,
        hover_data={"name": True, "Vuln_class": True},
    )
    figV.update_traces(marker_line_color="rgba(0,0,0,0)", marker_line_width=0)
    st.plotly_chart(transparentify(figV), use_container_width=True)

    top_names = (
        gdf_plot.sort_values("Vulnerability", ascending=False)
        .dropna(subset=["Vulnerability"])
        .loc[:, ["name"]]
        .drop_duplicates(subset=["name"])
        .head(5)["name"]
        .astype(str)
        .tolist()
    )
    st.subheader("5 most vulnerable neighbourhoods")
    st.markdown("\n".join([f"- {n}" for n in top_names]))