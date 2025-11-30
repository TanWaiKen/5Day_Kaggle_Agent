import pandas as pd
from io import StringIO

def analyze_data(data):
    """
    Analyze CSV data and return analysis results.

    Args:
        data: CSV data as string

    Returns:
        Dictionary with status and analysis results.
    """
    try:
        df = pd.read_csv(StringIO(data))
    except Exception as e:
        return {"status": "error", "error_message": f"Failed to parse CSV data: {str(e)}"}

    analysis_results = {
        'status': 'success',
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'unique_values': {},
        'missing_values': {},
        'data_types': {}
    }

    for column in df.columns:
        analysis_results['unique_values'][column] = int(df[column].nunique())
        analysis_results['missing_values'][column] = int(df[column].isnull().sum())
        analysis_results['data_types'][column] = str(df[column].dtype)

    return analysis_results

def clean_duplicates(data):
    """
    Remove duplicate rows from CSV data.

    Args:
        data: CSV data as string

    Returns:
        Dictionary with status and cleaned DataFrame info
    """
    try:
        df = pd.read_csv(StringIO(data))
    except Exception as e:
        return {"status": "error", "error_message": f"Failed to parse CSV data: {str(e)}"}

    original_count = len(df)
    cleaned_df = df.drop_duplicates()
    removed_count = original_count - len(cleaned_df)

    return {
        "status": "success",
        "cleaned_data": cleaned_df.to_csv(index=False),
        "removed_duplicates": int(removed_count)
    }
    
def handle_missing_values(data, critical_columns=None):
    """
    Handle missing values for all columns in one operation.

    Args:
        data: CSV data as string
        critical_columns: List of critical column names
        
    Returns:
        Dictionary with status and cleaned DataFrame
    """
    try:
        df = pd.read_csv(StringIO(data))
    except Exception as e:
        return {"status": "error", "error_message": f"Failed to parse CSV data: {str(e)}"}
    
    if critical_columns is None:
        critical_columns = []
    
    df_copy = df.copy()
    actions_taken = []
    
    # Handle each column with missing values
    for column in df.columns:
        missing_count = df_copy[column].isnull().sum()
        if missing_count == 0:
            continue
            
        # Check if column is critical
        if column in critical_columns:
            df_copy = df_copy.dropna(subset=[column])
            actions_taken.append({
                "column": column,
                "action": "removed_rows",
                "reason": "critical_column",
                "removed_rows": int(missing_count)
            })
        else:
            # Non-critical columns - use 5% threshold
            missing_percentage = (missing_count / len(df)) * 100
            
            if missing_percentage > 5:
                if pd.api.types.is_numeric_dtype(df_copy[column]):
                    df_copy[column].fillna(df_copy[column].median(), inplace=True)
                    method = "median"
                else:
                    df_copy[column].fillna(df_copy[column].mode()[0], inplace=True)
                    method = "mode"
                
                actions_taken.append({
                    "column": column,
                    "action": "filled",
                    "filled_values": int(missing_count),
                    "method": method
                })
            else:
                df_copy = df_copy.dropna(subset=[column])
                actions_taken.append({
                    "column": column,
                    "action": "removed_rows",
                    "reason": "low_threshold",
                    "removed_rows": int(missing_count)
                })
    
    return {
        "status": "success",
        "cleaned_data": df_copy.to_csv(index=False),
        "actions_taken": actions_taken
    }

def save_csv(cleaned_data, filename):
    """
    Save cleaned CSV data to file.
    
    Args:
        cleaned_data: CSV data as string
        filename: Output filename
        
    Returns:
        Dictionary with status
    """
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            f.write(cleaned_data)
        return {"status": "success", "message": f"Data saved to {filename}"}
    except Exception as e:
        return {"status": "error", "error_message": f"Failed to save file: {str(e)}"}
    
print("✅ Data cleaning functions created")