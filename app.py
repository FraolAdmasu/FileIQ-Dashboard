import streamlit as st
import pandas as pd
import plotly.express as px
import os

from utils.file_processing import (
    scan_directory,
    extract_zip,
    format_size,
    cleanup_temp_dir
)

from utils.ui_components import (
    metric_card,
    create_pie_chart,
    create_bar_chart,
    create_line_chart
)

from utils.excel_analysis import generate_summary_stats


# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(
    page_title="File Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ---------------------------
# CSS Loader
# ---------------------------
def load_css():
    try:
        with open("assets/style.css", "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

load_css()


# ---------------------------
# Header
# ---------------------------
st.title("File Intelligence Dashboard")
st.markdown("Analyze your digital universe with professional insights.")


# ---------------------------
# Navigation
# ---------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["File & Folder Analysis", "Data (Excel) Analysis"]
)


# ---------------------------
# SESSION STATE INIT
# ---------------------------
if "scan_path" not in st.session_state:
    st.session_state.scan_path = None


# ---------------------------
# FILE & FOLDER ANALYSIS
# ---------------------------
if page == "File & Folder Analysis":

    st.header("File & Folder Analysis")
    st.markdown("Upload a ZIP file or scan a directory path.")

    col1, col2 = st.columns(2)

    # ZIP Upload (Cloud-safe)
    with col1:
        uploaded_file = st.file_uploader("Upload ZIP file", type=["zip"])

    # Folder Path (Cloud-safe replacement for tkinter)
    with col2:
        folder_path = st.text_input(
            "Or enter folder path (local mode only)",
            placeholder="e.g. C:/Users/You/Desktop/data"
        )

        if st.button("Scan Folder"):
            if folder_path and os.path.exists(folder_path):
                st.session_state.scan_path = folder_path
                st.success(f"Selected: {folder_path}")
            else:
                st.error("Invalid folder path")


    # ---------------------------
    # DATA LOADING
    # ---------------------------
    df = None
    temp_dir = None

    if uploaded_file is not None:
        with st.spinner("Extracting ZIP..."):
            temp_dir = extract_zip(uploaded_file)
            df = scan_directory(temp_dir)

    elif st.session_state.scan_path:
        with st.spinner("Scanning directory..."):
            df = scan_directory(st.session_state.scan_path)


    # ---------------------------
    # DASHBOARD
    # ---------------------------
    if df is not None and not df.empty:

        st.divider()
        st.subheader("Dashboard Overview")

        total_files = len(df)
        total_size = format_size(df["Size Bytes"].sum())
        unique_types = df["Extension"].nunique()

        c1, c2, c3 = st.columns(3)

        with c1:
            metric_card("Total Files", f"{total_files:,}")
        with c2:
            metric_card("Total Size", total_size)
        with c3:
            metric_card("File Types", str(unique_types))

        st.divider()

        # ---------------------------
        # CHARTS
        # ---------------------------
        c1, c2 = st.columns(2)

        with c1:
            type_counts = df["Extension"].value_counts().reset_index()
            type_counts.columns = ["Extension", "Count"]

            top_types = type_counts.head(10)

            if len(type_counts) > 10:
                others = pd.DataFrame({
                    "Extension": ["Other"],
                    "Count": [type_counts["Count"][10:].sum()]
                })
                top_types = pd.concat([top_types, others])

            fig = create_pie_chart(
                top_types["Extension"],
                top_types["Count"],
                "File Type Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            df["Created Date"] = pd.to_datetime(df["Created Date"])
            time_data = df.groupby(df["Created Date"].dt.date).size().reset_index(name="Count")

            fig = create_line_chart(
                time_data,
                "Created Date",
                "Count",
                "Files Created Over Time"
            )
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # ---------------------------
        # LARGEST FILES
        # ---------------------------
        st.subheader("Largest Files")

        largest = df.nlargest(10, "Size Bytes")
        largest["Short Name"] = largest["File Name"].apply(
            lambda x: x[:20] + "..." if len(x) > 20 else x
        )

        fig = create_bar_chart(
            largest,
            "Short Name",
            "Size Bytes",
            "Top 10 Largest Files"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # ---------------------------
        # TABLE VIEW
        # ---------------------------
        st.subheader("Detailed File Viewer")

        search = st.text_input("Search file name")
        types = st.multiselect("Filter type", df["Extension"].unique())

        filtered = df.copy()

        if search:
            filtered = filtered[
                filtered["File Name"].str.contains(search, case=False, na=False)
            ]

        if types:
            filtered = filtered[filtered["Extension"].isin(types)]

        view = filtered[
            ["File Name", "Extension", "Size", "Created Date", "Modified Date", "Folder Path"]
        ]

        st.dataframe(view, use_container_width=True)

        st.download_button(
            "Download CSV",
            view.to_csv(index=False).encode("utf-8"),
            file_name="file_report.csv",
            mime="text/csv"
        )

        if temp_dir:
            cleanup_temp_dir(temp_dir)


# ---------------------------
# EXCEL ANALYSIS
# ---------------------------
elif page == "Data (Excel) Analysis":

    st.header("Data (Excel) Analysis")

    file = st.file_uploader(
        "Upload Excel or CSV",
        type=["xlsx", "xls", "csv"]
    )

    if file is not None:

        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        if df.empty:
            st.warning("Empty dataset")
        else:

            stats, num_cols, cat_cols, date_cols = generate_summary_stats(df)

            st.divider()

            c1, c2, c3 = st.columns(3)

            with c1:
                metric_card("Rows", stats["Total Rows"])
            with c2:
                metric_card("Columns", stats["Total Columns"])
            with c3:
                metric_card("Missing", stats["Missing Values"])

            st.divider()

            st.subheader("Automated Insights")

            # Numerical
            if num_cols:
                for col in num_cols[:2]:
                    fig = px.histogram(df, x=col, title=f"{col} Distribution")
                    st.plotly_chart(fig, use_container_width=True)

            # Categorical
            if cat_cols:
                valid = [c for c in cat_cols if df[c].nunique() < 20]

                for col in valid[:2]:
                    data = df[col].value_counts().reset_index()
                    data.columns = [col, "Count"]

                    fig = px.pie(data, names=col, values="Count", title=col)
                    st.plotly_chart(fig, use_container_width=True)

            st.divider()
            st.dataframe(df.head(100), use_container_width=True)
