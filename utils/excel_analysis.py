import pandas as pd

def generate_summary_stats(df: pd.DataFrame):
    """
    Generates summary statistics for a given pandas DataFrame.
    """
    # Basic shape
    num_rows = df.shape[0]
    num_cols = df.shape[1]
    
    # Missing values
    missing_vals = df.isnull().sum()
    total_missing = missing_vals.sum()
    
    # Identify column types
    numerical_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    date_cols = df.select_dtypes(include=['datetime']).columns.tolist()
    
    stats = {
        "Total Rows": f"{num_rows:,}",
        "Total Columns": str(num_cols),
        "Missing Values": f"{total_missing:,}",
        "Numerical Columns": str(len(numerical_cols)),
        "Categorical Columns": str(len(categorical_cols)),
        "Date Columns": str(len(date_cols))
    }
    
    return stats, numerical_cols, categorical_cols, date_cols
