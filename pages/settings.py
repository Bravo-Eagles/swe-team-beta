import streamlit as st
from src.passwords import require_login
from src.sidebar import sidebar
from src.database import get_text_size, update_text_size as save_text_size

# Page configuration
st.set_page_config(
    page_title="Settings",
    page_icon="⚙️",
    layout="wide"
)

# Require login
user = require_login()
sidebar()

# Page title
st.title("Settings")
st.subheader("Customize your experience")

st.divider()

# Accessibility settings
st.header("Accessibility")
st.write("Adjust the text size to make the application easier to read.")

# Text size selection
st.subheader("Text Size")

st.write("Choose your preferred text size:")


# Database values and their corresponding labels
font_size_values = {
    "Small": 14,
    "Medium": 18,
    "Large": 24
}

# Get the logged-in user's account ID
account_id = user["id"]

# Load the saved preference when switching accounts
if st.session_state.get("settings_account_id") != account_id:
    saved_size = get_text_size(account_id)

    size_labels = {
        14: "Small",
        16: "Medium",  # Supports previously saved preferences
        18: "Medium",
        20: "Large",   # Supports previously saved preferences
        24: "Large"
    }

    preferred_size = size_labels.get(saved_size, "Medium")

    st.session_state["preferred_text_size"] = preferred_size
    st.session_state["text_size_selection"] = preferred_size
    st.session_state["settings_account_id"] = account_id

# Restore the radio button after navigating between pages
if "text_size_selection" not in st.session_state:
    st.session_state["text_size_selection"] = (
        st.session_state["preferred_text_size"]
    )


def update_text_size():
    selected_label = st.session_state["text_size_selection"]

    # Update the session preference
    st.session_state["preferred_text_size"] = selected_label

    # Save the preference to the database
    save_text_size(account_id, font_size_values[selected_label])



text_size = st.radio(
    "Select a text size",
    options=["Small", "Medium", "Large"],
    horizontal=True,
    key="text_size_selection",
    on_change=update_text_size
)


# Define font sizes
font_sizes = {
    "Small": "14px",
    "Medium": "18px",
    "Large": "24px"
}

# Get the selected font size
selected_size = font_sizes[text_size]

# Display preview
st.divider()
st.subheader("Preview")

st.markdown(
    f"""
    <p style="font-size: {selected_size};">
        This is an example of how text will appear throughout the application.
    </p>
    """,
    unsafe_allow_html=True
)