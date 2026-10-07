import streamlit

# This is a mockup page lacking functionality to act as a placeholder

streamlit.set_page_config(initial_sidebar_state="collapsed")

# Hide the sidebar and its collapse/expand control entirely
streamlit.markdown(
    """
    <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"] {
            display: none;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Center the card using empty columns on either side
_, center, _ = streamlit.columns([1, 2, 1])

with center:
    with streamlit.container(border=True):
        streamlit.header("Login")
        streamlit.text_input(label="Email")
        streamlit.text_input(label="Pasword")
        streamlit.button("Login", type="primary")
        streamlit.page_link("./pages/signup.py", label="Create your account")
