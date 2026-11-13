import streamlit as st
from src.accessibility import apply_text_size


def sidebar():
    # Apply user's preferred text size
    apply_text_size()

    # Sidebar navigation
    st.sidebar.page_link('main.py', label='Home')
    st.sidebar.page_link('pages/AITest.py', label='AI Test Page')
    st.sidebar.page_link('pages/import.py', label='Data Import')
    st.sidebar.page_link('pages/student_dashboard.py', label='Student Dashboard')
    st.sidebar.page_link('pages/settings.py', label='Settings')