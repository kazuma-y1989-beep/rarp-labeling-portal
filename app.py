import streamlit as st

from portal.auth import ensure_login, logout
from portal.config import APP_TITLE
from portal.db import get_profile
from portal.pages import render_admin, render_dashboard, render_files, render_upload
from portal.supabase_client import get_client

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {max-width: 1220px; padding-top: 1.3rem;}
      [data-testid="stMetricValue"] {font-size: 2rem;}
      .portal-title {font-size: 2.05rem; font-weight: 760; margin-bottom: 0;}
      .portal-subtitle {color: #6b7280; margin: 0 0 1rem 0;}
      .rank-card {border: 1px solid #e5e7eb; border-radius: 12px; padding: 12px 16px; margin-bottom: 8px;}
    </style>
    """,
    unsafe_allow_html=True,
)

client = get_client()
user = ensure_login(client)
profile = get_profile(client, user.id)

with st.sidebar:
    st.markdown(f"### {APP_TITLE}")
    st.caption(f'{profile["researcher_name"]} 先生')
    page_options = ["ダッシュボード", "CSVアップロード", "登録ファイル"]
    if profile["role"] == "admin":
        page_options.append("管理者")
    selected_page = st.radio("メニュー", page_options)
    st.divider()
    if st.button("ログアウト", use_container_width=True):
        logout(client)

st.markdown(f'<div class="portal-title">{APP_TITLE}</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="portal-subtitle">RARPフェーズラベリングCSVの収集・進捗管理</div>',
    unsafe_allow_html=True,
)

if selected_page == "ダッシュボード":
    render_dashboard(client, profile)
elif selected_page == "CSVアップロード":
    render_upload(client, profile)
elif selected_page == "登録ファイル":
    render_files(client, profile)
elif selected_page == "管理者":
    render_admin(client, profile)
