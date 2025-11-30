import pandas as pd
import uuid
import os
import requests
from io import StringIO
from google.adk.agents import Agent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.adk.agents.remote_a2a_agent import (
    RemoteA2aAgent,
    AGENT_CARD_WELL_KNOWN_PATH,
)
from google.genai import types

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

def analyze_data(data):
    """Analyze CSV data and return analysis results"""
    try:
        df = pd.read_csv(StringIO(data))
        
        # Calculate statistics
        total_missing = df.isnull().sum().sum()
        duplicates = df.duplicated().sum()
        
        # Create human-readable analysis
        analysis_text = f"""📊 DATA ANALYSIS COMPLETE

📈 Dataset Overview:
• Total rows: {len(df):,}
• Total columns: {len(df.columns)}
• Columns: {', '.join(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}

🔍 Data Quality Issues:
• Duplicate rows found: {duplicates:,}
• Total missing values: {total_missing:,}
• Columns with missing data: {len([col for col in df.columns if df[col].isnull().sum() > 0])}

🛠️ Cleaning Plan:
• Will remove {duplicates} duplicate rows
• Critical columns (customer_id, product_id): Remove rows if missing
• Other columns: Fill with median/mode if >5% missing, otherwise remove rows

Ready to proceed with data cleaning!"""
        
        analysis_results = {
            'status': 'success',
            'analysis_text': analysis_text,
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'duplicates': int(duplicates),
            'total_missing': int(total_missing),
            'unique_values': {},
            'missing_values': {},
            'data_types': {}
        }
        for column in df.columns:
            analysis_results['unique_values'][column] = int(df[column].nunique())
            analysis_results['missing_values'][column] = int(df[column].isnull().sum())
            analysis_results['data_types'][column] = str(df[column].dtype)
        return analysis_results
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

# Create RemoteA2aAgent for data cleaning service
remote_data_cleaning_agent = RemoteA2aAgent(
    name="remote_data_cleaning_agent",
    description="Remote data cleaning service that handles duplicates and missing values.",
    agent_card=f"http://localhost:8001{AGENT_CARD_WELL_KNOWN_PATH}",
)

print("✅ Remote Data Cleaning Agent proxy created!")
print(f"   Connected to: http://localhost:8001")
print(f"   Agent card: http://localhost:8001{AGENT_CARD_WELL_KNOWN_PATH}")
print("   Ready for data cleaning pipeline!")

def explain_and_ask_approval(cleaning_log):
    """Explain results and ask user for save approval"""
    try:
        if not cleaning_log or cleaning_log.get("status") != "success":
            return {"status": "error", "error_message": "No valid cleaning results to explain"}
        
        summary = cleaning_log.get("summary", {})
        
        explanation = f"""🎉 DATA CLEANING COMPLETED!

📈 SUMMARY:
• Original rows: {summary.get('original_rows', 0):,}
• Final rows: {summary.get('final_rows', 0):,}
• Duplicates removed: {summary.get('duplicates_removed', 0):,}

🔧 ACTIONS TAKEN:"""
        
        actions = summary.get("actions_taken", [])
        for action in actions:
            if action["action"] == "filled":
                explanation += f"\n• {action['column']}: Filled {action['count']} missing values with {action['method']}"
            elif action["action"] == "removed_rows":
                explanation += f"\n• {action['column']}: Removed {action['count']} rows ({action.get('reason', 'missing data')})"
        
        explanation += "\n\n❓ Do you want to save this cleaned data? (yes/no)"
        
        return {
            "status": "success",
            "explanation": explanation,
            "temp_file": cleaning_log.get("temp_file", ""),
            "file_id": cleaning_log.get("file_id", "")
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

def save_final_file(temp_file, file_id):
    """Save temp file to final location"""
    try:
        if not os.path.exists(temp_file):
            return {"status": "error", "error_message": "Temp file not found"}
        
        PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
        os.makedirs(RESULTS_DIR, exist_ok=True)
        
        final_file = os.path.join(RESULTS_DIR, f"{file_id}_cleaned.csv")
        df = pd.read_csv(temp_file)
        df.to_csv(final_file, index=False)
        
        # Clean up temp file
        os.remove(temp_file)
        
        return {"status": "success", "message": f"File saved to {final_file}"}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

def clear_cache(temp_file):
    """Clear temporary files"""
    try:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return {"status": "success", "message": "Cache cleared"}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

# Data Analysis Agent
data_analyzer_agent = Agent(
    name="data_analyzer_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    description="Specialized agent for data analysis and quality assessment.",
    instruction="""You are a data analysis specialist.
    
    Use analyze_data(data) where data is CSV string format.
    Provide detailed insights about data quality, missing values, and column statistics.
    Check the "status" field in the response for errors.""",
    tools=[analyze_data],
)

# Main Data Pipeline Agent that uses remote cleaning service
data_pipeline_agent = Agent(
    name="data_pipeline_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    description="Coordinates data analysis, cleaning, and user approval workflow.",
    instruction="""You coordinate the data cleaning pipeline:
    
    1. First analyze the data using analyze_data()
    2. Then ask the remote_data_cleaning_agent to clean the data
    3. Explain results and ask for approval using explain_and_ask_approval()
    4. If user says 'yes': use save_final_file(temp_file, file_id)
    5. If user says 'no': use clear_cache(temp_file)
    
    Always check status fields for errors.""",
    tools=[analyze_data, explain_and_ask_approval, save_final_file, clear_cache],
    sub_agents=[remote_data_cleaning_agent],
)

# Root agent - simplified with RemoteA2aAgent
root_agent = data_pipeline_agent

print("✅ Data Cleaning Pipeline created!")
print("   Model: gemini-2.5-flash-lite")
print("   Sub-agents: 1 (remote Data Cleaning Agent via A2A)")
print("   Ready to process CSV data!")