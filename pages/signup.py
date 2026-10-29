import streamlit
from src.passwords import signup_user_account

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

        with streamlit.form("signup_form", border=False):
        #Makes first and last name input boxes next to each other
            col1, col2 = streamlit.columns(2)

            #KSU Email and Password entry
            user_email = streamlit.text_input(label="Email")
            reg_password = streamlit.text_input(label="Pasword", type="password")
            conf_password = streamlit.text_input(label="Confirm Password", type="password")
            submitted = streamlit.form_submit_button("Register", type="primary")

        if submitted:
            if reg_password != conf_password:
                streamlit.error("Passwords do not match.")
            elif signup_user_account(user_email, reg_password):
                streamlit.success("Account created. You can log in now.")
            else:
                streamlit.error("That email is already registered.")
        streamlit.page_link("./pages/login.py", label="or Login")