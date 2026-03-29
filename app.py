import streamlit as st
import pandas as pd
import json

# Set page config
st.set_page_config(
    page_title="File Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    try:
        with open("assets/style.css", "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

load_css()

st.title("File Intelligence Dashboard")
st.markdown("Analyze your digital universe with professional insights.")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["File & Folder Analysis", "Data (Excel) Analysis"])

from utils.file_processing import scan_directory, extract_zip, format_size, cleanup_temp_dir
from utils.ui_components import metric_card, create_pie_chart, create_bar_chart, create_line_chart

if page == "File & Folder Analysis":
    st.header("File & Folder Analysis")
    st.markdown("Upload a ZIP file containing the folder you want to analyze.")

    uploaded_file = st.file_uploader("Upload a folder (as ZIP)", type=["zip"])
    df = None
    temp_dir = None

    if uploaded_file is not None:
        with st.spinner("Extracting ZIP and scanning..."):
            temp_dir = extract_zip(uploaded_file)
            df = scan_directory(temp_dir)

    if df is not None and not df.empty:
        st.divider()
        st.subheader("Dashboard Overview")

        # Calculate KPIs
        total_files = len(df)
        total_size_bytes = df['Size Bytes'].sum()
        total_size_str = format_size(total_size_bytes)
        unique_types = df['Extension'].nunique()

        # Render Metrics
        m1, m2, m3 = st.columns(3)
        with m1:
            metric_card("Total Files", f"{total_files:,}")
        with m2:
            metric_card("Total Size", total_size_str)
        with m3:
            metric_card("File Types", str(unique_types))

        st.divider()

        # Charts section
        c1, c2 = st.columns(2)

        with c1:
            # File type distribution
            type_counts = df['Extension'].value_counts().reset_index()
            type_counts.columns = ['Extension', 'Count']
            top_types = type_counts.head(10)
            if len(type_counts) > 10:
                others = pd.DataFrame({'Extension': ['Other'], 'Count': [type_counts['Count'][10:].sum()]})
                top_types = pd.concat([top_types, others])
            pie_fig = create_pie_chart(top_types['Extension'], top_types['Count'], "File Type Distribution")
            st.plotly_chart(pie_fig, use_container_width=True)

        with c2:
            # Files created over time
            df['Date_Str'] = df['Created Date']
            date_counts = df.groupby('Date_Str').size().reset_index(name='Count')
            date_counts = date_counts.sort_values('Date_Str')
            line_fig = create_line_chart(date_counts, 'Date_Str', 'Count', "Files Created Over Time")
            st.plotly_chart(line_fig, use_container_width=True)

        st.divider()

        # Largest files
        st.subheader("Largest Files")
        largest_df = df.nlargest(10, 'Size Bytes')
        largest_df['Short Name'] = largest_df['File Name'].apply(lambda n: n[:20] + '...' if len(n) > 20 else n)
        bar_fig = create_bar_chart(largest_df, 'Short Name', 'Size Bytes', "Top 10 Largest Files", labels={'Size Bytes': 'Size (Bytes)'})
        st.plotly_chart(bar_fig, use_container_width=True)

        st.divider()

        # Data table with filters
        st.subheader("Detailed File Viewer")

        # Filters
        f1, f2, f3 = st.columns(3)
        with f1:
            search_query = st.text_input("Search by File Name")
        with f2:
            type_filter = st.multiselect("Filter by Type", options=df['Extension'].unique())
        with f3:
            min_date = pd.to_datetime(df['Created Date']).min().date()
            max_date = pd.to_datetime(df['Created Date']).max().date()
            date_range = st.date_input("Filter by Date Range", [min_date, max_date])

        # Apply filters
        filtered_df = df.copy()
        if search_query:
            filtered_df = filtered_df[filtered_df['File Name'].str.contains(search_query, case=False, na=False)]
        if type_filter:
            filtered_df = filtered_df[filtered_df['Extension'].isin(type_filter)]

        if len(date_range) == 2:
            d_start, d_end = date_range
            df_dates = pd.to_datetime(filtered_df['Created Date']).dt.date
            filtered_df = filtered_df[(df_dates >= d_start) & (df_dates <= d_end)]

        display_df = filtered_df[['File Name', 'Extension', 'Size', 'Created Date', 'Modified Date', 'Folder Path']]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Download button
        csv = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Data as CSV",
            data=csv,
            file_name='file_analysis_report.csv',
            mime='text/csv',
        )

        if temp_dir:
            cleanup_temp_dir(temp_dir)

# The "Data (Excel) Analysis" section remains unchanged
