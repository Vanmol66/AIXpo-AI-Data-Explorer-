import io
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(page_title="AIXpo | AI Data Explorer", page_icon="AI", layout="wide")

st.markdown("""<style>
.block-container{max-width:1440px;padding:1.5rem 2rem 2.5rem}.hero{padding:2rem;border-radius:22px;color:#fff!important;background:radial-gradient(circle at 88% 15%,#4f46e5 0,transparent 30%),linear-gradient(120deg,#0b1220,#172554);margin-bottom:1.2rem}.hero *{color:inherit!important}.hero h1{font-size:2.7rem;margin:0;letter-spacing:-.06em}.hero p{font-size:1.04rem;margin:.55rem 0 0;color:#cbd5e1!important}.eyebrow{text-transform:uppercase;letter-spacing:.14em;color:#a5b4fc!important;font-size:.72rem;font-weight:700}[data-testid="stSidebar"]{background:#101827}[data-testid="stSidebar"] *{color:#e8eefb}div[data-testid="stMetric"]{padding:1rem;border:1px solid #e2e8f0;border-radius:14px;background:#fff!important;box-shadow:0 2px 10px rgba(15,23,42,.04)}div[data-testid="stMetric"] *{color:#0f172a!important}.note,.insight{padding:1rem 1.1rem;background:#f8fafc!important;border:1px solid #e2e8f0;border-radius:12px;color:#0f172a!important}.note *,.insight *{color:#0f172a!important}.note{border-left:3px solid #6366f1;background:#eef2ff!important}.insight{min-height:96px}.insight strong{display:block;margin-bottom:.25rem}.route-title{margin-top:.2rem}
</style>""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def read_dataset(file_bytes, file_name):
    stream, suffix = io.BytesIO(file_bytes), Path(file_name).suffix.lower()
    if suffix == ".csv": return pd.read_csv(stream)
    if suffix in {".xlsx", ".xls"}: return pd.read_excel(stream)
    if suffix == ".json": return pd.read_json(stream)
    raise ValueError("Supported file types are CSV, Excel, and JSON.")


def get_dataset():
    if "dataset" not in st.session_state:
        st.info("Upload a dataset first to use this area.")
        st.page_link("app.py", label="Go to Upload", icon="⬆️")
        st.stop()
    return st.session_state.dataset, st.session_state.dataset_name


def get_profile(data):
    numeric = data.select_dtypes(include="number").columns.tolist()
    quality = pd.DataFrame({"Column": data.columns.astype(str), "Type": [str(t) for t in data.dtypes], "Missing": [int(data[c].isna().sum()) for c in data.columns], "Unique values": [int(data[c].nunique(dropna=True)) for c in data.columns]})
    return numeric, int(data.isna().sum().sum()), int(data.duplicated().sum()), quality


def page_hero(title, subtitle):
    st.markdown(f"<section class='hero'><div class='eyebrow'>AIXpo · AI Data Explorer</div><h1>{title}</h1><p>{subtitle}</p></section>", unsafe_allow_html=True)
    route_buttons()


def route_buttons():
    """Show an always-visible route switcher in the main content area."""
    labels = [("Upload", "⬆️"), ("Overview", "📊"), ("Explore", "📈"), ("Ask AI", "✨"), ("Data", "🗂️")]
    columns = st.columns(len(labels))
    for column, (label, icon) in zip(columns, labels):
        with column:
            if st.button(f"{icon} {label}", key=f"route_{label}", use_container_width=True):
                st.switch_page(ROUTES[label])
    st.divider()


def upload_page():
    page_hero("Bring your data to life", "Upload a file to generate an instant profile, explore visual patterns, and ask focused questions.")
    uploaded = st.file_uploader("Drop in your dataset", type=["csv", "xlsx", "xls", "json"], help="CSV, Excel, and JSON are supported.")
    c1, c2 = st.columns([1, 3])
    with c1:
        use_demo = st.button("Load demo dataset")
    if uploaded:
        try:
            st.session_state.dataset = read_dataset(uploaded.getvalue(), uploaded.name)
            st.session_state.dataset_name = uploaded.name
            st.success(f"{uploaded.name} is ready for analysis.")
        except Exception as error:
            st.error(f"We could not read this file: {error}")
            return
    elif use_demo:
        st.session_state.dataset = pd.read_csv(Path(__file__).parent / "sample_data" / "outdoor_activity.csv")
        st.session_state.dataset_name = "outdoor_activity.csv — demo"
        st.success("Demo dataset is ready for analysis.")
    st.markdown("<div class='note'><strong>How it works</strong><br>1. Upload your dataset here. 2. Review its quality in Overview. 3. Explore charts or ask local AI questions from the navigation.</div>", unsafe_allow_html=True)
    if "dataset" in st.session_state:
        data, name = get_dataset()
        st.subheader("Current dataset")
        st.write(f"**{name}** · {len(data):,} rows · {len(data.columns):,} columns")
        st.dataframe(data.head(5), use_container_width=True, hide_index=True)


def overview_page():
    data, name = get_dataset(); numeric, missing, duplicates, quality = get_profile(data)
    page_hero("Dataset overview", f"Quality and structure report for {name}.")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Rows", f"{len(data):,}"); m2.metric("Columns", len(data.columns)); m3.metric("Missing values", f"{missing:,}"); m4.metric("Duplicate rows", f"{duplicates:,}")
    left, right = st.columns([1.35, 1])
    with left:
        st.subheader("Your data at a glance")
        st.dataframe(data.head(10), use_container_width=True, hide_index=True)
    with right:
        st.subheader("Automatic analysis")
        st.markdown(f"<div class='insight'><strong>Data completeness</strong>{missing:,} missing values across {len(data.columns):,} columns.</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='insight'><strong>Data consistency</strong>{duplicates:,} duplicate records detected.</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='insight'><strong>Available measures</strong>{len(numeric):,} numeric columns are ready for analysis.</div>", unsafe_allow_html=True)
    st.subheader("Column health")
    st.dataframe(quality, use_container_width=True, hide_index=True)
    if numeric:
        st.subheader("Numeric summary")
        st.dataframe(data[numeric].describe().T.round(2), use_container_width=True)


def explore_page():
    data, name = get_dataset(); numeric, _, _, _ = get_profile(data)
    page_hero("Explore visually", f"Build an interactive chart from {name}.")
    c1, c2, c3 = st.columns(3)
    chart_type = c1.selectbox("Visual", ["Bar", "Line", "Scatter", "Histogram"])
    x_col = c2.selectbox("X axis", list(data.columns))
    y_col = c3.selectbox("Y axis / value", numeric or list(data.columns))
    color_col = st.selectbox("Group by (optional)", ["None"] + list(data.columns))
    try:
        color = None if color_col == "None" else color_col
        if chart_type == "Bar": figure = px.bar(data, x=x_col, y=y_col, color=color)
        elif chart_type == "Line": figure = px.line(data, x=x_col, y=y_col, color=color, markers=True)
        elif chart_type == "Scatter": figure = px.scatter(data, x=x_col, y=y_col, color=color)
        else: figure = px.histogram(data, x=y_col, color=color)
        figure.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=30, b=10), height=550)
        st.plotly_chart(figure, use_container_width=True)
    except Exception as error:
        st.warning(f"Try another column combination: {error}")


def ai_page():
    data, name = get_dataset(); numeric, _, _, quality = get_profile(data)
    page_hero("Ask AIXpo AI", "Use your local Ollama model for an evidence-based read of your dataset.")
    st.caption(f"Dataset: {name}")
    question = st.text_area("What would you like to discover?", placeholder="What are the strongest patterns in this dataset?")
    if st.button("Analyse with AIXpo AI", type="primary"):
        if not question.strip(): st.warning("Enter a question first."); return
        context = {"dataset": name, "rows": len(data), "columns": quality.to_dict("records"), "numeric_summary": data[numeric].describe().round(2).to_dict() if numeric else {}, "sample_rows": data.head(8).astype(object).where(pd.notna(data.head(8)), None).to_dict("records")}
        prompt = f"Dataset context: {json.dumps(context, default=str)[:18000]}\n\nQuestion: {question}"
        with st.spinner("AIXpo is analysing your data locally..."):
            try:
                response = requests.post(f"{st.session_state.ollama_url.rstrip('/')}/api/chat", json={"model": st.session_state.model, "stream": False, "messages": [{"role": "system", "content": "You are AIXpo, a precise data analyst. Use only supplied context. Answer with Insights, Evidence, and Recommended next step. Clearly state uncertainty."}, {"role": "user", "content": prompt}]}, timeout=180)
                response.raise_for_status(); st.markdown(response.json().get("message", {}).get("content", "The model returned an empty response."))
            except requests.exceptions.ConnectionError: st.error("AIXpo could not reach Ollama. Start Ollama and check the sidebar settings.")
            except requests.exceptions.Timeout: st.error("The local model timed out. Try a smaller model or a shorter question.")
            except Exception as error: st.error(f"Analysis could not be completed: {error}")


def data_page():
    data, name = get_dataset()
    page_hero("Source data", f"Review and export {name}.")
    st.dataframe(data, use_container_width=True, hide_index=True)
    st.download_button("Download working copy", data.to_csv(index=False).encode("utf-8"), "aixpo_export.csv", "text/csv")


with st.sidebar:
    st.markdown("## AIXpo")
    st.caption("AI Data Explorer")
    st.divider()
    st.markdown("**Local AI settings**")
    st.session_state.ollama_url = st.text_input("Ollama URL", st.session_state.get("ollama_url", "http://localhost:11434"))
    st.session_state.model = st.text_input("Model", st.session_state.get("model", "qwen2.5:3b"))
    st.caption("Files stay in this session. AI requests go only to your configured Ollama server.")

ROUTES = {
    "Upload": st.Page(upload_page, title="Upload", icon="⬆️", default=True),
    "Overview": st.Page(overview_page, title="Overview", icon="📊"),
    "Explore": st.Page(explore_page, title="Explore", icon="📈"),
    "Ask AI": st.Page(ai_page, title="Ask AI", icon="✨"),
    "Data": st.Page(data_page, title="Data", icon="🗂️"),
}
navigation = st.navigation(list(ROUTES.values()), position="sidebar")
navigation.run()
