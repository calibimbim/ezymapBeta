import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import io
import zipfile
import tempfile
import os

# Function to load and validate dataset
def load_dataset(uploaded_file):
    try:
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)
        return df
    except Exception as e:
        st.error(f"Error loading dataset: {e}")
        return None

def load_shapefile(files):
    try:
        with tempfile.TemporaryDirectory() as tmpdirname:
            for file in files:
                with open(os.path.join(tmpdirname, file.name), "wb") as f:
                    f.write(file.getbuffer())
            shp_path = next((os.path.join(tmpdirname, f) for f in os.listdir(tmpdirname) if f.endswith('.shp')), None)
            if shp_path:
                gdf = gpd.read_file(shp_path)
                return gdf
            else:
                raise FileNotFoundError("No .shp file found in uploaded files.")
    except Exception as e:
        st.error(f"Error loading shapefile: {e}")
        return None

def main():
    st.title('ezymap')

    with st.sidebar:
        uploaded_files = st.file_uploader("Upload Shapefile Components", type=['shp', 'shx', 'dbf', 'prj'], accept_multiple_files=True)
        uploaded_dataset = st.file_uploader("Upload Dataset (CSV or Excel)", type=['csv', 'xlsx'])

    if uploaded_files and uploaded_dataset:
        gdf = load_shapefile(uploaded_files)
        df = load_dataset(uploaded_dataset)

        if gdf is not None and df is not None:
            with st.sidebar:
                shapefile_field = st.selectbox("Select Matching Field in Shapefile", gdf.columns)
                dataset_field = st.selectbox("Select Matching Field in Dataset", df.columns)
                value_field = st.selectbox("Select Value Field for Coloring", df.columns)
                num_categories = st.slider("Number of Categories", 1, 5)
                cmap_options = plt.colormaps()
                selected_cmap = st.selectbox("Select Color Map", cmap_options, index=cmap_options.index('viridis'))
                border_color = st.color_picker('Pick a border color', '#000000')
                border_width = st.slider('Border Width', 0.0, 3.0, 0.8)
                show_color_bar = st.checkbox("Show Color Bar")
                add_labels = st.checkbox("Add Label")
                if add_labels:
                    label_field = st.selectbox("Select Label Field", gdf.columns)
                    label_size = st.slider("Label Font Size", 5, 18, 8)
                    label_color = st.color_picker("Label Color", '#000000')

            norm = Normalize(vmin=df[value_field].min(), vmax=df[value_field].max())
            fig, ax = plt.subplots()
            ax.set_aspect('equal', adjustable='datalim')
            plt.box(on=None)  # Remove square border
            ax.set_xticks([])  # Remove x-axis tick marks
            ax.set_yticks([])  # Remove y-axis tick marks
            ax.set_xticklabels([])  # Remove x-axis tick labels
            ax.set_yticklabels([])  # Remove y-axis tick labels
            ax.set_axis_off()  # Hide the axis completely

            cmap = plt.get_cmap(selected_cmap, num_categories)

            merged_gdf = gdf.merge(df, left_on=shapefile_field, right_on=dataset_field, how='left')
            merged_gdf.plot(column=value_field, cmap=cmap, norm=norm, linewidth=border_width, ax=ax, edgecolor=border_color)

            if add_labels:
                for idx, row in merged_gdf.iterrows():
                    ax.annotate(text=row[label_field], xy=(row.geometry.centroid.x, row.geometry.centroid.y),
                                horizontalalignment='center', fontsize=label_size, color=label_color)

            if show_color_bar:
                sm = ScalarMappable(norm=norm, cmap=cmap)
                sm.set_array([])
                fig.colorbar(sm, ax=ax)

            st.pyplot(fig)

            # Download PNG
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=300)
            buf.seek(0)
            st.download_button("Download map as PNG", buf, "choropleth_map.png", "image/png")

            # Download SVG
            buf_svg = io.BytesIO()
            fig.savefig(buf_svg, format="svg")
            buf_svg.seek(0)
            st.download_button("Download map as SVG", buf_svg.getvalue(), "choropleth_map.svg", "image/svg+xml")

if __name__ == "__main__":
    main()
