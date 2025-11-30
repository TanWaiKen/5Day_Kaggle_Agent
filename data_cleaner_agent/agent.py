from google.adk.agents import Agent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.genai import types
from .data_cleaner import analyze_data, clean_duplicates, handle_missing_values, save_csv

# Configure Model Retry
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

# Data Analysis Agent
data_analyzer_agent = Agent(
    name="data_analyzer_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    description="Specialized agent for data analysis and quality assessment.",
    instruction="""You are a data analysis specialist.
    
    IMPORTANT: All tools only accept CSV data as strings. When users provide data, pass it directly as a string to the tools.
    
    For data analysis requests:
    1. Use `analyze_data(data)` where data is CSV string format
    2. Check the "status" field in the response for errors
    3. Provide detailed insights about data quality, missing values, and column statistics
    4. Recommend cleaning actions based on analysis results
    
    If the tool returns status "error", explain the issue clearly.""",
    tools=[analyze_data],
)

# Duplicate Removal Agent
duplicate_cleaner_agent = Agent(
    name="duplicate_cleaner_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    description="Removes duplicate rows from data.",
    instruction="""Remove duplicate rows from CSV data.
    
    Use `clean_duplicates(data)` where data is CSV string.
    Return the cleaned_data from the result for next step.
    Check status field for errors.""",
    tools=[clean_duplicates],
)

# Missing Values Handler Agent
missing_values_agent = Agent(
    name="missing_values_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    description="Handles missing values in data.",
    instruction="""Handle missing values in CSV data.
    
    Use `handle_missing_values(data, critical_columns)` where:
    - data: CSV string from previous step
    - critical_columns: List of critical columns (ID fields, primary keys)
    
    Return the cleaned_data from the result for next step.
    Check status field for errors.""",
    tools=[handle_missing_values],
)

# CSV Saver Agent
csv_saver_agent = Agent(
    name="csv_saver_agent",
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    description="Saves cleaned data to CSV file.",
    instruction="""Save cleaned CSV data to file.
    
    Use `save_csv(cleaned_data, filename)` where:
    - cleaned_data: CSV string from previous step
    - filename: Output filename (e.g. 'cleaned_data.csv')
    
    Check status field for errors.""",
    tools=[save_csv],
)

# Data Cleaning Pipeline
data_cleaning_pipeline = SequentialAgent(
    name="DataCleaningPipeline",
    sub_agents=[duplicate_cleaner_agent, missing_values_agent, csv_saver_agent],
)

# Root agent
root_agent = SequentialAgent(
    name="CompleteDataPipeline",
    sub_agents=[data_analyzer_agent, data_cleaning_pipeline],
)

