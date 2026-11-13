import streamlit as st
from src.passwords import require_login
from src.sidebar import sidebar

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

# Initialize saved preference
if "preferred_text_size" not in st.session_state:
    st.session_state["preferred_text_size"] = "Medium"

# Initialize radio button
if "text_size_selection" not in st.session_state:
    st.session_state["text_size_selection"] = (
        st.session_state["preferred_text_size"]
    )


def update_text_size():
    st.session_state["preferred_text_size"] = (
        st.session_state["text_size_selection"]
    )


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
    "Medium": "16px",
    "Large": "20px"
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