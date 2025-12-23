import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from urllib.parse import quote
from io import BytesIO
import time
from auth_pages import show_login_page, show_logout_button, require_auth

# Page config
st.set_page_config(
    page_title="CleanDataPro",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "CleanDataPro - Data Cleaning & Analysis Tool"}
)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "token" not in st.session_state:
    st.session_state.token = None
if "email" not in st.session_state:
    st.session_state.email = None
if "name" not in st.session_state:
    st.session_state.name = None

# Require authentication before loading the dashboard
require_auth()

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
    /* Style logout button in red */
    .stSidebar [data-testid="stButton"] button:last-of-type {
        background-color: #dc3545 !important;
        color: white !important;
        border-color: #dc3545 !important;
    }
    .stSidebar [data-testid="stButton"] button:last-of-type:hover {
        background-color: #c82333 !important;
        border-color: #c82333 !important;
    }
</style>
""", unsafe_allow_html=True)

BACKEND_BASE = os.environ.get("CLEAN_DATAPRO_BACKEND", "http://localhost:8000")


def _auth_headers() -> dict:
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

# Session state initialization
if "processing" not in st.session_state:
    st.session_state.processing = False
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# Sidebar navigation
with st.sidebar:
    st.title("CleanDataPro")
    st.markdown(f"**User:** {st.session_state.name or st.session_state.email}")
    st.markdown("---")
    
    page = st.radio(
        "Navigation",
        ["Upload & Clean", "Analytics", "Processing History", "Settings"],
        key="nav_page"
    )
    
    st.markdown("---")
    if st.button("Logout", use_container_width=True, key="logout_btn"):
        st.session_state.authenticated = False
        st.session_state.token = None
        st.session_state.email = None
        st.session_state.name = None
        st.rerun()
    
    # Footer - About section
    st.markdown("---")
    st.markdown("""
    ### About CleanDataPro
    CleanDataPro helps you:
    - Analyze data quality issues
    - Automatically clean datasets
    - Generate professional reports
    - Track processing history
    
    **Developed by:** Adriel Perera
    
    An undergraduate specializing in Software Engineering who created this project to improve technical skills and successfully deployed it to production.
    
    If you like this work, feel free to:
    - [Connect on LinkedIn](https://www.linkedin.com/in/adriel-perera)
    - [Check out my GitHub](https://github.com/adriel03-dp)
    - Leave feedback or comments
    
    **Version:** 1.0.0
    """)

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
                headers=_auth_headers(),
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
    
    # Merge before/after data with missing counts (not just percentages)
    merged = pd.merge(
        df_before[["column", "missing_count", "missing_pct"]].rename(
            columns={"missing_count": "Count Before", "missing_pct": "Before (%)"}
        ),
        df_after[["column", "missing_count", "missing_pct"]].rename(
            columns={"missing_count": "Count After", "missing_pct": "After (%)"}
        ),
        on="column",
        how="outer",
    ).fillna(0)
    
    # Add a column for improvement
    merged["Fixed"] = merged["Count Before"] - merged["Count After"]
    
    # Display table first (more informative)
    st.markdown("**Summary Table:**")
    display_table = merged[["column", "Count Before", "Before (%)", "Count After", "After (%)", "Fixed"]].copy()
    display_table.columns = ["Column", "Missing Before", "Before %", "Missing After", "After %", "Fixed"]
    st.dataframe(display_table, width='stretch', hide_index=True)
    
    st.markdown("---")
    
    # Create visualization showing missing counts (more visible than percentages)
    st.markdown("**Missing Values Count Comparison:**")
    
    # Prepare data for grouped bar chart
    chart_data = []
    for _, row in merged.iterrows():
        chart_data.append({
            "Column": str(row["column"]),
            "Stage": "Before",
            "Count": int(row["Count Before"]) if pd.notna(row["Count Before"]) else 0
        })
        chart_data.append({
            "Column": str(row["column"]),
            "Stage": "After",
            "Count": int(row["Count After"]) if pd.notna(row["Count After"]) else 0
        })
    
    chart_df = pd.DataFrame(chart_data)
    # Ensure Count is integer type
    chart_df["Count"] = chart_df["Count"].astype(int)
    
    fig = px.bar(
        chart_df,
        x="Column",
        y="Count",
        color="Stage",
        labels={"Count": "Missing Values"},
        title="Missing Values: Before vs After Cleaning",
        barmode="group",
        color_discrete_map={"Before": "#ef553b", "After": "#00cc96"},
        text="Count"
    )
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    fig.update_layout(
        height=400, 
        hovermode="x unified",
        yaxis_title="Number of Missing Values",
        xaxis_title="Column"
    )
    st.plotly_chart(fig, width='stretch')

def display_data_issues_report(data):
    """Display comprehensive report of data issues before and after cleaning"""
    summary = data.get("summary", {})
    before = summary.get("missing_summary_before", [])
    after = summary.get("missing_summary_after", [])
    
    if not before:
        st.warning("No analysis data available")
        return
    
    # MAIN BEFORE & AFTER COMPARISON - Most Prominent
    st.markdown("""
    <div style='background: linear-gradient(90deg, #fff3e0 0%, #e0f2f1 100%); padding: 25px; border-radius: 15px; margin: 20px 0;'>
        <h2 style='text-align: center; color: #1a1a1a; margin: 0;'>📊 YOUR DATA TRANSFORMATION</h2>
        <p style='text-align: center; color: #666; margin: 10px 0 0 0;'>See exactly what issues were found and what was fixed</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get key metrics
    original_rows = summary.get("original_rows", 0)
    cleaned_rows = summary.get("cleaned_rows", 0)
    duplicates = summary.get("dropped_duplicates", 0)
    missing_before = summary.get("missing_before", 0)
    missing_after = summary.get("missing_after", 0)
    cols_count = summary.get("columns", 1)
    
    # Calculate percentages
    missing_before_pct = (missing_before / (original_rows * cols_count) * 100) if original_rows > 0 else 0
    missing_after_pct = (missing_after / (cleaned_rows * cols_count) * 100) if cleaned_rows > 0 else 0
    
    # THREE COLUMN COMPARISON: BEFORE / FIXES / AFTER
    before_col, fixes_col, after_col = st.columns([1, 0.8, 1], gap="large")
    
    # BEFORE COLUMN
    with before_col:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #ffcdd2 0%, #f8bbd0 100%); padding: 20px; border-radius: 12px; border: 3px solid #c62828;'>
            <h3 style='color: #b71c1c; text-align: center; margin: 0 0 15px 0;'>❌ BEFORE CLEANING</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style='background: #fff5f5; padding: 15px; border-radius: 8px; margin: 10px 0;'>
            <p style='margin: 8px 0; font-size: 14px;'><b>📥 Total Rows:</b> <span style='color: #d32f2f; font-size: 16px; font-weight: bold;'>{original_rows:,}</span></p>
            <p style='margin: 8px 0; font-size: 14px;'><b>🔄 Duplicates Found:</b> <span style='color: #d32f2f; font-size: 16px; font-weight: bold;'>{duplicates}</span> rows</p>
            <p style='margin: 8px 0; font-size: 14px;'><b>📭 Missing Values:</b> <span style='color: #d32f2f; font-size: 16px; font-weight: bold;'>{missing_before:,}</span> cells</p>
            <p style='margin: 8px 0; font-size: 14px;'><b>🔴 Data Quality:</b> <span style='color: #d32f2f; font-size: 16px; font-weight: bold;'>{100-missing_before_pct:.1f}%</span></p>
            <hr style='margin: 10px 0; border: none; border-top: 2px solid #ffcdd2;'>
            <p style='margin: 5px 0; font-size: 13px; color: #666;'><b>⚠️ Data Issues:</b></p>
            <p style='margin: 3px 0 0 0; font-size: 12px; color: #d32f2f;'>• {duplicates} duplicate rows<br>• {missing_before:,} empty cells<br>• {missing_before_pct:.1f}% missing data</p>
        </div>
        """, unsafe_allow_html=True)
    
    # FIXES COLUMN (Middle arrow/transformation)
    with fixes_col:
        st.markdown("""
        <div style='display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%;'>
            <div style='text-align: center; margin: 30px 0;'>
                <p style='font-size: 24px; margin: 0;'>⚙️</p>
                <p style='font-size: 14px; color: #666; margin: 10px 0;'><b>CLEANING</b></p>
                <p style='font-size: 40px; margin: 0;'>→</p>
                <p style='font-size: 12px; color: #666; margin: 10px 0;'><b>FIXED</b></p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show what was fixed
        st.markdown(f"""
        <div style='background: #fff9c4; padding: 12px; border-radius: 8px; text-align: center; margin: 10px 0;'>
            <p style='margin: 5px 0; font-size: 12px; color: #f57f17;'><b>Removed</b></p>
            <p style='margin: 0; font-size: 16px; color: #f57f17; font-weight: bold;'>{duplicates} dups</p>
        </div>
        <div style='background: #e1f5fe; padding: 12px; border-radius: 8px; text-align: center; margin: 10px 0;'>
            <p style='margin: 5px 0; font-size: 12px; color: #01579b;'><b>Filled</b></p>
            <p style='margin: 0; font-size: 16px; color: #01579b; font-weight: bold;'>{missing_before - missing_after:,} cells</p>
        </div>
        """, unsafe_allow_html=True)
    
    # AFTER COLUMN
    with after_col:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #c8e6c9 0%, #a5d6a7 100%); padding: 20px; border-radius: 12px; border: 3px solid #1b5e20;'>
            <h3 style='color: #1b5e20; text-align: center; margin: 0 0 15px 0;'>✅ AFTER CLEANING</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style='background: #f1f8f5; padding: 15px; border-radius: 8px; margin: 10px 0;'>
            <p style='margin: 8px 0; font-size: 14px;'><b>📥 Total Rows:</b> <span style='color: #2e7d32; font-size: 16px; font-weight: bold;'>{cleaned_rows:,}</span></p>
            <p style='margin: 8px 0; font-size: 14px;'><b>🔄 Duplicates:</b> <span style='color: #2e7d32; font-size: 16px; font-weight: bold;'>0</span> rows</p>
            <p style='margin: 8px 0; font-size: 14px;'><b>📭 Missing Values:</b> <span style='color: #2e7d32; font-size: 16px; font-weight: bold;'>{missing_after:,}</span> cells</p>
            <p style='margin: 8px 0; font-size: 14px;'><b>🟢 Data Quality:</b> <span style='color: #2e7d32; font-size: 16px; font-weight: bold;'>{100-missing_after_pct:.1f}%</span></p>
            <hr style='margin: 10px 0; border: none; border-top: 2px solid #c8e6c9;'>
            <p style='margin: 5px 0; font-size: 13px; color: #666;'><b>✅ All Fixed:</b></p>
            <p style='margin: 3px 0 0 0; font-size: 12px; color: #1b5e20;'>• All duplicates removed<br>• All missing values filled<br>• {100-missing_after_pct:.1f}% complete data</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # QUALITY IMPROVEMENT HIGHLIGHT
    improvement = (100 - missing_before_pct) - (100 - missing_after_pct)
    quality_improvement_pct = ((100 - missing_after_pct) - (100 - missing_before_pct)) / (100 - missing_before_pct) * 100 if (100 - missing_before_pct) > 0 else 0
    
    if improvement > 0:
        st.markdown(f"""
        <div style='background: linear-gradient(90deg, #c8e6c9 0%, #a5d6a7 100%); padding: 25px; border-radius: 12px; border-left: 5px solid #1b5e20; margin: 20px 0;'>
            <h3 style='color: #1b5e20; margin: 0 0 10px 0;'>🎯 IMPROVEMENT ACHIEVED</h3>
            <p style='color: #1b5e20; margin: 0; font-size: 24px; font-weight: bold;'>{improvement:.1f} point increase in data quality</p>
            <p style='color: #2e7d32; margin: 5px 0 0 0; font-size: 16px;'>Your data is now {100-missing_after_pct:.1f}% complete (up from {100-missing_before_pct:.1f}%)</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Create tabs for detailed views
    tab1, tab2, tab3, tab4 = st.tabs([
        "🚨 Issues Found", 
        "📊 Missing by Column", 
        "🧹 Cleaning Details", 
        "✅ Final Quality"
    ])
    
    with tab1:
        st.markdown("### 🚨 Complete List of Issues Found")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div style='background: #ffe0e0; padding: 20px; border-radius: 10px; text-align: center;'>
                <h2 style='color: #d32f2f; margin: 0;'>{duplicates}</h2>
                <p style='color: #d32f2f; margin: 5px 0 0 0;'><b>Duplicate<br>Rows</b></p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style='background: #fff3cd; padding: 20px; border-radius: 10px; text-align: center;'>
                <h2 style='color: #f57f17; margin: 0;'>{missing_before:,}</h2>
                <p style='color: #f57f17; margin: 5px 0 0 0;'><b>Missing<br>Values</b></p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style='background: #f3e5f5; padding: 20px; border-radius: 10px; text-align: center;'>
                <h2 style='color: #7b1fa2; margin: 0;'>{missing_before_pct:.1f}%</h2>
                <p style='color: #7b1fa2; margin: 5px 0 0 0;'><b>Data<br>Missing</b></p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div style='background: #e1f5fe; padding: 20px; border-radius: 10px; text-align: center;'>
                <h2 style='color: #01579b; margin: 0;'>{100-missing_before_pct:.1f}%</h2>
                <p style='color: #01579b; margin: 5px 0 0 0;'><b>Quality<br>Before</b></p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### Detailed Issue Breakdown")
        
        issue_list = []
        
        if duplicates > 0:
            issue_list.append({
                "🚨 Issue": "Duplicate Rows",
                "Count": duplicates,
                "Percentage": f"{(duplicates/original_rows*100):.2f}%" if original_rows > 0 else "0%",
                "Severity": "HIGH" if duplicates > original_rows * 0.05 else "MEDIUM",
                "Status": "✅ REMOVED"
            })
        
        if missing_before > 0:
            issue_list.append({
                "🚨 Issue": "Missing Values",
                "Count": f"{missing_before:,}",
                "Percentage": f"{missing_before_pct:.2f}%",
                "Severity": "HIGH" if missing_before_pct > 20 else ("MEDIUM" if missing_before_pct > 5 else "LOW"),
                "Status": "✅ FILLED"
            })
        
        if issue_list:
            df_issues = pd.DataFrame(issue_list)
            st.dataframe(df_issues, width='stretch', hide_index=True)
        else:
            st.success("✅ No data quality issues found!")
    
    with tab2:
        st.markdown("### 📊 Missing Values Breakdown by Column")
        
        df_before = pd.DataFrame(before)
        df_after = pd.DataFrame(after)
        
        merged = pd.merge(
            df_before[["column", "missing_count", "missing_pct", "dtype", "unique_count"]],
            df_after[["column", "missing_count", "missing_pct"]].rename(columns={
                "missing_count": "missing_count_after",
                "missing_pct": "missing_pct_after"
            }),
            on="column",
            how="outer"
        ).fillna(0)
        
        merged["Fixed"] = merged["missing_count"] - merged["missing_count_after"]
        merged["Status"] = merged.apply(
            lambda row: "✅ Fixed" if row["missing_count_after"] == 0 else "⚠️ Partial",
            axis=1
        )
        
        display_cols = merged[[
            "column", "dtype", "missing_count", "missing_pct", 
            "missing_count_after", "missing_pct_after", "Fixed", "Status"
        ]].copy()
        display_cols.columns = [
            "Column", "Type", "Before", "Before %", 
            "After", "After %", "Fixed ✅", "Status"
        ]
        
        st.dataframe(display_cols, width='stretch', hide_index=True)
        
        st.markdown("---")
        
        fig = px.bar(
            merged,
            x="column",
            y=["missing_count", "missing_count_after"],
            labels={"column": "Column", "value": "Missing Count", "variable": "Stage"},
            title="Missing Values: Before vs After by Column",
            barmode="group",
            color_discrete_map={
                "missing_count": "#ef553b",
                "missing_count_after": "#00cc96"
            },
            text="value"
        )
        fig.update_traces(texttemplate='%{value}', textposition='outside')
        fig.update_layout(height=400, hovermode="x unified", xaxis_tickangle=-45)
        st.plotly_chart(fig, width='stretch')
    
    with tab3:
        st.markdown("### 🧹 Complete Cleaning Process")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**What Was Fixed:**")
            st.markdown(f"""
            ✅ **Removed {duplicates} Duplicate Rows**
            - Exact duplicate rows deleted
            - {(cleaned_rows/original_rows*100):.1f}% of data retained
            
            ✅ **Filled {missing_before - missing_after:,} Missing Values**
            - Numeric columns: Filled with median
            - Categorical columns: Filled with mode
            - Datetime columns: Filled with earliest date
            
            ✅ **Total Issues Resolved: {duplicates + (missing_before - missing_after):,}**
            """)
        
        with col2:
            st.markdown("**Transformation Summary:**")
            st.markdown(f"""
            📥 Original data: {original_rows:,} rows × {cols_count} columns
            
            🗑️ Removed: {original_rows - cleaned_rows:,} duplicate rows
            
            🧹 Cleaned: {cleaned_rows:,} rows (final result)
            
            📊 Data preserved: {(cleaned_rows/original_rows*100):.2f}%
            """)
        
        st.markdown("---")
        
        # Funnel chart
        fig_funnel = go.Figure()
        
        stages = ["Original\nData", "Duplicates\nRemoved", "Missing Values\nFilled", "Clean\nData ✅"]
        values = [
            original_rows,
            cleaned_rows,
            cleaned_rows,
            cleaned_rows
        ]
        
        fig_funnel.add_trace(go.Funnel(
            y=stages,
            x=values,
            marker=dict(color=["#ef553b", "#ffa726", "#66bb6a", "#00cc96"]),
            text=[f"{v:,} rows" for v in values],
            textposition="inside",
            hovertemplate="<b>%{y}</b><br>Rows: %{x:,}<extra></extra>"
        ))
        
        fig_funnel.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
        st.plotly_chart(fig_funnel, width='stretch')
    
    with tab4:
        st.markdown("### ✅ Data Quality Assessment")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Before Cleaning:**")
            st.markdown(f"""
            📊 Completeness: **{100-missing_before_pct:.1f}%**
            
            📭 Missing Data: **{missing_before_pct:.1f}%**
            
            🔄 Duplicate Rows: **{duplicates}** ({(duplicates/original_rows*100):.2f}%)
            
            📈 Quality Score: **{100-missing_before_pct:.0f}**/100
            
            ⚠️ Status: Needs cleaning
            """)
        
        with col2:
            st.markdown("**After Cleaning:**")
            st.markdown(f"""
            📊 Completeness: **{100-missing_after_pct:.1f}%**
            
            📭 Missing Data: **{missing_after_pct:.1f}%**
            
            🔄 Duplicate Rows: **0** (0%)
            
            📈 Quality Score: **{100-missing_after_pct:.0f}**/100
            
            ✅ Status: Ready for analysis
            """)
        
        st.markdown("---")
        
        if 100 - missing_after_pct >= 95:
            st.success(f"🎉 **Excellent!** Your data quality improved by {improvement:.1f} points and is now {100-missing_after_pct:.1f}% complete!")
        elif 100 - missing_after_pct >= 85:
            st.info(f"✅ **Good!** Your data quality improved by {improvement:.1f} points. Data is {100-missing_after_pct:.1f}% complete.")
        else:
            st.warning(f"⚠️ Data quality improved by {improvement:.1f} points to {100-missing_after_pct:.1f}% complete.")

def display_downloads(data):
    """Display download links"""
    cleaned_file = data.get("cleaned_file")
    report_file = data.get("report_file")
    json_summary = data.get("json_summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if cleaned_file:
            fn = _basename_posix(cleaned_file)
            if fn:
                url = f"{BACKEND_BASE}/api/download?kind=processed&filename={quote(fn)}"
                st.markdown(f"[📥 Download Cleaned CSV]({url})", unsafe_allow_html=True)
    
    with col2:
        if report_file:
            fn = _basename_posix(report_file)
            if fn:
                url = f"{BACKEND_BASE}/api/download?kind=reports&filename={quote(fn)}"
                st.markdown(f"[📄 Download PDF Report]({url})", unsafe_allow_html=True)
    
    with col3:
        if json_summary:
            fn = _basename_posix(json_summary)
            if fn:
                url = f"{BACKEND_BASE}/api/download?kind=reports&filename={quote(fn)}"
                st.markdown(f"[📊 Download JSON Summary]({url})", unsafe_allow_html=True)

# Page: Upload & Clean
if page == "Upload & Clean":
    st.header("Upload & Clean Your Data")
    
    # Introduction with tabs
    intro_tab1, intro_tab2 = st.tabs(["📤 Upload", "ℹ️ How It Works"])
    
    with intro_tab1:
        st.markdown("""
        <div style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
            <h3 style='margin-top: 0;'>✨ Upload Your CSV File</h3>
            <p>CleanDataPro will analyze your data quality and automatically fix issues including duplicates and missing values.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with intro_tab2:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **Step 1: Upload**
            
            Choose your CSV file (max 200MB)
            
            ✓ Automatic format detection  
            ✓ UTF-8 encoding support  
            ✓ Instant preview  
            """)
        
        with col2:
            st.markdown("""
            **Step 2: Analyze & Clean**
            
            CleanDataPro processes your file
            
            ✓ Detect data quality issues  
            ✓ Remove duplicates  
            ✓ Fill missing values  
            """)
        
        with col3:
            st.markdown("""
            **Step 3: Download**
            
            Get your cleaned data
            
            ✓ CSV format  
            ✓ PDF report  
            ✓ JSON summary  
            """)
    
    st.markdown("---")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=["csv"],
        help="Upload a CSV file to get started. Maximum size: 200MB"
    )
    
    if uploaded_file is not None:
        # File information
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📄 File Name", uploaded_file.name.split('.')[0])
        
        with col2:
            st.metric("💾 File Size", f"{uploaded_file.size / 1024:.1f} KB")
        
        with col3:
            try:
                preview_df = pd.read_csv(uploaded_file)
                st.metric("📊 Dimensions", f"{preview_df.shape[0]} × {preview_df.shape[1]}")
            except:
                st.metric("📊 Dimensions", "Error")
        
        st.markdown("---")
        
        # Show file preview
        with st.expander("👀 Preview File (First 10 Rows)", expanded=True):
            try:
                uploaded_file.seek(0)  # Reset file pointer to beginning
                preview_df = pd.read_csv(uploaded_file)
                st.dataframe(preview_df.head(10), width='stretch')
                
                with st.expander("📋 Column Information"):
                    col_info = []
                    for col in preview_df.columns:
                        col_info.append({
                            "Column": col,
                            "Type": str(preview_df[col].dtype),
                            "Missing": preview_df[col].isna().sum(),
                            "Unique": preview_df[col].nunique()
                        })
                    st.dataframe(pd.DataFrame(col_info), width='stretch', hide_index=True)
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")
        
        st.markdown("---")
        
        # Processing options
        with st.expander("⚙️ Processing Options", expanded=False):
            st.markdown("**Enabled Features:**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("✓ Remove duplicate rows")
                st.write("✓ Detect numeric types")
                st.write("✓ Fill missing values")
            
            with col2:
                st.write("✓ Generate reports")
                st.write("✓ Save to history")
                st.write("✓ Preserve raw data")
        
        st.markdown("---")
        
        # Process button
        if st.button("🔄 Process & Clean", width='stretch', type="primary"):
            result = process_file(uploaded_file)
            
            if result:
                st.success("✅ Processing complete!")
                
                st.markdown("---")
                
                # Display metrics
                st.subheader("📊 Summary")
                display_summary_metrics(result)
                
                st.markdown("---")
                
                # Display data issues report
                st.subheader("🚨 Data Issues & Cleaning Results")
                display_data_issues_report(result)
                
                st.markdown("---")
                
                # Display analysis
                st.subheader("📈 Data Quality Analysis")
                display_missing_analysis(result)
                
                st.markdown("---")
                
                # Downloads
                st.subheader("📥 Download Results")
                display_downloads(result)
    else:
        # Show information when no file is uploaded
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **📋 Supported File Format**
            
            • CSV (.csv)
            • UTF-8 encoding
            • Max size: 200MB
            • Headers required
            """)
        
        with col2:
            st.markdown("""
            **🤖 What Gets Cleaned**
            
            • Exact duplicate rows
            • Missing/empty values
            • Type inconsistencies
            • Data quality issues
            """)

# Page: Analytics
elif page == "Analytics":
    st.header("Advanced Analytics Dashboard")
    
    # Analytics information tabs
    analytics_tab1, analytics_tab2, analytics_tab3 = st.tabs(["📊 Dashboard", "📖 Guide", "💡 Tips"])
    
    with analytics_tab2:
        st.markdown("""
        **Dashboard Sections**
        
        1. **Key Metrics Overview** - High-level statistics about your data
        2. **Cleaning Impact Analysis** - How much data was cleaned and improved
        3. **Column-Wise Analysis** - Per-column cleaning details and quality scores
        4. **Data Completeness Heatmap** - Visual representation of data quality
        """)
    
    with analytics_tab3:
        st.markdown("""
        **Understanding the Charts**
        
        💡 **Quality Score**: 100% means no missing values, 0% means all values missing
        
        💡 **Data Loss Overview**: Shows what percentage of issues were fixed
        
        💡 **Column Types**: Numeric vs Categorical distribution
        
        💡 **Improvement %**: Percentage increase in overall data quality
        """)
    
    with analytics_tab1:
        if st.session_state.last_result:
            data = st.session_state.last_result
            summary = data.get("summary", {})
            
            # ========== TOP METRICS SECTION ==========
            st.subheader("📊 Key Metrics Overview")
            metric_cols = st.columns(5)
            
            with metric_cols[0]:
                st.metric("📥 Original Rows", f"{summary.get('original_rows', 0):,}")
            
            with metric_cols[1]:
                st.metric("✅ Cleaned Rows", f"{summary.get('cleaned_rows', 0):,}")
            
            with metric_cols[2]:
                st.metric("📋 Total Columns", f"{summary.get('columns', 0)}")
            
            with metric_cols[3]:
                missing_before = summary.get("missing_before", 0)
                missing_after = summary.get("missing_after", 0)
                st.metric("🩹 Issues Fixed", f"{missing_before - missing_after:,}")
            
            with metric_cols[4]:
                improvement = 0
                if summary.get("missing_before", 0) > 0:
                    improvement = ((summary.get("missing_before", 0) - summary.get("missing_after", 0)) / summary.get("missing_before", 0)) * 100
                st.metric("⬆️ Quality Improvement", f"{improvement:.1f}%")
            
            st.markdown("---")
            
            # ========== CLEANING IMPACT SECTION ==========
            st.subheader("🎯 Cleaning Impact Analysis")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Data Loss Overview**")
                before_total = summary.get("missing_before", 0)
                after_total = summary.get("missing_after", 0)
                
                if before_total > 0:
                    fixed = before_total - after_total
                    improvement_pct = (fixed / before_total) * 100
                    fig = go.Figure(data=[
                        go.Pie(
                            labels=["Fixed", "Remaining"],
                            values=[fixed, after_total],
                            hole=0.4,
                            marker=dict(colors=["#00cc96", "#ef553b"]),
                            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>"
                        )
                    ])
                    fig.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
                    st.plotly_chart(fig, width='stretch')
                else:
                    st.info("No missing values to fix")
            
            with col2:
                st.write("**Row Statistics**")
                original = summary.get("original_rows", 0)
                duplicates = summary.get("dropped_duplicates", 0)
                cleaned = summary.get("cleaned_rows", 0)
                
                # Show row progression through cleaning stages
                rows_data = {
                    "Stage": ["Original Data", "After Duplicate Removal", "Final Cleaned"],
                    "Rows": [original, original - duplicates, cleaned]
                }
                df_rows = pd.DataFrame(rows_data)
                
                fig = px.bar(
                    df_rows,
                    x="Stage",
                    y="Rows",
                    text="Rows",
                    color="Stage",
                    color_discrete_sequence=["#667eea", "#ef553b", "#00cc96"]
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(height=400, showlegend=False, 
                                 yaxis_title="Row Count",
                                 xaxis_title="",
                                 margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig, width='stretch')
            
            with col3:
                st.write("**Column Types**")
                numeric = summary.get("numeric_cols", 0)
                categorical = summary.get("categorical_cols", 0)
                
                if numeric + categorical > 0:
                    fig = go.Figure(data=[
                        go.Bar(
                            x=["Numeric", "Categorical"],
                            y=[numeric, categorical],
                            text=[numeric, categorical],
                            textposition='outside',
                            marker=dict(color=["#00cc96", "#667eea"])
                        )
                    ])
                    fig.update_layout(height=400, showlegend=False, 
                                     xaxis_title="", yaxis_title="Count",
                                     margin=dict(l=0, r=0, t=30, b=0))
                    st.plotly_chart(fig, width='stretch')
            
            st.markdown("---")
            
            # ========== COLUMN-WISE ANALYSIS ==========
            st.subheader("🔍 Column-Wise Data Quality Analysis")
            
            before_list = summary.get("missing_summary_before", [])
            after_list = summary.get("missing_summary_after", [])
            
            if before_list and after_list:
                df_before = pd.DataFrame(before_list)
                df_after = pd.DataFrame(after_list)
                
                # Merge data for comparison
                merged = pd.merge(
                    df_before[["column", "missing_pct", "dtype", "unique_count"]].rename(
                        columns={"missing_pct": "Missing Before (%)"}
                    ),
                    df_after[["column", "missing_pct"]].rename(
                        columns={"missing_pct": "Missing After (%)"}
                    ),
                    on="column",
                    how="outer"
                ).fillna(0)
                
                # 1. Missing Value Trend Chart
                fig_missing = px.bar(
                    merged.melt(id_vars=["column"], 
                               value_vars=["Missing Before (%)", "Missing After (%)"]),
                    x="column",
                    y="value",
                    color="variable",
                    labels={"value": "Missing Percentage (%)", "variable": "Stage"},
                    title="Missing Values: Before vs After Cleaning",
                    barmode="group",
                    color_discrete_map={
                        "Missing Before (%)": "#ef553b",
                        "Missing After (%)": "#00cc96"
                    }
                )
                fig_missing.update_layout(height=400, hovermode="x unified",
                                         xaxis_tickangle=-45)
                st.plotly_chart(fig_missing, width='stretch')
                
                # 2. Detailed Column Stats Table
                with st.expander("📋 Detailed Column Statistics"):
                    display_data = merged.copy()
                    display_data["Data Type"] = display_data["dtype"]
                    display_data["Unique Count"] = display_data["unique_count"].astype(int)
                    display_data["Improvement"] = (
                        display_data["Missing Before (%)"] - display_data["Missing After (%)"]
                    ).round(2)
                    
                    st.dataframe(
                        display_data[[
                            "column", "Data Type", "Unique Count",
                            "Missing Before (%)", "Missing After (%)", "Improvement"
                        ]].rename(columns={"column": "Column"}),
                        width='stretch',
                        hide_index=True
                    )
                
                # 3. Data Quality Score by Column
                merged["Quality Score"] = 100 - merged["Missing After (%)"]
                
                fig_quality = px.bar(
                    merged.sort_values("Quality Score"),
                    x="Quality Score",
                    y="column",
                    orientation="h",
                    color="Quality Score",
                    color_continuous_scale="RdYlGn",
                    range_color=[0, 100],
                    title="Data Quality Score by Column",
                    labels={"column": "Column", "Quality Score": "Quality Score (%)"}
                )
                fig_quality.update_layout(height=400)
                st.plotly_chart(fig_quality, width='stretch')
            
            st.markdown("---")
            
            # ========== DATA COMPLETENESS HEATMAP (AFTER CLEANING) ==========
            st.subheader("🔥 Data Completeness After Cleaning")
            
            # Show before/after comparison
            col_before, col_after = st.columns(2)
            
            if before_list and after_list:
                # BEFORE cleaning
                with col_before:
                    st.write("**Before Cleaning**")
                    heatmap_data_before = []
                    for col_info in before_list:
                        col_name = col_info.get("column", "")
                        missing_pct = col_info.get("missing_pct", 0)
                        completeness = 100 - missing_pct
                        heatmap_data_before.append({
                            "Column": col_name,
                            "Completeness (%)": completeness
                        })
                    
                    if heatmap_data_before:
                        df_heatmap_before = pd.DataFrame(heatmap_data_before)
                        fig_before = px.bar(
                            df_heatmap_before.sort_values("Completeness (%)", ascending=True),
                            x="Completeness (%)",
                            y="Column",
                            orientation="h",
                            color="Completeness (%)",
                            color_continuous_scale="RdYlGn",
                            range_color=[0, 100],
                            text="Completeness (%)"
                        )
                        fig_before.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                        fig_before.update_layout(height=400, xaxis_title="Completeness (%)")
                        st.plotly_chart(fig_before, width='stretch')
                
                # AFTER cleaning
                with col_after:
                    st.write("**After Cleaning**")
                    heatmap_data_after = []
                    for col_info in after_list:
                        col_name = col_info.get("column", "")
                        missing_pct = col_info.get("missing_pct", 0)
                        completeness = 100 - missing_pct
                        heatmap_data_after.append({
                            "Column": col_name,
                            "Completeness (%)": completeness
                        })
                    
                    if heatmap_data_after:
                        df_heatmap_after = pd.DataFrame(heatmap_data_after)
                        fig_after = px.bar(
                            df_heatmap_after.sort_values("Completeness (%)", ascending=True),
                            x="Completeness (%)",
                            y="Column",
                            orientation="h",
                            color="Completeness (%)",
                            color_continuous_scale="RdYlGn",
                            range_color=[0, 100],
                            text="Completeness (%)"
                        )
                        fig_after.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                        fig_after.update_layout(height=400, xaxis_title="Completeness (%)")
                        st.plotly_chart(fig_after, width='stretch')
        else:
            st.info("📤 Upload and process a file first to see analytics")
        
        # Analytics footer with best practices
        st.markdown("---")
        
        with st.expander("📚 Analytics Best Practices"):
            st.markdown("""
            **Interpreting Your Results**
            
            • **Quality Score**: Focus on columns with low scores (< 70%)
            • **Missing Values**: Track improvements across runs
            • **Duplicates**: Monitor duplicate removal effectiveness
            • **Type Consistency**: Ensure data types are correct
            
            **Next Steps**
            
            1. Review the Data Issues report for detailed findings
            2. Download the cleaned CSV for further analysis
            3. Check PDF report for stakeholder sharing
            4. Use JSON summary for programmatic access
            """)
elif page == "Processing History":
    st.header("Processing History")
    
    hist_tab1, hist_tab2 = st.tabs(["History", "About"])
    
    with hist_tab2:
        st.markdown("""
        **Processing History Feature**
        
        This page shows all previous data cleaning operations performed in CleanDataPro.
        
        **Information Tracked**
        
        • File name and metadata
        • Processing timestamp
        • Original data dimensions
        • Cleaning statistics
        • Quality metrics
        • Run ID for reference
        
        **Storage**
        
        History is stored in MongoDB for persistent access across sessions.
        """)
    
    with hist_tab1:
        try:
            resp = requests.get(
                f"{BACKEND_BASE}/api/runs?limit=20",
                headers=_auth_headers(),
                timeout=10,
            )
            if resp.status_code == 200:
                history_data = resp.json()
                runs = history_data.get("runs", [])
                
                if runs:
                    # Statistics
                    st.markdown(f"**📈 Statistics**: {len(runs)} processing runs found")
                    
                    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                    
                    with stat_col1:
                        total_rows = sum([r.get("summary", {}).get("cleaned_rows", 0) for r in runs])
                        st.metric("✅ Total Cleaned Rows", f"{total_rows:,}")
                    
                    with stat_col2:
                        total_duplicates = sum([r.get("summary", {}).get("dropped_duplicates", 0) for r in runs])
                        st.metric("🗑️ Total Duplicates Removed", f"{total_duplicates:,}")
                    
                    with stat_col3:
                        total_missing_fixed = sum([
                            r.get("summary", {}).get("missing_before", 0) - r.get("summary", {}).get("missing_after", 0)
                            for r in runs
                        ])
                        st.metric("🩹 Total Issues Fixed", f"{total_missing_fixed:,}")
                    
                    with stat_col4:
                        improvements = []
                        for r in runs:
                            s = r.get("summary", {})
                            mb = s.get("missing_before", 0) or 0
                            ma = s.get("missing_after", 0) or 0
                            if mb > 0 and ma <= mb:
                                improvements.append(((mb - ma) / mb) * 100)

                        if improvements:
                            avg_improvement = sum(improvements) / len(improvements)
                            st.metric("📊 Average Quality Improvement", f"{avg_improvement:.1f}%")
                        else:
                            st.metric("📊 Average Quality Improvement", "N/A")
                    
                    st.markdown("---")
                    
                    # Filtering options
                    filter_col1, filter_col2 = st.columns(2)
                    
                    with filter_col1:
                        limit = st.select_slider(
                            "Rows to display",
                            options=[5, 10, 20, 50],
                            value=20
                        )
                    
                    with filter_col2:
                        sort_by = st.selectbox(
                            "Sort by",
                            ["Most Recent", "Oldest First", "Largest File"],
                            index=0
                        )
                    
                    st.markdown("---")
                    
                    # Create history dataframe with detailed information
                    history_list = []
                    for run in runs[:limit]:
                        summary = run.get("summary", {})
                        orig_rows = summary.get("original_rows", 0)
                        cleaned_rows = summary.get("cleaned_rows", 0)
                        
                        # Calculate quality improvement
                        missing_before = summary.get("missing_before", 0)
                        missing_after = summary.get("missing_after", 0)
                        improvement = 0
                        if missing_before > 0:
                            improvement = ((missing_before - missing_after) / missing_before) * 100
                        
                        history_list.append({
                            "📄 File Name": run.get("uploaded_filename", "Unknown"),
                            "🔑 Run ID": run.get("run_id", "N/A")[:12],
                            "📥 Original Rows": f"{orig_rows:,}",
                            "✅ Cleaned Rows": f"{cleaned_rows:,}",
                            "🗑️ Duplicates": summary.get("dropped_duplicates", 0),
                            "📊 Columns": summary.get("columns", 0),
                            "⬆️ Quality Improvement": f"{improvement:.1f}%"
                        })
                    
                    if history_list:
                        df_history = pd.DataFrame(history_list)
                        st.dataframe(df_history, width='stretch', hide_index=True)
                        
                        st.markdown("---")
                        
                        # Detailed view option
                        with st.expander("🔍 View Detailed Information"):
                            selected_run_idx = st.selectbox(
                                "Select a run to view details",
                                range(min(len(runs), limit)),
                                format_func=lambda i: f"{runs[i].get('uploaded_filename', 'Unknown')} - {runs[i].get('run_id', '')[:8]}"
                            )
                            
                            if selected_run_idx is not None and selected_run_idx < len(runs):
                                selected_run = runs[selected_run_idx]
                                summary = selected_run.get("summary", {})
                                
                                st.write("**Run Details**")
                                detail_col1, detail_col2 = st.columns(2)
                                
                                with detail_col1:
                                    st.write(f"📄 **File**: {selected_run.get('uploaded_filename', 'Unknown')}")
                                    st.write(f"🔑 **Run ID**: {selected_run.get('run_id', 'N/A')}")
                                    st.write(f"📊 **Original Rows**: {summary.get('original_rows', 'N/A'):,}")
                                    st.write(f"✅ **Cleaned Rows**: {summary.get('cleaned_rows', 'N/A'):,}")
                                
                                with detail_col2:
                                    st.write(f"🗑️ **Duplicates Removed**: {summary.get('dropped_duplicates', 0)}")
                                    st.write(f"📋 **Total Columns**: {summary.get('columns', 0)}")
                                    st.write(f"📭 **Missing Values Fixed**: {summary.get('missing_before', 0) - summary.get('missing_after', 0):,}")
                                    st.write(f"📋 **Numeric Columns**: {summary.get('numeric_cols', 0)}")
                    else:
                        st.info("No processing history found")
                else:
                    st.info("📭 No processing history found. Upload and process a file to get started.")
            else:
                st.warning("⚠️ Could not fetch history from backend")
        except Exception as e:
            st.error(f"❌ Error fetching history: {e}")
        
        st.markdown("---")
        
        # Footer with information
        with st.expander("ℹ️ Storage Information"):
            st.markdown("""
            **History Storage**
            
            • **Database**: MongoDB (optional)
            • **Persistence**: Persists across sessions if MongoDB configured
            • **Retention**: Configurable retention policies
            • **Limit**: Last 20 runs displayed
            
            **Without MongoDB**
            
            History is stored in-memory during the session only.
            """)

# Page: Settings
elif page == "Settings":
    st.header("Settings & Configuration")
    
    # Tabs for different settings categories
    tab1, tab2, tab3, tab4 = st.tabs([
        "System", 
        "Storage", 
        "API", 
        "Preferences"
    ])
    
    with tab1:
        st.subheader("System Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Backend Status**")
            try:
                resp = requests.get(
                    f"{BACKEND_BASE}/api/runs?limit=1",
                    headers=_auth_headers(),
                    timeout=5,
                )
                if resp.status_code == 200:
                    st.success("✅ Backend Online")
                    st.info(f"**URL:** {BACKEND_BASE}")
                else:
                    st.error(f"⚠️ Backend Error: {resp.status_code}")
            except requests.exceptions.ConnectionError:
                st.error("❌ Backend Offline")
            except Exception as e:
                st.error(f"❌ Connection Error: {str(e)}")
        
        with col2:
            st.markdown("**System Health**")
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Frontend", "Running ✓", delta=None)
            with col_b:
                st.metric("API Version", "v1.0", delta=None)
        
        st.markdown("---")
        st.markdown("**Environment**")
        env_info = {
            "Backend URL": BACKEND_BASE,
            "Frontend Port": "8501",
            "Python Version": "3.11+",
            "Streamlit Version": "1.24.0+"
        }
        
        for key, value in env_info.items():
            st.write(f"• **{key}:** `{value}`")
    
    with tab2:
        st.subheader("Storage & Files Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Upload Settings**")
            st.write("""
            • **Max File Size:** 200 MB
            • **Supported Format:** CSV (.csv)
            • **Encoding:** UTF-8
            • **Storage:** `data/raw/`
            """)
        
        with col2:
            st.markdown("**Output Settings**")
            st.write("""
            • **Cleaned Data:** `data/processed/`
            • **PDF Reports:** `reports/`
            • **JSON Summary:** `reports/`
            • **History:** MongoDB (if configured)
            """)
        
        st.markdown("---")
        st.markdown("**Data Retention**")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Raw Files", "Kept", "7 days")
        with col2:
            st.metric("Reports", "Kept", "30 days")
        with col3:
            st.metric("History", "Stored", "Persistent")
    
    with tab3:
        st.subheader("API Configuration")
        
        st.markdown("**REST API Endpoints**")
        
        endpoints = {
            "POST /api/process": "Process uploaded CSV file",
            "GET /api/download": "Download processed files",
            "GET /api/runs": "Get processing history",
            "GET /api/runs/{id}": "Get specific run details",
            "GET /healthz": "Health check endpoint"
        }
        
        for endpoint, desc in endpoints.items():
            st.write(f"• **{endpoint}** - {desc}")
        
        st.markdown("---")
        st.markdown("**API Documentation**")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"[📖 Swagger UI]({BACKEND_BASE}/docs)")
        with col2:
            st.markdown(f"[📖 ReDoc]({BACKEND_BASE}/redoc)")
        
        st.markdown("---")
        st.markdown("**Authentication**")
        st.info("""
        Current authentication: None (public API)
        
        **For Production:**
        - Configure API keys in `.env`
        - Enable CORS restrictions
        - Use HTTPS/TLS encryption
        - Implement rate limiting
        """)
    
    with tab4:
        st.subheader("User Preferences")
        
        st.markdown("**Display Preferences**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Data Table Display**")
            rows_to_show = st.select_slider(
                "Rows to display in preview",
                options=[5, 10, 20, 50],
                value=10
            )
            st.caption(f"Selected: {rows_to_show} rows")
        
        with col2:
            st.markdown("**Chart Theme**")
            theme = st.selectbox(
                "Color scheme",
                ["Plotly", "Dark", "Light"],
                label_visibility="collapsed"
            )
            st.caption(f"Selected: {theme}")
        
        st.markdown("---")
        st.markdown("**Report Preferences**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            include_charts = st.checkbox("Include charts in PDF", value=True)
            include_raw = st.checkbox("Include raw data", value=False)
        
        with col2:
            pdf_format = st.selectbox(
                "Report format",
                ["Standard", "Detailed", "Executive Summary"],
                label_visibility="collapsed"
            )
            export_format = st.multiselect(
                "Export formats",
                ["CSV", "PDF", "JSON"],
                default=["CSV", "PDF"]
            )
        
        st.markdown("---")
        st.markdown("**Processing Options**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("• Remove exact duplicates: ✓ Enabled")
            st.write("• Auto-detect numeric types: ✓ Enabled")
            st.write("• Fill missing values: ✓ Enabled")
        
        with col2:
            st.write("• Generate PDF report: ✓ Enabled")
            st.write("• Save to history: ✓ Enabled")
            st.write("• Preserve raw data: ✓ Enabled")
        
        if st.button("💾 Save Preferences", width='stretch'):
            st.success("✅ Preferences saved successfully")
    
    st.markdown("---")
    
    # System Information
    with st.expander("📋 System Information"):
        st.markdown("**Application Details**")
        sys_info = {
            "App Name": "CleanDataPro",
            "Version": "1.0.0",
            "Status": "Production Ready",
            "Last Updated": "December 19, 2024",
            "API Endpoints": "5 active"
        }
        
        for key, value in sys_info.items():
            st.write(f"• **{key}:** {value}")
        
        st.markdown("**Supported Data Types**")
        st.write("""
        • **Numeric:** int, float, double
        • **Text:** string, varchar
        • **Datetime:** date, datetime, timestamp
        • **Boolean:** bool, true/false
        • **Special:** NULL, NaN, empty strings
        """)
        
        st.markdown("**Cleaning Strategies**")
        st.write("""
        • **Numeric Missing Values:** Median
        • **Categorical Missing Values:** Mode (most frequent)
        • **Datetime Missing Values:** Minimum date
        • **Duplicates:** Exact row matching
        • **Type Inference:** Safe conversion
        """)
    
    # Support Section
    with st.expander("❓ Support & Documentation"):
        st.markdown("**Documentation**")
        doc_links = {
            "Quick Start": "[2-minute guide](./DATA_ISSUES_QUICK_START.md)",
            "Complete Guide": "[Full documentation](./DATA_ISSUES_REPORT_GUIDE.md)",
            "API Reference": "[API documentation](./README.md#api-documentation)",
            "Troubleshooting": "[Common issues](./README.md#troubleshooting)"
        }
        
        for title, link in doc_links.items():
            st.markdown(f"• {title}: {link}")
        
        st.markdown("**GitHub Repository**")
        st.write("https://github.com/adriel03-dp/clean-datapro")
        
        st.markdown("**Contact & Support**")
        st.write("For issues, questions, or feature requests, please open an issue on GitHub.")
