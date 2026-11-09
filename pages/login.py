import streamlit
from src.passwords import handle_login, current_user, login_user


#Route to dashboard, where login redirects too
HOME_PAGE = "./pages/example.py"
def redirect_after_login():
    scheduled_id = streamlit.session_state.pop(
        "pending_checkin_id", None
    )

    if scheduled_id:
        streamlit.switch_page(
            "./pages/check_in.py",
            query_params={"scheduled_id": str(scheduled_id)}
        )

    streamlit.switch_page(HOME_PAGE)

streamlit.set_page_config(initial_sidebar_state="collapsed")

if current_user():
    redirect_after_login()

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
        with streamlit.form("login_form", border=False):
            email = streamlit.text_input(label="Email")
            password = streamlit.text_input(label="Password")
            submitted = streamlit.form_submit_button("Login", type="primary")

        if submitted:
            if not email or not password:
                streamlit.error("Please enter your email and password.")
            elif login_user(email, password):
                redirect_after_login()
            else:
                streamlit.error("Invalid email or password.")

        streamlit.page_link("./pages/signup.py", label="Create your account")
