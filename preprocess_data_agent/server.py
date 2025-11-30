import os
import uvicorn
import pandas as pd
from io import StringIO
from dotenv import load_dotenv
from google.adk.agents import Agent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.genai import types
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.runners import InMemoryRunner
from google.adk.plugins.logging_plugin import LoggingPlugin

load_dotenv()

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# File-based data transfer - kaggle project level
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS_DIR = os.path.join(PROJECT_ROOT, "uploads")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

print(f"PROJECT_ROOT: {PROJECT_ROOT}")

# Logging setup
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_data_temp(data, critical_columns=None):
    """Clean data and save as temporary file"""
    try:
        # Load data
        df = pd.read_csv(StringIO(data))
        original_rows = len(df)
        
        # Remove duplicates
        df_clean = df.drop_duplicates()
        duplicates_removed = original_rows - len(df_clean)
        
        # Handle missing values
        if critical_columns is None:
            critical_columns = ['customer_id', 'product_id']
        
        actions_taken = []
        for column in df_clean.columns:
            missing_count = df_clean[column].isnull().sum()
            if missing_count == 0:
                continue
                
            if column in critical_columns:
                df_clean = df_clean.dropna(subset=[column])
                actions_taken.append({"column": column, "action": "removed_rows", "count": int(missing_count)})
            else:
                missing_percentage = (missing_count / len(df_clean)) * 100
                if missing_percentage > 5:
                    if pd.api.types.is_numeric_dtype(df_clean[column]):
                        df_clean[column].fillna(df_clean[column].median(), inplace=True)
                        method = "median"
                    else:
                        df_clean[column].fillna(df_clean[column].mode()[0], inplace=True)
                        method = "mode"
                    actions_taken.append({"column": column, "action": "filled", "method": method, "count": int(missing_count)})
                else:
                    df_clean = df_clean.dropna(subset=[column])
                    actions_taken.append({"column": column, "action": "removed_rows", "count": int(missing_count)})
        
        # Save to temp location in results directory
        import uuid
        file_id = str(uuid.uuid4())
        temp_file = os.path.join(RESULTS_DIR, f"{file_id}_temp_cleaned.csv")
        df_clean.to_csv(temp_file, index=False)
        
        # Also return cleaned data for pipeline
        cleaned_data = df_clean.to_csv(index=False)
        
        return {
            "status": "success",
            "temp_file": temp_file,
            "file_id": file_id,
            "cleaned_data": cleaned_data,
            "summary": {
                "original_rows": original_rows,
                "final_rows": len(df_clean),
                "duplicates_removed": duplicates_removed,
                "actions_taken": actions_taken
            },
            "save_message": f"Temporary file saved: {temp_file}"
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

# Data Cleaning Agent
data_cleaning_agent = Agent(
    name="data_cleaning_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    description="Data cleaning and temporary file storage",
    instruction="""Clean CSV data and save as temporary file.
    
    Use clean_data_temp(data, critical_columns) where:
    - data: CSV string
    - critical_columns: List like ['customer_id', 'product_id'] (optional)
    
    This handles: duplicates → missing values → temp save.""",
    tools=[clean_data_temp]
)

if __name__ == "__main__":
    app = to_a2a(data_cleaning_agent, port=8001)
    uvicorn.run(app, host="localhost", port=8001, log_level="info")