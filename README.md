# AIXpo — AI Data Explorer

A local-first workspace for exploring custom data. Upload a CSV, Excel, or JSON dataset and AIXpo automatically profiles its shape, quality, and numeric measures. Build interactive charts or ask a locally running Ollama model for evidence-based insights.

## Features

- Upload custom CSV, XLSX/XLS, and JSON files.
- Automatic dataset analysis: rows, columns, missing values, duplicates, column health, and numeric summaries.
- Interactive bar, line, scatter, and histogram views.
- Local AI analysis through Ollama.
- Download the current working dataset as CSV.

## Run locally

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
ollama pull qwen2.5:3b
streamlit run app.py
```

Ollama is optional for the dashboard and visualisation features. It is required only for the **Ask AI** tab.

## Privacy

Files are processed in the local Streamlit session. A compact profile and a small sample of rows are sent to the Ollama URL configured in the sidebar; keep it pointed at your local Ollama server for a fully local workflow.
