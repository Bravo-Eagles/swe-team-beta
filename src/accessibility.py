import streamlit as st


def apply_text_size():
    """Apply the selected text size to the current page."""

    font_sizes = {
        "Small": "14px",
        "Medium": "16px",
        "Large": "20px"
    }

    text_size = st.session_state.get(
        "preferred_text_size", "Medium"
    )
    selected_size = font_sizes.get(text_size, "16px")

    st.markdown(
        f"""
        <style>
        .stMarkdown p,
        .stMarkdown li,
        .stText,
        .stCaption,
        [data-testid="stMetricLabel"],
        [data-testid="stMetricValue"] {{
            font-size: {selected_size} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )