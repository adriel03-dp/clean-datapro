"""Authentication pages for Streamlit"""
import streamlit as st
import requests
import os


BACKEND_BASE = os.environ.get("CLEAN_DATAPRO_BACKEND", "http://localhost:8000")

def show_login_page():
    """Render login/signup screen (dark mode)."""
    st.markdown(
        """
        <style>
        :root {
            --cdp-bg: #0e1117;
            --cdp-text: #e6e6e6;
            --cdp-card: rgba(24, 28, 38, 0.92);
            --cdp-border: rgba(255, 255, 255, 0.10);
            --cdp-v1: #00ff88;
            --cdp-v2: #00c853;
            --cdp-v3: #39ff14;
            --cdp-v4: #00ffcc;
        }
        @keyframes cdpFadeUp {
            from { opacity: 0; transform: translateY(10px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes cdpGradientMove {
            0%   { background-position: 0% 50%; }
            50%  { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        @keyframes cdpLightsDrift {
            0%   { transform: translate3d(-2%, -1%, 0) scale(1.00); opacity: 0.55; }
            50%  { transform: translate3d(2%, 1%, 0) scale(1.05); opacity: 0.70; }
            100% { transform: translate3d(-2%, -1%, 0) scale(1.00); opacity: 0.55; }
        }
        .stApp {
            background: var(--cdp-bg);
            color: var(--cdp-text);
            position: relative;
        }

        /* Ensure Streamlit content stays above the background light wash */
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > .main,
        section.main,
        [data-testid="stMain"] {
            position: relative;
            z-index: 2;
        }

        /* Blurry light wash across the whole screen */
        .stApp::before {
            content: "";
            position: fixed;
            inset: -25%;
            background:
              radial-gradient(circle at 18% 30%, rgba(0, 255, 136, 0.32), transparent 55%),
              radial-gradient(circle at 82% 70%, rgba(255, 77, 77, 0.22), transparent 58%),
              radial-gradient(circle at 55% 50%, rgba(0, 255, 204, 0.10), transparent 60%);
            filter: blur(70px);
            opacity: 0.45;
            animation: cdpLightsDrift 7.5s ease-in-out infinite;
            pointer-events: none;
            z-index: 0;
        }
        .stApp::after {
            content: "";
            position: fixed;
            inset: -35%;
            background: linear-gradient(
              120deg,
              transparent 10%,
              rgba(0, 255, 136, 0.10) 38%,
              rgba(255, 77, 77, 0.08) 62%,
              transparent 90%
            );
            filter: blur(90px);
            opacity: 0.30;
            animation: cdpLightsDrift 10s ease-in-out infinite reverse;
            pointer-events: none;
            z-index: 0;
        }

        /* Floating feature cards (decorative) */
        .cdp-floating {
            position: fixed;
            z-index: 2;
            pointer-events: none;
        }

        /* Decorative animated charts */
        @keyframes cdpFloat {
            0%   { transform: translateY(0px); }
            50%  { transform: translateY(-10px); }
            100% { transform: translateY(0px); }
        }
        @keyframes cdpBounce {
            0%, 100% { transform: translateY(0px); }
            50%      { transform: translateY(-14px); }
        }
        @keyframes cdpPulse {
            0%, 100% { opacity: 0.85; }
            50%      { opacity: 1; }
        }

        .cdp-chart {
            position: fixed;
            z-index: 1;
            pointer-events: none;
            width: 220px;
            padding: 16px;
            border-radius: 14px;
            background: rgba(10, 14, 18, 0.55);
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
            backdrop-filter: blur(6px);
        }
        .cdp-chart .cdp-chart-title {
            font-size: 0.78rem;
            opacity: 0.8;
            margin-bottom: 10px;
        }
        .cdp-green { color: var(--cdp-v2); }
        .cdp-red { color: #ff4d4d; }

        /* Mini bar chart */
        .cdp-bars {
            display: flex;
            gap: 8px;
            align-items: flex-end;
            height: 70px;
        }
        .cdp-bars span {
            width: 16px;
            border-radius: 8px;
            background: linear-gradient(180deg, var(--cdp-v1), var(--cdp-v2));
            animation: cdpPulse 1.6s ease-in-out infinite;
        }
        .cdp-bars span.red {
            background: linear-gradient(180deg, #ff6b6b, #ff2d2d);
        }

        /* Mini line chart */
        .cdp-line {
                        height: 84px;
            border-radius: 12px;
            background:
              radial-gradient(circle at 25% 65%, rgba(0, 255, 136, 0.22), transparent 42%),
              radial-gradient(circle at 75% 35%, rgba(255, 77, 77, 0.18), transparent 45%),
              linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
            border: 1px solid rgba(255,255,255,0.06);
            position: relative;
            overflow: hidden;
        }
        .cdp-line svg {
            position: absolute;
            inset: 0;
        }
        .cdp-line path {
            stroke-linecap: round;
            stroke-linejoin: round;
            fill: none;
            stroke-width: 3.2;
            stroke-dasharray: 260;
            stroke-dashoffset: 260;
            animation: cdpDraw 2.6s ease-in-out infinite;
        }
        @keyframes cdpDraw {
            0%   { stroke-dashoffset: 260; opacity: 0.65; }
            40%  { stroke-dashoffset: 0; opacity: 1; }
            100% { stroke-dashoffset: 0; opacity: 0.75; }
        }

        /* Mini donut */
        .cdp-donut {
            width: 104px;
            height: 104px;
            border-radius: 999px;
            margin: 2px auto 0;
            background: conic-gradient(var(--cdp-v2) 0 58%, #ff2d2d 58% 78%, rgba(255,255,255,0.10) 78% 100%);
            position: relative;
            animation: cdpSpin 3.8s linear infinite;
        }
        .cdp-donut::after {
            content: "";
            position: absolute;
            inset: 16px;
            background: rgba(10, 14, 18, 0.78);
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.06);
        }
        @keyframes cdpSpin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .cdp-chart-1 { top: 420px; left: 96px; animation: cdpFloat 3.2s ease-in-out infinite; }
        /* Place Run trend between top-left feature and Quality/Issues */
        .cdp-chart-2 { top: 250px; left: 96px; animation: cdpBounce 3.0s ease-in-out infinite; }
        /* Keep Completion on the right */
        .cdp-chart-3 { bottom: 260px; right: 132px; animation: cdpFloat 3.6s ease-in-out infinite; }
        .cdp-badge {
            width: 285px;
            padding: 16px 16px;
            border-radius: 14px;
            background: rgba(10, 14, 18, 0.55);
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
            backdrop-filter: blur(6px);
        }
        .cdp-badge h4 {
            margin: 0 0 6px 0;
            font-size: 1.05rem;
            letter-spacing: 0.2px;
            background: linear-gradient(90deg, var(--cdp-v1), var(--cdp-v2), var(--cdp-v3));
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }
        .cdp-badge p {
            margin: 0;
            opacity: 0.85;
            font-size: 0.92rem;
            line-height: 1.25rem;
        }
        .cdp-badge {
            animation: cdpFadeUp 520ms ease-out;
        }
        .cdp-float-1 { top: 92px; left: 92px; }
        .cdp-float-2 { top: 128px; right: 92px; }
        .cdp-float-3 { bottom: 104px; left: 92px; }
        .cdp-float-4 { bottom: 104px; right: 92px; }

        @media (max-width: 1100px) {
            .cdp-floating, .cdp-chart { display: none; }
        }
        [data-testid="stSidebar"] {
            display: none;
        }
        [data-testid="stMainBlockContainer"] {
            padding-top: 4rem;
            max-width: 520px;
            animation: cdpFadeUp 260ms ease-out;
            position: relative;
            z-index: 3;
        }
        div[data-testid="stForm"] {
            position: relative;
            background: var(--cdp-card);
            border: 1px solid var(--cdp-border);
            border-radius: 14px;
            padding: 28px;
            animation: cdpFadeUp 320ms ease-out;
            overflow: hidden;
                        /* Shadow + glow coming from behind the form */
                        box-shadow:
                            0 26px 70px rgba(0, 0, 0, 0.70),
                            0 0 0 1px rgba(255, 255, 255, 0.04),
                            0 0 60px rgba(0, 255, 136, 0.18),
                            0 0 46px rgba(255, 77, 77, 0.10);
        }
        /* Vibrant animated glow behind the form */
        div[data-testid="stForm"]::before {
            content: "";
            position: absolute;
            inset: -2px;
            border-radius: 16px;
                        background:
                            radial-gradient(circle at 18% 28%, rgba(0, 200, 83, 0.45), transparent 52%),
                            radial-gradient(circle at 82% 72%, rgba(255, 45, 45, 0.33), transparent 56%),
                            linear-gradient(120deg, var(--cdp-v1), var(--cdp-v2), var(--cdp-v3), var(--cdp-v4));
            background-size: 300% 300%;
            animation: cdpGradientMove 3.2s ease-in-out infinite;
            filter: blur(14px);
            opacity: 0.55;
            z-index: 0;
            pointer-events: none;
        }
                /* Extra soft blobs for green/red depth */
                div[data-testid="stForm"]::after {
                        content: "";
                        position: absolute;
                        inset: 0;
                        border-radius: 14px;
                        background:
                            radial-gradient(circle at 22% 18%, rgba(0, 255, 136, 0.22), transparent 50%),
                            radial-gradient(circle at 78% 82%, rgba(255, 77, 77, 0.18), transparent 52%);
                        filter: blur(18px);
                        opacity: 0.9;
                        z-index: 0;
                        pointer-events: none;
                }
        /* Keep the actual inputs above the glow */
        div[data-testid="stForm"] > * {
            position: relative;
            z-index: 1;
        }

        /* Animated gradient title */
        .cdp-title {
            background: linear-gradient(90deg, var(--cdp-v1), var(--cdp-v2), var(--cdp-v3), var(--cdp-v1));
            background-size: 300% 100%;
            animation: cdpGradientMove 4.5s ease-in-out infinite;
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            margin-bottom: 0.25rem;
        }
        div[data-testid="stForm"] button {
            transition: transform 120ms ease, filter 120ms ease;
        }
        div[data-testid="stForm"] button:hover {
            filter: brightness(1.05);
            transform: translateY(-1px);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="cdp-floating cdp-float-1"><div class="cdp-badge">
            <h4>Clean in minutes</h4>
            <p>Auto-detect missing values, duplicates, and basic format issues.</p>
        </div></div>
        <div class="cdp-floating cdp-float-2"><div class="cdp-badge">
            <h4>Clear reports</h4>
            <p>Generate a summary that explains what changed and why it matters.</p>
        </div></div>
        <div class="cdp-floating cdp-float-3"><div class="cdp-badge">
            <h4>Analytics ready</h4>
            <p>Get cleaner data so charts and insights are more reliable.</p>
        </div></div>
        <div class="cdp-floating cdp-float-4"><div class="cdp-badge">
            <h4>Track your runs</h4>
            <p>Keep history of processing so you can compare and repeat quickly.</p>
        </div></div>

        <div class="cdp-chart cdp-chart-1">
            <div class="cdp-chart-title"><span class="cdp-green">Quality ↑</span> / <span class="cdp-red">Issues ↓</span></div>
            <div class="cdp-bars">
                <span style="height: 22px"></span>
                <span style="height: 44px"></span>
                <span class="red" style="height: 18px"></span>
                <span style="height: 56px"></span>
                <span class="red" style="height: 26px"></span>
                <span style="height: 62px"></span>
            </div>
        </div>

        <div class="cdp-chart cdp-chart-2">
            <div class="cdp-chart-title">Run trend</div>
            <div class="cdp-line">
                <svg viewBox="0 0 240 90" preserveAspectRatio="none" aria-hidden="true">
                    <path d="M6,70 C40,52 58,58 84,44 C112,26 122,42 148,30 C176,18 192,26 234,18" style="stroke: var(--cdp-v2);"></path>
                    <path d="M6,62 C38,70 60,56 84,60 C108,64 124,52 146,56 C170,60 190,52 234,58" style="stroke: #ff2d2d; opacity:0.9;"></path>
                </svg>
            </div>
        </div>

        <div class="cdp-chart cdp-chart-3">
            <div class="cdp-chart-title">Completion</div>
            <div class="cdp-donut" aria-hidden="true"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "auth_tab" not in st.session_state:
        st.session_state.auth_tab = "login"

    st.markdown("<h1 class='cdp-title' style='text-align:center;'>CleanDataPro</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; opacity:0.85; margin-top:0;'>Sign in to continue</p>", unsafe_allow_html=True)

    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    with tab_login:
        _render_login_form()

    with tab_signup:
        _render_signup_form()


def _safe_error_message(res: requests.Response) -> str:
    try:
        payload = res.json()
        if isinstance(payload, dict) and payload.get("detail"):
            return str(payload.get("detail"))
        return str(payload)
    except Exception:
        text = (res.text or "").strip()
        return text if text else "Request failed"


def _render_login_form():
    """Simple login form"""
    st.markdown("<h3 style='text-align:center; margin-top:0;'>Login</h3>", unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="...@gmail.com")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign In", use_container_width=True)

        if submit:
            email = (email or "").strip()
            if not email or not password:
                st.error("Email and password are required.")
                return

            with st.spinner("Signing in..."):
                try:
                    res = requests.post(
                        f"{BACKEND_BASE}/api/auth/login",
                        json={"email": email, "password": password},
                        timeout=10,
                    )
                except requests.RequestException:
                    st.error("Could not reach the backend. Make sure it is running.")
                    return

            if res.status_code == 200:
                data = res.json()
                st.session_state.token = data.get("token")
                st.session_state.email = data.get("email", email)
                st.session_state.name = data.get("name")
                st.session_state.authenticated = True
                st.success("Logged in.")
                st.rerun()
            else:
                st.error(_safe_error_message(res))


def _render_signup_form():
    """Simple signup form"""
    st.markdown("<h3 style='text-align:center; margin-top:0;'>Create account</h3>", unsafe_allow_html=True)

    with st.form("signup_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Create Account", use_container_width=True)

        if submit:
            name = (name or "").strip()
            email = (email or "").strip()
            if not name or not email or not password or not confirm:
                st.error("All fields are required.")
                return
            if "@" not in email or "." not in email:
                st.error("Please enter a valid email.")
                return
            if len(password) < 8:
                st.error("Password must be at least 8 characters.")
                return
            if password != confirm:
                st.error("Passwords do not match.")
                return

            with st.spinner("Creating account..."):
                try:
                    res = requests.post(
                        f"{BACKEND_BASE}/api/auth/register",
                        json={"name": name, "email": email, "password": password},
                        timeout=10,
                    )
                except requests.RequestException:
                    st.error("Could not reach the backend. Make sure it is running.")
                    return

            if res.status_code == 200:
                data = res.json()
                st.session_state.token = data.get("token")
                st.session_state.email = data.get("email", email)
                st.session_state.name = data.get("name", name)
                st.session_state.authenticated = True
                st.success("Account created.")
                st.rerun()
            else:
                st.error(_safe_error_message(res))


def show_logout_button():
    """Show logout button in sidebar"""
    with st.sidebar:
        if st.session_state.get("authenticated"):
            st.markdown(f"**Logged in as:** {st.session_state.get('name', st.session_state.get('email'))}")
            
            if st.button("Logout", use_container_width=True):
                st.session_state.token = None
                st.session_state.email = None
                st.session_state.name = None
                st.session_state.authenticated = False
                st.rerun()


def require_auth():
    """Check if user is authenticated, redirect to login if not"""
    if not st.session_state.get("authenticated"):
        show_login_page()
        st.stop()
