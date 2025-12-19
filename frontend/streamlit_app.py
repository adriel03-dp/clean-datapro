import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from urllib.parse import quote
from io import BytesIO
import time

# Page config
st.set_page_config(
    page_title="CleanDataPro",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "CleanDataPro - Data Cleaning & Analysis Tool"}
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .success-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
    }
    .warning-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

BACKEND_BASE = os.environ.get("CLEAN_DATAPRO_BACKEND", "http://localhost:8000")

# Session state initialization
if "processing" not in st.session_state:
    st.session_state.processing = False
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# Sidebar navigation
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/data-in-cloud.png", width=80)
    st.title("CleanDataPro")
    st.markdown("---")
    
    page = st.radio(
        "📊 Navigation",
        ["🚀 Upload & Clean", "📈 Analytics", "📜 Processing History", "⚙️ Settings"],
        key="nav_page"
    )
    
    st.markdown("---")
    st.markdown("""
    ### About
    CleanDataPro helps you:
    - Analyze data quality issues
    - Automatically clean datasets
    - Generate professional reports
    - Track processing history
    """)
    
    st.markdown("---")
    st.markdown("**Version:** 1.0.0")

# Helper functions
def _basename_posix(path):
    if not path:
        return None
    return path.split("/")[-1]

def process_file(uploaded_file):
    """Process uploaded CSV file"""
    st.session_state.processing = True
    
    with st.spinner("🔄 Processing your file..."):
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
            resp = requests.post(
                f"{BACKEND_BASE}/api/process",
                files=files,
                timeout=60
            )
            
            if resp.status_code != 200:
                st.error(f"❌ Backend Error: {resp.status_code}")
                st.error(resp.text)
                return None
            
            st.session_state.last_result = resp.json()
            st.session_state.processing = False
            return resp.json()
        
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to backend. Is the FastAPI server running?")
            return None
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            return None

def display_summary_metrics(data):
    """Display summary metrics in columns"""
    summary = data.get("summary", {})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📥 Original Rows",
            f"{summary.get('original_rows', 'N/A'):,}",
            delta=None
        )
    
    with col2:
        st.metric(
            "✅ Cleaned Rows",
            f"{summary.get('cleaned_rows', 'N/A'):,}",
            delta=f"-{summary.get('dropped_duplicates', 0)} duplicates"
        )
    
    with col3:
        st.metric(
            "🗑️ Removed",
            f"{summary.get('dropped_duplicates', 0):,}",
            delta="duplicates"
        )
    
    with col4:
        original_missing = summary.get("missing_before", 0)
        cleaned_missing = summary.get("missing_after", 0)
        improvement = original_missing - cleaned_missing if original_missing > 0 else 0
        st.metric(
            "📊 Missing Values Fixed",
            f"{improvement:,}",
            delta=None
        )

def display_missing_analysis(data):
    """Display before/after missing data analysis"""
    summary = data.get("summary", {})
    before = summary.get("missing_summary_before", [])
    after = summary.get("missing_summary_after", [])
    
    if not before:
        st.warning("No analysis data available")
        return
    
    df_before = pd.DataFrame(before)
    df_after = pd.DataFrame(after)
    
    if df_before.empty:
        return
    
    # Merge before/after data
    merged = pd.merge(
        df_before[["column", "missing_pct"]].rename(
            columns={"missing_pct": "Before (%)"}
        ),
        df_after[["column", "missing_pct"]].rename(
            columns={"missing_pct": "After (%)"}
        ),
        on="column",
        how="outer",
    ).fillna(0)
    
    # Create visualization
    fig = px.bar(
        merged.melt(id_vars=["column"], value_vars=["Before (%)", "After (%)"]),
        x="column",
        y="value",
        color="variable",
        labels={"value": "Missing %", "variable": "Stage"},
        title="Missing Values: Before vs After Cleaning",
        barmode="group",
        color_discrete_map={"Before (%)": "#ef553b", "After (%)": "#00cc96"}
    )
    fig.update_layout(height=400, hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
    
    # Display table
    with st.expander("📋 View Detailed Analysis"):
        st.dataframe(merged, use_container_width=True, hide_index=True)

def display_downloads(data):
    """Display download links"""
    cleaned_file = data.get("cleaned_file")
    report_file = data.get("report_file")
    json_summary = data.get("json_summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if cleaned_file:
            fn = _basename_posix(cleaned_file)
            url = f"{BACKEND_BASE}/api/download?kind=processed&filename={quote(fn)}"
            st.markdown(f"[📥 Download Cleaned CSV]({url})", unsafe_allow_html=True)
    
    with col2:
        if report_file:
            fn = _basename_posix(report_file)
            url = f"{BACKEND_BASE}/api/download?kind=reports&filename={quote(fn)}"
            st.markdown(f"[📄 Download PDF Report]({url})", unsafe_allow_html=True)
    
    with col3:
        if json_summary:
            fn = _basename_posix(json_summary)
            url = f"{BACKEND_BASE}/api/download?kind=reports&filename={quote(fn)}"
            st.markdown(f"[📊 Download JSON Summary]({url})", unsafe_allow_html=True)

# Page: Upload & Clean
if page == "🚀 Upload & Clean":
    st.header("🚀 Upload & Clean Your Data")
    st.markdown("""
    Upload a CSV file to:
    - Analyze missing values and data quality
    - Automatically remove duplicates
    - Fill missing values intelligently
    - Generate a professional PDF report
    """)
    
    st.markdown("---")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        help="Upload a CSV file to get started"
    )
    
    if uploaded_file is not None:
        # Show file preview
        with st.expander("👀 Preview File", expanded=True):
            try:
                preview_df = pd.read_csv(uploaded_file)
                st.write(f"**File:** {uploaded_file.name}")
                st.write(f"**Size:** {uploaded_file.size / 1024:.2f} KB")
                st.write(f"**Shape:** {preview_df.shape[0]} rows × {preview_df.shape[1]} columns")
                st.dataframe(preview_df.head(10), use_container_width=True)
            except Exception as e:
                st.error(f"Error reading file: {e}")
        
        st.markdown("---")
        
        # Process button
        if st.button("🔄 Process & Clean", use_container_width=True, type="primary"):
            result = process_file(uploaded_file)
            
            if result:
                st.success("✅ Processing complete!")
                
                st.markdown("---")
                
                # Display metrics
                st.subheader("📊 Summary")
                display_summary_metrics(result)
                
                st.markdown("---")
                
                # Display analysis
                st.subheader("📈 Data Quality Analysis")
                display_missing_analysis(result)
                
                st.markdown("---")
                
                # Downloads
                st.subheader("📥 Download Results")
                display_downloads(result)

# Page: Analytics
elif page == "📈 Analytics":
    st.header("📈 Advanced Analytics")
    
    if st.session_state.last_result:
        data = st.session_state.last_result
        summary = data.get("summary", {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Cleaning Impact")
            before_total = summary.get("missing_before", 0)
            after_total = summary.get("missing_after", 0)
            
            if before_total > 0:
                improvement = ((before_total - after_total) / before_total) * 100
                fig = go.Figure(data=[
                    go.Pie(
                        labels=["Fixed", "Remaining"],
                        values=[before_total - after_total, after_total],
                        hole=0.4,
                        marker=dict(colors=["#00cc96", "#ef553b"])
                    )
                ])
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                st.metric("Data Quality Improvement", f"{improvement:.1f}%")
        
        with col2:
            st.subheader("Row Statistics")
            rows_data = {
                "Category": ["Original", "Duplicates", "Final"],
                "Count": [
                    summary.get("original_rows", 0),
                    summary.get("dropped_duplicates", 0),
                    summary.get("cleaned_rows", 0)
                ]
            }
            df_rows = pd.DataFrame(rows_data)
            
            fig = px.bar(
                df_rows,
                x="Category",
                y="Count",
                text="Count",
                color="Category",
                color_discrete_sequence=["#667eea", "#ef553b", "#00cc96"]
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Upload and process a file first to see analytics")

# Page: History
elif page == "📜 Processing History":
    st.header("📜 Processing History")
    
    try:
        resp = requests.get(f"{BACKEND_BASE}/api/runs?limit=20", timeout=10)
        if resp.status_code == 200:
            history_data = resp.json()
            runs = history_data.get("runs", [])
            
            if runs:
                st.success(f"Found {len(runs)} processing runs")
                
                # Create history dataframe
                history_list = []
                for run in runs:
                    history_list.append({
                        "File": run.get("uploaded_filename", "Unknown"),
                        "Run ID": run.get("run_id", "N/A")[:8],
                        "Original Rows": run.get("summary", {}).get("original_rows", "N/A"),
                        "Cleaned Rows": run.get("summary", {}).get("cleaned_rows", "N/A"),
                        "Duplicates Removed": run.get("summary", {}).get("dropped_duplicates", 0)
                    })
                
                df_history = pd.DataFrame(history_list)
                st.dataframe(df_history, use_container_width=True, hide_index=True)
            else:
                st.info("No processing history found")
        else:
            st.warning("Could not fetch history from backend")
    except Exception as e:
        st.error(f"Error fetching history: {e}")

# Page: Settings
elif page == "⚙️ Settings":
    st.header("⚙️ Settings & Configuration")
    
    st.subheader("Backend Configuration")
    st.write(f"**Backend URL:** `{BACKEND_BASE}`")
    
    if st.button("🔗 Test Backend Connection"):
        try:
            resp = requests.get(f"{BACKEND_BASE}/api/runs?limit=1", timeout=5)
            if resp.status_code == 200:
                st.success("✅ Backend is online and responding")
            else:
                st.warning(f"⚠️ Backend returned status {resp.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to backend. Make sure FastAPI server is running.")
        except Exception as e:
            st.error(f"❌ Error: {e}")
    
    st.markdown("---")
    
    st.subheader("About CleanDataPro")
    st.markdown("""
    **Version:** 1.0.0
    
    **Features:**
    - 📊 Missing value analysis
    - 🧹 Intelligent data cleaning
    - 📄 PDF report generation
    - 📜 Processing history tracking
    - 🔌 REST API integration
    
    **Tech Stack:**
    - Frontend: Streamlit
    - Backend: FastAPI
    - Data Processing: Pandas
    - Reporting: ReportLab
    - Visualization: Plotly
    
    **Repository:** [GitHub - clean-datapro](https://github.com/adriel03-dp/clean-datapro)
    """)
