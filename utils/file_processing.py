import os
import zipfile
import tempfile
import pandas as pd
from pathlib import Path
import datetime
import shutil

def format_size(size_bytes):
    """Format bytes into a human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def extract_zip(uploaded_file):
    """
    Extracts an uploaded zip file into a temporary directory 
    and returns the path to that directory.
    """
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(uploaded_file, "r") as zip_ref:
        zip_ref.extractall(temp_dir)
    return temp_dir

def scan_directory(directory_path: str) -> pd.DataFrame:
    """
    Recursively scans a directory and extracts file metadata.
    Returns a pandas DataFrame.
    """
    file_data = []
    
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                stat = os.stat(file_path)
                
                # Get relative path for cleaner display
                rel_path = os.path.relpath(file_path, directory_path)
                folder_path = os.path.dirname(rel_path)
                if not folder_path:
                    folder_path = "/"
                
                # Determine extension
                _, ext = os.path.splitext(file)
                ext = ext.lower() if ext else "unknown"
                
                # Create and modified dates
                created = datetime.datetime.fromtimestamp(stat.st_ctime)
                modified = datetime.datetime.fromtimestamp(stat.st_mtime)
                
                file_data.append({
                    "File Name": file,
                    "Extension": ext,
                    "Size Bytes": stat.st_size,
                    "Size": format_size(stat.st_size),
                    "Created Date": created.strftime("%Y-%m-%d"),
                    "Modified Date": modified.strftime("%Y-%m-%d"),
                    "Folder Path": folder_path,
                    "Full Path": file_path
                })
            except Exception as e:
                # Skip files we can't access
                print(f"Error accessing {file_path}: {e}")
                continue
                
    df = pd.DataFrame(file_data)
    return df

def cleanup_temp_dir(temp_dir):
    """Removes the temporary directory after processing is complete."""
    if temp_dir and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)
