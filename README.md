# DataForge — Local AI Data Analyst 🌿

**A privacy-first CSV analyst powered by open-weight AI running locally.** DataForge helps people inspect activity data, find patterns, build charts, and turn observations into practical offline actions.

Built for the Hacktoberfest 2026 Week 1 theme: **Touch Grass**.

## Why this exists

It is easy to collect data about our days and never turn it into useful action. DataForge makes personal or outdoor-activity datasets easier to understand. For example, a walking, running, hiking, or cycling log can reveal patterns in time outside and activity duration.

## Features

- Upload and inspect CSV files.
- Dataset overview: row/column counts, missing cells, duplicates, dtypes, unique values, and numeric summaries.
- Interactive bar, line, scatter, and histogram charts.
- Ask questions with a local open-weight model through Ollama.
- Export the loaded dataset as CSV.
- Local-first design: CSV processing runs in this app; AI prompts are sent to a local Ollama server rather than a hosted AI API.

## Stack

- Python
- Streamlit
- Pandas
- Plotly
- Ollama (local inference; default model configured as `qwen2.5:3b`)

## Run locally

1. Install Python 3.10 or newer.
2. Create and activate a virtual environment:

   **Windows PowerShell**
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **macOS/Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install Ollama from https://ollama.com/download and start it.
5. Download a model:
   ```bash
   ollama pull qwen2.5:3b
   ```
6. Start DataForge:
   ```bash
   streamlit run app.py
   ```

If Ollama uses another model, change **Local model name** in the sidebar to the model you have installed (`ollama list` shows installed models).

## Demo

For a quick demo, use the included `sample_data/outdoor_activity.csv`, or upload your own CSV. Open **Overview**, create a chart in **Explore chart**, then ask a question in **Ask local AI**.

## Privacy notes

The app reads the uploaded CSV into the local Python process. The AI request contains a compact dataset profile and a small sample of rows, sent to the configured Ollama endpoint. With Ollama running on your own machine, this stays local. Do not point the Ollama URL at an untrusted remote server or upload sensitive data to a shared machine.

## Current limitations

- CSV only; Excel support and robust calculations for arbitrary natural-language questions are future work.
- The LLM receives summary statistics and sample rows, not the entire dataset.
- AI output should be checked against the data before decisions are made.

## Challenge context

This project was created for the Hacktoberfest 2026 Week 1 DEV Challenge. The theme asks builders to help people get away from screens and into the world. DataForge connects data with action by helping users learn from outdoor-activity records and make realistic plans to spend more time outside.

## License

MIT
