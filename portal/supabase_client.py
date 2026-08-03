import streamlit as st
from supabase import Client, create_client


def get_client() -> Client:
    try:
        client = create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_ANON_KEY"],
        )
    except KeyError as exc:
        st.error(
            "Supabaseの接続情報が未設定です。Streamlit CloudのSecretsに "
            "SUPABASE_URL と SUPABASE_ANON_KEY を登録してください。"
        )
        st.stop()
        raise exc

    access_token = st.session_state.get("access_token")
    refresh_token = st.session_state.get("refresh_token")
    if access_token and refresh_token:
        try:
            client.auth.set_session(access_token, refresh_token)
        except Exception:
            for key in ("user_id", "access_token", "refresh_token"):
                st.session_state.pop(key, None)
    return client
