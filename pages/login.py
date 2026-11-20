import streamlit
from src.passwords import handle_login, current_user, login_user

# Route to dashboard, where login redirects to
HOME_PAGE = "./main.py"


def redirect_after_login():
    scheduled_id = streamlit.session_state.pop("pending_checkin_id", None)

    if scheduled_id:
        streamlit.switch_page(
            "./pages/check_in.py", query_params={"scheduled_id": str(scheduled_id)}
        )

    # Student tapped an NFC tag before logging in: send them back to check-in.
    if "nfc_uid" in streamlit.session_state:
        streamlit.switch_page("./pages/check_in.py")

    streamlit.switch_page(HOME_PAGE)


streamlit.set_page_config(initial_sidebar_state="collapsed")

if current_user():
    redirect_after_login()

# Safely detect active theme
try:
    is_dark = streamlit.context.theme.type == "dark"
except Exception:
    is_dark = False

# Theme-based color assignments
bg_gradient = (
    "linear-gradient(135deg, #071221 0%, #0E2442 60%, #16345E 100%)"
    if is_dark
    else "linear-gradient(135deg, #F5EEDB 0%, #E8D8B0 100%)"
)
card_bg = "#102036" if is_dark else "#FAF6EB"
card_shadow = (
    "0 18px 40px rgba(0, 0, 0, 0.55)"
    if is_dark
    else "0 16px 36px rgba(0, 57, 118, 0.18)"
)
title_color = "#FAF6EB" if is_dark else "#003976"
subtitle_color = "#CBD5E1" if is_dark else "#4A5568"
label_color = "#F5EEDB" if is_dark else "#003976"
input_bg = "#0A1626" if is_dark else "#FFFEF7"
input_text = "#FAF6EB" if is_dark else "#1A2433"
input_border = "#EFAB00" if is_dark else "#003976"
btn_bg = "#EFAB00" if is_dark else "#003976"
btn_text = "#071221" if is_dark else "#FAF6EB"
btn_hover = "#FFC42E" if is_dark else "#00244D"

# Inject clean stylesheet
streamlit.markdown(
    f"""
    <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stHeaderActionElements"] {{
            display: none !important;
        }}

        [data-testid="stHeader"] {{
            background: transparent !important;
        }}

        .block-container {{
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }}

        .stApp, [data-testid="stAppViewContainer"] {{
            background: {bg_gradient} !important;
        }}

        [data-testid="stForm"] {{
            background-color: {card_bg} !important;
            border-radius: 16px !important;
            box-shadow: {card_shadow} !important;
            border: 2px solid #EFAB00 !important;
            padding: 2rem 2.25rem !important;
            margin-top: 0.75rem !important;
        }}

        [data-testid="stForm"] label,
        [data-testid="stForm"] p,
        [data-testid="stForm"] span,
        a[data-testid="stPageLink-NavLink"] p {{
            color: {label_color} !important;
            font-weight: 600 !important;
        }}

        .stTextInput input {{
            background-color: {input_bg} !important;
            color: {input_text} !important;
            border: 1.5px solid {input_border} !important;
            border-radius: 8px !important;
        }}

        button[kind="primaryFormSubmit"] {{
            background-color: {btn_bg} !important;
            border: 2px solid {btn_bg} !important;
            border-radius: 8px !important;
        }}
        button[kind="primaryFormSubmit"] p {{
            color: {btn_text} !important;
            font-weight: 700 !important;
        }}
        button[kind="primaryFormSubmit"]:hover {{
            background-color: {btn_hover} !important;
            border-color: #EFAB00 !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Center the card layout
_, center, _ = streamlit.columns([1, 2, 1])

with center:
    streamlit.markdown(
        f"""
        <div style="text-align: center; margin-bottom: 0.5rem;">
            <div style="
                color: {title_color};
                font-size: 3.25rem;
                font-weight: 900;
                letter-spacing: -1px;
                line-height: 1.05;
                margin: 0;
                padding: 0;
            ">Check<span style="color: #EFAB00;">In</span></div>
            <div style="
                width: 180px;
                height: 4px;
                background-color: #EFAB00;
                border-radius: 999px;
                margin: 0.45rem auto 0.6rem auto;
            "></div>
            <p style="
                color: {subtitle_color};
                font-size: 0.95rem;
                font-weight: 600;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                margin: 0;
            ">Attendance &amp; Check-In Portal</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with streamlit.form("login_form", border=False):
        email = streamlit.text_input(label="Email")
        password = streamlit.text_input(label="Password", type="password")
        submitted = streamlit.form_submit_button("Login", type="primary")

    if submitted:
        if not email or not password:
            streamlit.error("Please enter your email and password.")
        elif login_user(email, password):
            redirect_after_login()
        else:
            streamlit.error("Invalid email or password.")

    streamlit.page_link("./pages/signup.py", label="Create your account")

    # Helper instruction to press R for theme switching
    streamlit.markdown(
        f"""
        <p style="
            text-align: center; 
            color: {subtitle_color}; 
            font-size: 0.8rem; 
            margin-top: 1rem;
            opacity: 0.85;
        ">
             Press <b>R</b> to update theme colors after switching light/dark mode
        </p>
        """,
        unsafe_allow_html=True,
    )