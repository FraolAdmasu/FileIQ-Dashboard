import streamlit as st
import pandas as pd
import json

# Set page config
st.set_page_config(
    page_title="File Intelligence Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    try:
        with open("assets/style.css", "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass # In case style.css isn't ready yet

load_css()

st.title("File Intelligence Dashboard")
st.markdown("Analyze your digital universe with professional insights.")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["File & Folder Analysis", "Data (Excel) Analysis"])

import tkinter as tk
from tkinter import filedialog
from utils.file_processing import scan_directory, extract_zip, format_size, cleanup_temp_dir
from utils.ui_components import metric_card, create_pie_chart, create_bar_chart, create_line_chart

def select_folder():
    """Opens a native OS folder dialog to select a directory."""
    root = tk.Tk()
    root.withdraw()
    root.wm_attributes('-topmost', 1)
    folder_path = filedialog.askdirectory(master=root)
    root.destroy()
    return folder_path

if page == "File & Folder Analysis":
    st.header("File & Folder Analysis")
    st.markdown("Upload a ZIP file or select a local folder to generate insights.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader("Upload a ZIP file", type=["zip"])
        
    with col2:
        st.write("Or scan a local folder (Desktop App mode)")
        if st.button("Select Folder to Scan"):
            folder_path = select_folder()
            if folder_path:
                st.session_state['scan_path'] = folder_path
                st.success(f"Selected: {folder_path}")
                
    # Logic to load data
    df = None
    temp_dir = None
    
    if uploaded_file is not None:
        with st.spinner("Extracting ZIP and scanning..."):
            temp_dir = extract_zip(uploaded_file)
            df = scan_directory(temp_dir)
            
    elif 'scan_path' in st.session_state and st.session_state['scan_path']:
        with st.spinner("Scanning directory..."):
            df = scan_directory(st.session_state['scan_path'])
            
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
            # Limit to top 10
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
            # Sort by date
            date_counts = date_counts.sort_values('Date_Str')
            # If huge range, this might be crowded but Plotly handles it
            line_fig = create_line_chart(date_counts, 'Date_Str', 'Count', "Files Created Over Time")
            st.plotly_chart(line_fig, use_container_width=True)
            
        st.divider()
        
        # Largest files
        st.subheader("Largest Files")
        largest_df = df.nlargest(10, 'Size Bytes')
        # Create a truncated name for chart labels
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
            # Date filter (extract min and max dates)
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
            
        # Display table, drop internal sort columns
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
            
elif page == "Data (Excel) Analysis":
    st.header("Data (Excel) Analysis")
    st.markdown("Upload Excel files to view auto-generated insights.")
    
    excel_file = st.file_uploader("Upload an Excel file (.xlsx, .xls, .csv)", type=["xlsx", "xls", "csv"])
    
    if excel_file is not None:
        try:
            with st.spinner("Analyzing data..."):
                if excel_file.name.endswith(".csv"):
                    df = pd.read_csv(excel_file)
                else:
                    df = pd.read_excel(excel_file)
                    
            if df.empty:
                st.warning("The uploaded file is empty.")
            else:
                st.divider()
                st.subheader("Data Overview")
                
                from utils.excel_analysis import generate_summary_stats
                stats, num_cols, cat_cols, date_cols = generate_summary_stats(df)
                
                # Render Metrics
                m1, m2, m3 = st.columns(3)
                with m1:
                    metric_card("Total Rows", stats["Total Rows"])
                with m2:
                    metric_card("Total Columns", stats["Total Columns"])
                with m3:
                    metric_card("Missing Values", stats["Missing Values"])
                    
                m4, m5, m6 = st.columns(3)
                with m4:
                    metric_card("Number Columns", stats["Numerical Columns"])
                with m5:
                    metric_card("Text Columns", stats["Categorical Columns"])
                with m6:
                    metric_card("Date Columns", stats["Date Columns"])
                
                st.divider()
                
                # Automated Insights
                st.subheader("Automated Insights / Distributions")
                
                if num_cols:
                    st.markdown("#### Numerical Distributions")
                    # Try to pick max 2 numerical cols for histograms
                    cols_to_plot = num_cols[:2]
                    c1, c2 = st.columns(len(cols_to_plot) if len(cols_to_plot) > 0 else 1)
                    columns_ui = [c1, c2]
                    for i, col in enumerate(cols_to_plot):
                        with columns_ui[i]:
                            fig = px.histogram(df, x=col, title=f"Distribution of {col}")
                            fig.update_layout(margin=dict(t=40, b=0, l=0, r=0), font=dict(family="Inter, sans-serif"))
                            fig.update_traces(marker_color='#8b5cf6', opacity=0.8)
                            st.plotly_chart(fig, use_container_width=True)
                
                if cat_cols:
                    st.markdown("#### Categorical Breakdowns")
                    # Pick categorical columns with reasonable unique values (not IDs)
                    valid_cat = [c for c in cat_cols if df[c].nunique() < 20]
                    cols_to_plot = valid_cat[:2]
                    
                    if cols_to_plot:
                        c1, c2 = st.columns(len(cols_to_plot))
                        columns_ui = [c1, c2]
                        for i, col in enumerate(cols_to_plot):
                            with columns_ui[i]:
                                counts = df[col].value_counts().reset_index()
                                counts.columns = [col, 'Count']
                                fig = create_pie_chart(counts[col], counts['Count'], f"Breakdown of {col}")
                                st.plotly_chart(fig, use_container_width=True)
                                
                st.divider()
                st.subheader("Data Preview")
                st.dataframe(df.head(100), use_container_width=True)
                
        except Exception as e:
            st.error(f"Error reading the file: {e}")
