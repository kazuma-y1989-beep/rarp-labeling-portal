import streamlit as st

from portal.auth import ensure_login, logout
from portal.config import APP_TITLE
from portal.db import get_profile
from portal.pages import render_admin, render_dashboard, render_files, render_upload
from portal.supabase_client import get_client

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --primary: #7C5CFC;
        --accent: #FFB84D;
        --mint: #35C6A3;
        --text: #1F2937;
        --muted: #6B7280;
        --card: rgba(255,255,255,0.95);
        --shadow: 0 12px 30px rgba(77,63,140,0.10);
    }

    html, body, [class*="css"] {
        font-family: "Segoe UI", "Hiragino Sans", "Yu Gothic UI", sans-serif;
        color: var(--text);
    }

    .stApp {
        background:
            radial-gradient(circle at 85% 5%, rgba(124,92,252,0.11), transparent 28%),
            radial-gradient(circle at 70% 90%, rgba(53,198,163,0.08), transparent 28%),
            linear-gradient(180deg, #FBFAFF 0%, #F7FAFF 100%);
    }

    .block-container {
        max-width: 1240px;
        padding-top: 4.8rem !important;
        padding-bottom: 3rem;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FFFFFF 0%, #FAF8FF 55%, #F5F8FF 100%);
        border-right: 1px solid rgba(124,92,252,0.12);
    }

    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 18px;
    }

    .sidebar-logo {
        width: 44px;
        height: 44px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #7C5CFC, #A881FF);
        box-shadow: 0 8px 20px rgba(124,92,252,0.28);
        font-size: 23px;
    }

    .sidebar-title {
        font-weight: 800;
        font-size: 1.08rem;
        line-height: 1.25;
    }

    .user-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        margin-bottom: 14px;
        border-radius: 999px;
        background: #F0EBFF;
        color: #6547D8;
        font-weight: 700;
        font-size: 0.88rem;
    }

    section[data-testid="stSidebar"] [role="radiogroup"] label {
        border-radius: 12px;
        padding: 8px 10px;
        transition: all 0.2s ease;
    }

    section[data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: #F1EDFF;
        transform: translateX(2px);
    }

    .hero {
        position: relative;
        overflow: hidden;
        border-radius: 24px;
        padding: 24px 28px;
        margin-bottom: 20px;
        background:
            linear-gradient(135deg, rgba(124,92,252,0.14), rgba(255,255,255,0.92) 48%, rgba(53,198,163,0.10));
        border: 1px solid rgba(124,92,252,0.12);
        box-shadow: var(--shadow);
    }

    .hero-title {
        font-size: clamp(2rem, 3vw, 3rem);
        line-height: 1.1;
        font-weight: 900;
        letter-spacing: -0.04em;
        background: linear-gradient(90deg, #5E45D4 0%, #8B5CF6 50%, #21A58A 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }

    .hero-subtitle {
        color: var(--muted);
        font-size: 1rem;
        margin: 0;
    }

    div[data-testid="stMetric"] {
        background: var(--card);
        border: 1px solid rgba(124,92,252,0.11);
        border-radius: 18px;
        padding: 18px 20px;
        box-shadow: var(--shadow);
        min-height: 126px;
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 16px 36px rgba(77,63,140,0.15);
    }

    div[data-testid="stMetricLabel"] {
        color: var(--muted);
        font-weight: 700;
    }

    div[data-testid="stMetricValue"] {
        font-size: 2.05rem;
        font-weight: 900;
        color: var(--text);
    }

    div[data-testid="stDataFrame"] {
        border-radius: 18px;
        overflow: hidden;
        border: 1px solid rgba(124,92,252,0.10);
        box-shadow: var(--shadow);
        background: white;
    }

    .stButton button,
    .stDownloadButton button {
        border-radius: 12px !important;
        font-weight: 800 !important;
        transition: transform 0.18s ease;
    }

    .stButton button[kind="primary"],
    .stDownloadButton button {
        background: linear-gradient(135deg, #7C5CFC, #9A74FF) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 8px 18px rgba(124,92,252,0.25);
    }

    section[data-testid="stFileUploaderDropzone"] {
        border-radius: 18px;
        border: 2px dashed rgba(124,92,252,0.35);
        background: linear-gradient(135deg, #FBFAFF, #F8FCFF);
        padding: 18px;
    }

    div[data-testid="stProgress"] > div > div {
        background: linear-gradient(90deg, #7C5CFC, #35C6A3);
        border-radius: 999px;
    }

    @media (max-width: 900px) {
        .block-container {
            padding-top: 4rem !important;
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

client = get_client()
user = ensure_login(client)
profile = get_profile(client, user.id)

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-logo">🤖</div>
            <div class="sidebar-title">RARP AI<br>Labeling Portal</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    role_label = "管理者" if profile["role"] == "admin" else "研究者"
    st.markdown(
        f'<div class="user-chip">👤 {profile["researcher_name"]} 先生　{role_label}</div>',
        unsafe_allow_html=True,
    )

    page_options = ["🏠 ダッシュボード", "📤 CSVアップロード", "📁 登録ファイル"]
    if profile["role"] == "admin":
        page_options.append("🛡️ 管理者")

    selected_page = st.radio("メニュー", page_options)

    st.divider()

    if st.button("↪ ログアウト", use_container_width=True):
        logout(client)

st.markdown(
    f"""
    <div class="hero">
        <div class="hero-title">{APP_TITLE}</div>
        <p class="hero-subtitle">RARPフェーズラベリングCSVの収集・進捗管理</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if selected_page == "🏠 ダッシュボード":
    render_dashboard(client, profile)
elif selected_page == "📤 CSVアップロード":
    render_upload(client, profile)
elif selected_page == "📁 登録ファイル":
    render_files(client, profile)
elif selected_page == "🛡️ 管理者":
    render_admin(client, profile)
