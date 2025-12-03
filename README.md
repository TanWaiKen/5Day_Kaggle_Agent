# AI-Powered Data Cleaning Pipeline

An intelligent data cleaning application built with Google's Agent Development Kit (ADK) that uses specialized AI agents to automatically analyze, clean, and process CSV datasets.

## 🎥 Demo Video

[![AI-Powered Data Cleaning Pipeline Demo](https://img.youtube.com/vi/9Hfk6FJOVPw/0.jpg)](https://youtu.be/9Hfk6FJOVPw)

[Watch the full demo on YouTube](https://youtu.be/9Hfk6FJOVPw)

## Overview

This application leverages multiple AI agents working in sequence to provide comprehensive data cleaning capabilities. Each agent specializes in a specific aspect of data processing, creating an efficient and intelligent pipeline for data preparation tasks.

## Key Features

- **Intelligent Data Analysis**: Automated assessment of data quality, missing values, and column statistics
- **Duplicate Detection & Removal**: Smart identification and elimination of duplicate records
- **Missing Value Handling**: Context-aware strategies for handling missing data based on column criticality
- **Automated CSV Processing**: Seamless input/output handling for CSV files
- **Multi-Agent Architecture**: Specialized agents for different cleaning tasks
- **Error Handling**: Robust error detection and reporting throughout the pipeline

## Architecture

The application uses a distributed multi-agent architecture with public file servers:

### 1. Local Agent (Port 8002)
- Analyzes CSV data and saves to local file server
- Creates public URLs for file access
- Coordinates with remote cleaning agent
- Serves files at `http://localhost:8002/files/`

### 2. Remote Cleaning Agent (Port 8001)
- Downloads files via public URLs
- Performs data cleaning (duplicates, missing values)
- Saves cleaned files to remote file server
- Serves cleaned files at `http://localhost:8001/files/`

### 3. Public File Server Architecture
- Each agent has its own file server
- Files are accessible via public URLs
- No direct file path sharing between agents
- Clean separation of concerns

## Technology Stack

- **Google Agent Development Kit (ADK)**: Multi-agent framework
- **Gemini 2.5 Flash Lite**: Large language model for agent intelligence
- **Pandas**: Data manipulation and analysis
- **Python**: Core programming language

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your Google API credentials in `.env` file

## Running the Application

### Step 1: Start Remote Cleaning Agent
```bash
cd remote_agent
python server.py
```
This starts the remote cleaning service on port 8001.

### Step 2: Start Local Agent
```bash
cd local_agent
python agent.py
```
This starts the local agent service on port 8002.

### Step 3: Start ADK Web Interface
```bash
# From the kaggle project root directory
adk web
```
This starts the web interface to interact with the agents.

## Usage Workflow

1. **Upload CSV Data**: Provide CSV data through the web interface
2. **Data Analysis**: Local agent analyzes and saves to file server
3. **Remote Processing**: File URL sent to remote agent for cleaning
4. **Results**: User receives cleaned file URL for download
5. **File Access**: Both original and cleaned files available via public URLs

## Data Processing Logic

### Missing Value Strategy
- **Critical Columns**: Rows with missing values are removed
- **Non-Critical Columns**: 
  - If >5% missing: Fill with median (numeric) or mode (categorical)
  - If ≤5% missing: Remove rows with missing values

### Duplicate Handling
- Complete row comparison for duplicate detection
- Preserves first occurrence of duplicate records
- Reports total duplicates removed

## Benefits

- **Distributed Architecture**: Separate agents with public file servers
- **Public File Access**: Files accessible via HTTP URLs
- **Automated Processing**: Reduces manual data cleaning effort
- **Scalable**: Handles datasets of various sizes
- **Intelligent**: Context-aware decision making
- **Reliable**: Built-in error handling and validation
- **Modular Design**: Easy to extend and customize
- **Experiment-Friendly**: Public file servers for easy testing

## Use Cases

- Data preprocessing for machine learning projects
- Dataset preparation for analysis and visualization
- Data quality assessment and improvement
- Automated data pipeline integration
- Research data standardization

## File Structure

```
kaggle/
├── local_agent/
│   ├── files/            # Local file server storage
│   ├── .env              # Environment configuration
│   └── agent.py          # Local agent (port 8002)
├── remote_agent/
│   ├── files/            # Remote file server storage
│   ├── .env              # Environment configuration
│   └── server.py         # Remote cleaning agent (port 8001)
├── requirements.txt      # Dependencies
└── README.md            # This file
```

## Public URLs

- **Local Agent Files**: `http://localhost:8002/files/{filename}`
- **Remote Agent Files**: `http://localhost:8001/files/{filename}`
- **Web Interface**: Available after running `adk web`

## Contributing

This application demonstrates the power of multi-agent AI systems for data processing tasks. The modular architecture allows for easy extension and customization of cleaning strategies.