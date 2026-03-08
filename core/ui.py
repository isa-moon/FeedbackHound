"""共享的 Streamlit 页面初始化。"""

import streamlit as st

from config import SESSION_DEFAULTS


def initialize_session_state() -> None:
    """初始化跨页面共享的 session_state。"""
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def setup_page() -> None:
    """初始化当前页面所需的共享状态。"""
    initialize_session_state()
