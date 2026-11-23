import streamlit as st
from src.passwords import current_user
from src.database import get_text_size


def apply_text_size():
    """Load and apply the logged-in user's preferred text size."""

    font_sizes = {
        "Small": "14px",
        "Medium": "18px",
        "Large": "24px"
    }

    # Get the currently logged-in user
    user = current_user()

    if user is not None:
        account_id = user["id"]

        # Load the preference when the user changes
        if st.session_state.get("accessibility_account_id") != account_id:
            saved_size = get_text_size(account_id)

            size_labels = {
                14: "Small",
                16: "Medium",  # Supports previously saved preferences
                18: "Medium",
                20: "Large",   # Supports previously saved preferences
                24: "Large"
            }

            st.session_state["preferred_text_size"] = (
                size_labels.get(saved_size, "Medium")
            )

            st.session_state["accessibility_account_id"] = account_id

    # Apply the saved preference
    text_size = st.session_state.get(
        "preferred_text_size", "Medium"
    )
    selected_size = font_sizes.get(text_size, "16px")

    st.markdown(
        f"""
        <style>
        h1,
        h2,
        h3,
        h4,
        h5,
        h6,
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