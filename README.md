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

The application uses a distributed agent architecture with RemoteA2aAgent for inter-service communication:

### 1. Data Pipeline Agent (Main Coordinator)
- Orchestrates the complete data cleaning workflow
- Analyzes CSV data structure and quality
- Coordinates with remote cleaning service
- Manages user approval workflow

### 2. Remote Data Cleaning Agent (Port 8001)
- Handles duplicate detection and removal
- Implements intelligent missing value strategies
- Processes critical columns (customer_id, product_id)
- Uses statistical methods (median/mode) for non-critical columns
- Applies 5% threshold rule for decision making

### 3. User Approval Workflow
- Explains cleaning results to user
- Asks for save confirmation
- Saves to results directory if approved
- Clears cache if declined

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

## Usage

The application processes CSV data through a coordinated pipeline:

1. **Data Analysis**: Analyzes CSV data quality and structure
2. **Remote Cleaning**: Sends data to remote cleaning service (port 8001)
3. **Results Explanation**: Shows cleaning summary and asks for approval
4. **User Decision**: Save to results/ directory or clear cache
5. **File Management**: Automatic cleanup of temporary files

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

- **Distributed Architecture**: RemoteA2aAgent enables service separation
- **User Control**: Approval workflow before saving cleaned data
- **Automated Processing**: Reduces manual data cleaning effort
- **Consistent Results**: Standardized cleaning procedures
- **Scalable**: Handles datasets of various sizes
- **Intelligent**: Context-aware decision making
- **Reliable**: Built-in error handling and validation
- **Cache Management**: Automatic cleanup of temporary files

## Use Cases

- Data preprocessing for machine learning projects
- Dataset preparation for analysis and visualization
- Data quality assessment and improvement
- Automated data pipeline integration
- Research data standardization

## File Structure

```
kaggle/
├── data_cleaner_agent/
│   └── agent.py          # Main pipeline coordinator with RemoteA2aAgent
├── preprocess_data_agent/
│   └── server.py         # Remote cleaning service (port 8001)
├── uploads/              # Temporary upload storage
├── results/              # Final cleaned data output
├── requirements.txt      # Dependencies
└── README.md            # This file
```

## Contributing

This application demonstrates the power of multi-agent AI systems for data processing tasks. The modular architecture allows for easy extension and customization of cleaning strategies.