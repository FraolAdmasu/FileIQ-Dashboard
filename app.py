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
