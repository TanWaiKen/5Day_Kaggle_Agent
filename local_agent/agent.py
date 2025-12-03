import pandas as pd
import os
from io import StringIO
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
from google.adk.tools import AgentTool
from google.genai import types

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

def validate_path(file_path):
    """Security check for file paths"""
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ALLOWED_DIRS = [os.path.join(PROJECT_ROOT, "uploads"), os.path.join(PROJECT_ROOT, "results")]
    
    abs_path = os.path.abspath(file_path)
    return any(abs_path.startswith(allowed_dir) for allowed_dir in ALLOWED_DIRS)

# Local agent file server setup
LOCAL_FILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "files")
os.makedirs(LOCAL_FILES_DIR, exist_ok=True)

def save_upload_file(data):
    """Save uploaded data to local file server"""
    try:
        import uuid
        
        # Fix column name if needed
        if data.startswith('datacustomer_id'):
            data = data.replace('datacustomer_id', 'customer_id', 1)
        
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_upload.csv"
        upload_file = os.path.join(LOCAL_FILES_DIR, filename)
        
        with open(upload_file, 'w', newline='', encoding='utf-8') as f:
            f.write(data)
        
        # Return public URL for local file server
        public_url = f"http://localhost:8002/files/{filename}"
        
        return {"status": "success", "upload_path": upload_file, "public_url": public_url, "file_id": file_id}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

def analyze_data(data):
    """Analyze CSV data and return analysis results"""
    try:
        # Save data to local file server first
        upload_result = save_upload_file(data)
        if upload_result["status"] != "success":
            return upload_result
        
        # Read data for analysis
        df = pd.read_csv(StringIO(data))
        total_missing = df.isnull().sum().sum()
        duplicates = df.duplicated().sum()
        
        analysis_text = f"""DATA ANALYSIS COMPLETE

Dataset Overview:
- Total rows: {len(df):,}
- Total columns: {len(df.columns)}
- Columns: {', '.join(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}

Data Quality Issues:
- Duplicate rows found: {duplicates:,}
- Total missing values: {total_missing:,}
- Columns with missing data: {len([col for col in df.columns if df[col].isnull().sum() > 0])}

Ready to proceed with data cleaning!"""
        
        return {
            'status': 'success',
            'analysis_text': analysis_text,
            'upload_path': upload_result["upload_path"],
            'public_url': upload_result["public_url"],
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'duplicates': int(duplicates),
            'total_missing': int(total_missing)
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}





remote_data_cleaning_agent = RemoteA2aAgent(
    name="remote_data_cleaning_agent",
    description="Remote data cleaning service",
    agent_card=f"http://localhost:8001{AGENT_CARD_WELL_KNOWN_PATH}",
)

data_pipeline_agent = Agent(
    name="data_pipeline_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    description="Coordinates data analysis, cleaning, and download workflow.",
    instruction="""When user provides CSV data:
    
    1. Call analyze_data(data) to analyze and save the file
    2. Show analysis results to user (do not show upload URL)
    3. Transfer to remote_data_cleaning_agent with the public_url
    4. Show only the cleaned file URL from remote agent to user
    
    The remote agent will access the file via public URL.""",
    tools=[analyze_data],
    sub_agents=[remote_data_cleaning_agent],
)


if __name__ == "__main__":
    from fastapi import FastAPI
    from fastapi.staticfiles import StaticFiles
    from google.adk.a2a.utils.agent_to_a2a import to_a2a
    import uvicorn
    
    app = to_a2a(data_pipeline_agent, port=8002)
    
    # Mount static file server for public access
    app.mount("/files", StaticFiles(directory=LOCAL_FILES_DIR), name="files")
    
    uvicorn.run(app, host="localhost", port=8002, log_level="info")

root_agent = data_pipeline_agent