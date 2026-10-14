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
    #Signup Card
    with streamlit.container(border=True):
        streamlit.header("Sign Up")

        #Makes first and last name input boxes next to each other
        col1, col2 = streamlit.columns(2)
        with col1:
            streamlit.text_input(label="First Name")
        with col2:
            streamlit.text_input(label="Last Name")

        #KSU Email and Password entry
        streamlit.text_input(label="Email")
        streamlit.text_input(label="Pasword", type="password")
        streamlit.button("Register", type="primary")
        streamlit.page_link("./pages/login.py", label="or Login")