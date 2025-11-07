import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os
from urllib.parse import quote

BACKEND_BASE = os.environ.get("CLEAN_DATAPRO_BACKEND", "http://localhost:8000")

st.set_page_config(page_title="CleanDataPro - Demo", layout="wide")
st.title("CleanDataPro — Upload & Clean CSV")

st.markdown(
    "Upload a CSV file and the backend will clean it, generate a PDF report "
    "and JSON summary.\nYou can download the cleaned CSV and report after "
    "processing."
)

uploaded = st.file_uploader("Choose a CSV file", type=["csv"])

if uploaded is not None:
    st.info("Uploading and processing — this may take a few seconds...")
    files = {"file": (uploaded.name, uploaded.getvalue(), "text/csv")}
    try:
        resp = requests.post(
            f"{BACKEND_BASE}/api/process",
            files=files,
        )
    except Exception as e:
        st.error(f"Failed to call backend: {e}")
        st.stop()

    if resp.status_code != 200:
        st.error(f"Backend returned an error: {resp.status_code} - {resp.text}")
        st.stop()

    data = resp.json()
    st.success("Processing complete")

    # Summary
    st.subheader("Summary")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("Original rows:", data.get("summary", {}).get("original_rows"))
        st.write("Cleaned rows:", data.get("summary", {}).get("cleaned_rows"))
        st.write(
            "Dropped duplicates:", data.get("summary", {}).get("dropped_duplicates")
        )

    # Show missing% bar chart (before)
    before = data.get("summary", {}).get("missing_summary_before", [])
    after = data.get("summary", {}).get("missing_summary_after", [])

    if before:
        df_before = pd.DataFrame(before)
        df_after = pd.DataFrame(after)

        if not df_before.empty:
            st.subheader("Missing % by column — Before vs After")
            merged = pd.merge(
                df_before[["column", "missing_pct"]].rename(
                    columns={"missing_pct": "before_pct"}
                ),
                df_after[["column", "missing_pct"]].rename(
                    columns={"missing_pct": "after_pct"}
                ),
                on="column",
                how="outer",
            ).fillna(0)

            fig = px.bar(
                merged.melt(id_vars=["column"], value_vars=["before_pct", "after_pct"]),
                x="column",
                y="value",
                color="variable",
                labels={"value": "Missing %", "variable": "Stage"},
                title="Missing % before vs after",
            )
            st.plotly_chart(fig, use_container_width=True)

    # Show artifact download links
    st.subheader("Downloads")
    raw_file = data.get("raw_file")
    cleaned_file = data.get("cleaned_file")
    report_file = data.get("report_file")
    json_summary = data.get("json_summary")

    def _basename_posix(path):
        if not path:
            return None
        return path.split("/")[-1]

    links = []
    if cleaned_file:
        fn = _basename_posix(cleaned_file)
        url = f"{BACKEND_BASE}/api/download?kind=processed&filename={quote(fn)}"
        links.append(("Cleaned CSV", url))
    if report_file:
        fn = _basename_posix(report_file)
        url = f"{BACKEND_BASE}/api/download?kind=reports&filename={quote(fn)}"
        links.append(("PDF Report", url))
    if json_summary:
        fn = _basename_posix(json_summary)
        url = f"{BACKEND_BASE}/api/download?kind=reports&filename={quote(fn)}"
        links.append(("JSON Summary", url))

    for label, url in links:
        st.markdown(f"- [{label}]({url})")

    st.info("If download links don't work in Streamlit, open them in your browser.")
