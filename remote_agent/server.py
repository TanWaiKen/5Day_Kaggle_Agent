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

# Remote agent file server setup
REMOTE_FILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "files")
os.makedirs(REMOTE_FILES_DIR, exist_ok=True)

def clean_data_temp(public_url, critical_columns=None):
    """Clean data from public URL and save to remote file server"""
    try:
        # Load data from public URL
        df = pd.read_csv(public_url)
        original_rows = len(df)
        
        # Remove duplicates
        df_clean = df.drop_duplicates()
        duplicates_removed = original_rows - len(df_clean)
        
        # Handle missing values
        if critical_columns is None:
            critical_columns = []
        
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
                        df_clean[column] = df_clean[column].fillna(df_clean[column].median())
                        method = "median"
                    else:
                        df_clean[column] = df_clean[column].fillna(df_clean[column].mode()[0])
                        method = "mode"
                    actions_taken.append({"column": column, "action": "filled", "method": method, "count": int(missing_count)})
                else:
                    df_clean = df_clean.dropna(subset=[column])
                    actions_taken.append({"column": column, "action": "removed_rows", "count": int(missing_count)})
        
        # Save to remote file server
        import uuid
        file_id = str(uuid.uuid4())
        cleaned_filename = f"{file_id}_cleaned.csv"
        cleaned_file_path = os.path.join(REMOTE_FILES_DIR, cleaned_filename)
        df_clean.to_csv(cleaned_file_path, index=False)
        
        # Return public URL for remote file server
        public_url = f"http://localhost:8001/files/{cleaned_filename}"
        
        return {
            "status": "success",
            "public_url": public_url,
            "file_id": file_id,
            "summary": {
                "original_rows": original_rows,
                "final_rows": len(df_clean),
                "duplicates_removed": duplicates_removed,
                "actions_taken": actions_taken
            }
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

# Data Cleaning Agent
data_cleaning_agent = Agent(
    name="data_cleaning_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    description="Data cleaning and temporary file storage",
    instruction="""When given a public_url parameter:
    
    1. Call clean_data_temp(public_url) to process the CSV file
    2. Return the complete result including public_url and summary
    
    The result will be sent back to the calling agent.""",
    tools=[clean_data_temp]
)

if __name__ == "__main__":
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    
    app = to_a2a(data_cleaning_agent, port=8001)
    
    # Mount static file server for public access
    app.mount("/files", StaticFiles(directory=REMOTE_FILES_DIR), name="files")
    
    uvicorn.run(app, host="localhost", port=8001, log_level="info")