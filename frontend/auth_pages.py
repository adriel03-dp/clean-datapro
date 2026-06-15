"""Authentication pages for Streamlit"""
import streamlit as st
import requests

from config import BACKEND_BASE

AUTH_TIMEOUT = (10, 90)


def _backend_connection_error() -> None:
    st.error(
        "The backend did not respond. On Render Free, the first request can "
        "take up to a minute while the service wakes up. Please try again."
    )


def _show_login_page_legacy():
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
            position: absolute;
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
            position: absolute;
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

        .cdp-chart-1 { top: 445px; left: 6vw; animation: cdpFloat 3.2s ease-in-out infinite; }
        .cdp-chart-2 { top: 245px; left: 6vw; animation: cdpBounce 3.0s ease-in-out infinite; }
        .cdp-chart-3 { top: 360px; right: 7vw; animation: cdpFloat 3.6s ease-in-out infinite; }
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
        .cdp-float-1 { top: 55px; left: 6vw; }
        .cdp-float-2 { top: 75px; right: 6vw; }
        .cdp-float-3 { top: 650px; left: 6vw; }
        .cdp-float-4 { top: 650px; right: 6vw; }

        @media (max-width: 1450px), (max-height: 820px) {
            .cdp-floating, .cdp-chart { display: none; }
        }
        [data-testid="stSidebar"] {
            display: none;
        }
        [data-testid="stMainBlockContainer"] {
            padding-top: 2rem;
            padding-bottom: 3rem;
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
            padding: 24px;
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
        @media (max-width: 700px) {
            [data-testid="stMainBlockContainer"] {
                padding: 1.25rem 1rem 2rem;
            }
            div[data-testid="stForm"] {
                padding: 20px;
                border-radius: 12px;
            }
        }
        @media (prefers-reduced-motion: reduce) {
            .stApp::before,
            .stApp::after,
            .cdp-floating,
            .cdp-chart,
            .cdp-title,
            div[data-testid="stForm"],
            div[data-testid="stForm"]::before {
                animation: none !important;
            }
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


def show_login_page():
    """Render the premium light authentication experience."""
    st.markdown(
        """
        <style>
        :root {
            --auth-ink: #0b1739;
            --auth-muted: #65708a;
            --auth-blue: #246bfe;
            --auth-green: #12b76a;
            --auth-red: #ff4d5e;
            --auth-line: #e4e9f2;
            --auth-soft: #f5f8ff;
            --auth-card: rgba(255, 255, 255, 0.94);
        }
        @keyframes authRise {
            from { opacity: 0; transform: translateY(16px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes authDrift {
            0%, 100% { transform: translate3d(0, 0, 0); }
            50% { transform: translate3d(0, -8px, 0); }
        }
        .stApp {
            color: var(--auth-ink);
            background:
                radial-gradient(circle at 7% 8%, rgba(36, 107, 254, 0.12), transparent 28%),
                radial-gradient(circle at 88% 82%, rgba(18, 183, 106, 0.10), transparent 26%),
                linear-gradient(135deg, #ffffff 0%, #f7faff 48%, #f2f7ff 100%);
        }
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stSidebar"] {
            display: none;
        }
        [data-testid="stMainBlockContainer"] {
            max-width: 1180px;
            padding: 2.5rem 2rem 3rem;
        }
        [data-testid="stHorizontalBlock"] {
            align-items: center;
            gap: 4rem;
            min-height: calc(100vh - 5.5rem);
        }
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {
            padding: 1rem 0;
            animation: authRise 520ms ease-out both;
        }
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child {
            padding: 2rem;
            border: 1px solid rgba(222, 228, 240, 0.9);
            border-radius: 24px;
            background: var(--auth-card);
            box-shadow:
                0 28px 70px rgba(30, 64, 175, 0.12),
                0 8px 24px rgba(15, 23, 42, 0.06);
            backdrop-filter: blur(18px);
            animation: authRise 520ms 90ms ease-out both;
        }
        .auth-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 2.2rem;
        }
        .auth-logo {
            display: grid;
            place-items: center;
            width: 44px;
            height: 44px;
            border-radius: 13px;
            color: white;
            font-size: 1.35rem;
            font-weight: 900;
            background: linear-gradient(145deg, var(--auth-blue), #1c9cff);
            box-shadow: 0 10px 24px rgba(36, 107, 254, 0.25);
        }
        .auth-brand-name {
            color: var(--auth-ink);
            font-size: 1.18rem;
            font-weight: 800;
            letter-spacing: -0.03em;
        }
        .auth-brand-name span { color: var(--auth-blue); }
        .auth-brand-tag {
            color: var(--auth-muted);
            font-size: 0.72rem;
            margin-top: 1px;
        }
        .auth-hero h1 {
            max-width: 560px;
            margin: 0;
            color: var(--auth-ink);
            font-size: clamp(2.35rem, 4.4vw, 4.35rem);
            line-height: 0.98;
            letter-spacing: -0.055em;
        }
        .auth-hero h1 .blue { color: var(--auth-blue); }
        .auth-hero h1 .green { color: var(--auth-green); }
        .auth-hero > p {
            max-width: 540px;
            margin: 1.25rem 0 1.65rem;
            color: var(--auth-muted);
            font-size: 1rem;
            line-height: 1.65;
        }
        .auth-features {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        .auth-feature {
            display: grid;
            grid-template-columns: 42px 1fr;
            gap: 12px;
            align-items: center;
            padding: 14px;
            border: 1px solid var(--auth-line);
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.78);
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.04);
        }
        .auth-feature-icon {
            display: grid;
            place-items: center;
            width: 42px;
            height: 42px;
            border-radius: 12px;
            color: var(--auth-blue);
            font-size: 1.15rem;
            background: #edf4ff;
        }
        .auth-feature:nth-child(2) .auth-feature-icon {
            color: var(--auth-green);
            background: #eafbf3;
        }
        .auth-feature:nth-child(3) .auth-feature-icon {
            color: #7c3aed;
            background: #f3efff;
        }
        .auth-feature:nth-child(4) .auth-feature-icon {
            color: var(--auth-red);
            background: #fff0f2;
        }
        .auth-feature strong {
            display: block;
            color: var(--auth-ink);
            font-size: 0.84rem;
        }
        .auth-feature small {
            display: block;
            margin-top: 2px;
            color: var(--auth-muted);
            font-size: 0.69rem;
            line-height: 1.35;
        }
        .auth-insights {
            margin-top: 14px;
            padding: 16px;
            border: 1px solid var(--auth-line);
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.88);
        }
        .auth-insights-label {
            color: var(--auth-muted);
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }
        .auth-metrics {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-top: 12px;
        }
        .auth-metric {
            padding: 12px;
            border-radius: 13px;
            background: var(--auth-soft);
        }
        .auth-metric span {
            display: block;
            color: var(--auth-muted);
            font-size: 0.66rem;
        }
        .auth-metric strong {
            display: block;
            margin-top: 4px;
            color: var(--auth-ink);
            font-size: 1.05rem;
        }
        .auth-metric em {
            color: var(--auth-green);
            font-size: 0.65rem;
            font-style: normal;
            font-weight: 700;
        }
        .auth-card-head {
            margin-bottom: 1.15rem;
        }
        .auth-card-head .eyebrow {
            color: var(--auth-blue);
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }
        .auth-card-head h2 {
            margin: 0.35rem 0 0.35rem;
            color: var(--auth-ink);
            font-size: 1.8rem;
            letter-spacing: -0.035em;
        }
        .auth-card-head p {
            margin: 0;
            color: var(--auth-muted);
            font-size: 0.86rem;
        }
        [data-baseweb="tab-list"] {
            gap: 8px;
            padding: 5px;
            border-radius: 12px;
            background: #f1f5fb;
        }
        [data-baseweb="tab"] {
            flex: 1;
            justify-content: center;
            height: 42px;
            border-radius: 9px;
            color: var(--auth-muted);
            font-weight: 700;
        }
        [aria-selected="true"][data-baseweb="tab"] {
            color: var(--auth-blue);
            background: white;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);
        }
        [data-baseweb="tab-highlight"],
        [data-baseweb="tab-border"] {
            display: none;
        }
        div[data-testid="stForm"] {
            margin-top: 0.9rem;
            padding: 0;
            border: 0;
            background: transparent;
        }
        div[data-testid="stForm"] h3 {
            margin: 0 0 0.2rem;
            color: var(--auth-ink);
            font-size: 1.2rem;
            letter-spacing: -0.02em;
        }
        div[data-testid="stTextInput"] label p {
            color: #26324d;
            font-size: 0.78rem;
            font-weight: 700;
        }
        div[data-testid="stTextInput"] input {
            min-height: 48px;
            color: var(--auth-ink);
            border: 1px solid #dfe5ef;
            border-radius: 10px;
            background: #fbfcff;
            box-shadow: none;
        }
        div[data-testid="stTextInput"] input:focus {
            border-color: var(--auth-blue);
            box-shadow: 0 0 0 3px rgba(36, 107, 254, 0.12);
        }
        div[data-testid="stFormSubmitButton"] button {
            min-height: 48px;
            margin-top: 0.4rem;
            border: 0;
            border-radius: 10px;
            color: white;
            font-weight: 800;
            background: linear-gradient(100deg, var(--auth-blue), #2855f7);
            box-shadow: 0 10px 22px rgba(36, 107, 254, 0.22);
            transition: transform 150ms ease, box-shadow 150ms ease;
        }
        div[data-testid="stFormSubmitButton"] button:hover {
            color: white;
            transform: translateY(-1px);
            box-shadow: 0 14px 26px rgba(36, 107, 254, 0.28);
        }
        [data-testid="stAlert"] {
            border-radius: 11px;
            font-size: 0.82rem;
        }
        .auth-secure {
            margin-top: 1rem;
            color: var(--auth-muted);
            font-size: 0.72rem;
            text-align: center;
        }
        @media (max-width: 900px) {
            [data-testid="stMainBlockContainer"] {
                max-width: 620px;
                padding: 1.5rem 1rem 2.5rem;
            }
            [data-testid="stHorizontalBlock"] {
                display: block;
                min-height: auto;
            }
            [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {
                display: none;
            }
            [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child {
                width: 100% !important;
                padding: 1.35rem;
                border-radius: 18px;
            }
        }
        @media (prefers-reduced-motion: reduce) {
            [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
                animation: none !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    intro, auth = st.columns([1.08, 0.92], gap="large")

    with intro:
        st.markdown(
            """
            <section class="auth-hero">
                <div class="auth-brand">
                    <div class="auth-logo">C</div>
                    <div>
                        <div class="auth-brand-name">CleanData<span>Pro</span></div>
                        <div class="auth-brand-tag">Clean. Analyze. Transform.</div>
                    </div>
                </div>
                <h1>Transform messy data into
                    <span class="green">clear</span>
                    <span class="blue">insights.</span>
                </h1>
                <p>Detect quality issues, clean datasets automatically, and
                    turn unreliable CSV files into analysis-ready data.</p>
                <div class="auth-features">
                    <div class="auth-feature">
                        <div class="auth-feature-icon">⌕</div>
                        <div><strong>Detect issues</strong><small>Find missing values, duplicates, and invalid formats.</small></div>
                    </div>
                    <div class="auth-feature">
                        <div class="auth-feature-icon">✓</div>
                        <div><strong>Smart cleaning</strong><small>Repair common data problems automatically.</small></div>
                    </div>
                    <div class="auth-feature">
                        <div class="auth-feature-icon">▥</div>
                        <div><strong>Visualize quality</strong><small>Compare before-and-after quality metrics.</small></div>
                    </div>
                    <div class="auth-feature">
                        <div class="auth-feature-icon">⇩</div>
                        <div><strong>Export reports</strong><small>Download cleaned CSV, PDF, and JSON files.</small></div>
                    </div>
                </div>
                <div class="auth-insights">
                    <div class="auth-insights-label">Data quality overview</div>
                    <div class="auth-metrics">
                        <div class="auth-metric"><span>Rows processed</span><strong>24,532</strong><em>↑ ready to analyze</em></div>
                        <div class="auth-metric"><span>Issues detected</span><strong>1,245</strong><em>✓ identified</em></div>
                        <div class="auth-metric"><span>Quality score</span><strong>92%</strong><em>↑ improved</em></div>
                    </div>
                </div>
            </section>
            """,
            unsafe_allow_html=True,
        )

    with auth:
        st.markdown(
            """
            <div class="auth-card-head">
                <div class="eyebrow">Your data workspace</div>
                <h2>Welcome to CleanDataPro</h2>
                <p>Sign in or create an account to start cleaning your data.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        tab_login, tab_signup = st.tabs(["Sign in", "Create account"])
        with tab_login:
            _render_login_form()
        with tab_signup:
            _render_signup_form()
        st.markdown(
            '<div class="auth-secure">Secure authentication • Your data stays private</div>',
            unsafe_allow_html=True,
        )


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
    st.markdown("<h3>Welcome back</h3>", unsafe_allow_html=True)

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
                        timeout=AUTH_TIMEOUT,
                    )
                except requests.RequestException:
                    _backend_connection_error()
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
    st.markdown("<h3>Create your workspace</h3>", unsafe_allow_html=True)

    with st.form("signup_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email", placeholder="___@gmail.com")
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
                        timeout=AUTH_TIMEOUT,
                    )
                except requests.RequestException:
                    _backend_connection_error()
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
