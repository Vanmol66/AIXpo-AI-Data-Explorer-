import io
import json
import requests
import pandas as pd
import plotly.express as px
import streamlit as st
from pathlib import Path
st.set_page_config(page_title="DataForge | Local AI Data Analyst", page_icon="🌿", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.6rem; max-width: 1400px;}
.hero {padding: 1.3rem 1.5rem; border-radius: 18px; background: linear-gradient(120deg,#173f35,#286a54); color: white; margin-bottom: 1rem;}
.hero h1 {margin:0; font-size:2.4rem;}
.hero p {margin:.35rem 0 0 0; opacity:.92;}
div[data-testid="stMetric"] {border:1px solid #d8e4dd; padding:12px; border-radius:12px;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>🌿 DataForge</h1>
  <p>Your local AI data analyst — turn activity data into insights, then take them outside.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Settings")
    ollama_url = st.text_input("Ollama URL", value="http://localhost:11434")
    model = st.text_input("Local model name", value="qwen2.5:3b", help="Use a model installed in Ollama, e.g. qwen2.5:3b or llama3.2:3b.")
    st.caption("Privacy: uploaded files are processed in this app session. AI prompts go to your local Ollama server, not a hosted AI API.")
    st.divider()
    st.markdown("**Quick start**")
    st.code("ollama pull qwen2.5:3b\nstreamlit run app.py", language="bash")

uploaded = st.file_uploader("Upload a CSV file", type=["csv"])
use_sample = st.toggle("Use the included outdoor activity sample", value=True)

if uploaded is not None:
    try:
        df = pd.read_csv(uploaded)
        dataset_name = uploaded.name
    except Exception as e:
        st.error(f"Could not read this CSV: {e}")
        st.stop()
elif use_sample:
    df = pd.read_csv(Path(__file__).parent / "sample_data" / "outdoor_activity.csv")
    dataset_name = "outdoor_activity.csv (sample)"
else:
    st.info("Upload a CSV or turn on the sample dataset to begin.")
    st.stop()

if df.empty:
    st.warning("This dataset has no rows.")
    st.stop()

# Make column names readable in summaries without changing the dataframe itself.
numeric_cols = df.select_dtypes(include="number").columns.tolist()
categorical_cols = df.select_dtypes(exclude="number").columns.tolist()
missing_total = int(df.isna().sum().sum())
duplicate_total = int(df.duplicated().sum())

st.caption(f"Dataset: **{dataset_name}** · Data is analysed locally in Python.")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Rows", f"{len(df):,}")
m2.metric("Columns", f"{len(df.columns):,}")
m3.metric("Missing cells", f"{missing_total:,}")
m4.metric("Duplicate rows", f"{duplicate_total:,}")

tab_overview, tab_chart, tab_ai, tab_data = st.tabs(["📊 Overview", "📈 Explore chart", "🤖 Ask local AI", "🧾 Data preview"])

with tab_overview:
    left, right = st.columns([1.25, 1])
    with left:
        st.subheader("Dataset preview")
        st.dataframe(df.head(12), use_container_width=True, hide_index=True)
    with right:
        st.subheader("Column quality")
        quality = pd.DataFrame({
            "column": df.columns,
            "dtype": [str(t) for t in df.dtypes],
            "missing": [int(v) for v in df.isna().sum().values],
            "missing_%": [round(float(v) / len(df) * 100, 1) for v in df.isna().sum().values],
            "unique_values": [int(df[c].nunique(dropna=True)) for c in df.columns],
        })
        st.dataframe(quality, use_container_width=True, hide_index=True)
    if numeric_cols:
        st.subheader("Numeric summary")
        st.dataframe(df[numeric_cols].describe().T.round(2), use_container_width=True)

with tab_chart:
    st.subheader("Build a quick chart")
    c1, c2, c3 = st.columns(3)
    chart_type = c1.selectbox("Chart type", ["Bar", "Line", "Scatter", "Histogram"])
    x_col = c2.selectbox("X axis", options=list(df.columns), index=0)
    y_options = numeric_cols if numeric_cols else list(df.columns)
    y_col = c3.selectbox("Y axis / value", options=y_options, index=0)
    color_col = st.selectbox("Optional colour grouping", options=["None"] + list(df.columns))
    try:
        if chart_type == "Bar":
            fig = px.bar(df, x=x_col, y=y_col, color=None if color_col == "None" else color_col)
        elif chart_type == "Line":
            fig = px.line(df, x=x_col, y=y_col, color=None if color_col == "None" else color_col, markers=True)
        elif chart_type == "Scatter":
            fig = px.scatter(df, x=x_col, y=y_col, color=None if color_col == "None" else color_col)
        else:
            fig = px.histogram(df, x=y_col, color=None if color_col == "None" else color_col)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not create this chart combination: {e}")

with tab_ai:
    st.subheader("Ask your dataset")
    st.write("Ask a question about the uploaded data. DataForge sends a compact summary and sample rows to your **local** Ollama model.")
    question = st.text_area("Your question", placeholder="Which activity has the highest average duration? What patterns do you notice?", height=90)
    if st.button("Analyse with local AI", type="primary"):
        if not question.strip():
            st.warning("Enter a question first.")
        else:
            profile = {
                "dataset_name": dataset_name,
                "row_count": int(len(df)),
                "columns": [{"name": str(c), "dtype": str(df[c].dtype), "missing": int(df[c].isna().sum()), "unique": int(df[c].nunique(dropna=True))} for c in df.columns],
                "numeric_summary": df[numeric_cols].describe().round(2).replace({float("nan"): None}).to_dict() if numeric_cols else {},
                "categorical_examples": {str(c): [str(v) for v in df[c].dropna().astype(str).unique()[:12]] for c in categorical_cols},
                "sample_rows": df.head(8).astype(object).where(pd.notna(df.head(8)), None).to_dict(orient="records"),
            }
            system_prompt = (
                "You are DataForge, a careful local data analyst. Use only the dataset context provided. "
                "Do not invent values or claim to have calculated something that is not present in the context. "
                "If the question requires a calculation not directly available in the summary/sample, explain that a precise calculation needs to be added and suggest the relevant Pandas operation. "
                "Give a concise answer with: Answer, Evidence, and Next step. "
                "This app supports the Touch Grass theme: when relevant, suggest a practical offline/outdoor action grounded in the data, without forcing it."
            )
            prompt = f"DATASET CONTEXT (JSON):\n{json.dumps(profile, default=str)[:18000]}\n\nUSER QUESTION:\n{question}"
            with st.spinner(f"Contacting local Ollama model '{model}'..."):
                try:
                    response = requests.post(
                        f"{ollama_url.rstrip('/')}/api/chat",
                        json={"model": model, "stream": False, "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ]},
                        timeout=180
                    )
                    response.raise_for_status()
                    answer = response.json().get("message", {}).get("content", "")
                    if answer:
                        st.markdown(answer)
                    else:
                        st.warning("The model returned an empty response.")
                except requests.exceptions.ConnectionError:
                    st.error("Could not connect to Ollama. Install/start Ollama, pull the model, then try again.")
                    st.code("ollama pull qwen2.5:3b\nollama serve", language="bash")
                except requests.exceptions.Timeout:
                    st.error("The local model took too long. Try a smaller model or ask a shorter question.")
                except Exception as e:
                    st.error(f"Local AI request failed: {e}")

with tab_data:
    st.subheader("Full dataset")
    st.dataframe(df, use_container_width=True, hide_index=True)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download current dataset as CSV", data=csv_bytes, file_name="dataforge_export.csv", mime="text/csv")

st.divider()
st.caption("Built for Hacktoberfest 2026 Week 1 · Open-source AI · Local-first data analysis · Touch Grass 🌱")
