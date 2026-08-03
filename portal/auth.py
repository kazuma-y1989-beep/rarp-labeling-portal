import streamlit as st
from supabase import Client


def login_form(client: Client) -> None:
    st.subheader("ログイン")
    with st.form("login_form"):
        email = st.text_input("メールアドレス")
        password = st.text_input("パスワード", type="password")
        submitted = st.form_submit_button("ログイン", use_container_width=True)

    if submitted:
        try:
            response = client.auth.sign_in_with_password(
                {"email": email.strip(), "password": password}
            )
            st.session_state["user_id"] = response.user.id
            st.session_state["access_token"] = response.session.access_token
            st.session_state["refresh_token"] = response.session.refresh_token
            st.rerun()
        except Exception:
            st.error("メールアドレスまたはパスワードを確認してください。")


def ensure_login(client: Client):
    user_id = st.session_state.get("user_id")
    if user_id:
        try:
            response = client.auth.get_user()
            if response.user:
                return response.user
        except Exception:
            pass

    login_form(client)
    st.stop()


def logout(client: Client) -> None:
    try:
        client.auth.sign_out()
    finally:
        for key in ("user_id", "access_token", "refresh_token"):
            st.session_state.pop(key, None)
        st.rerun()
