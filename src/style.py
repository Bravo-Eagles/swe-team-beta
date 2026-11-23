# src/style.py
import streamlit
from pathlib import Path
from PIL import Image

# Resolved relative to this file, so it works no matter where you run streamlit from
FAVICON_PATH = Path(__file__).resolve().parent / "favicon.ico"

GOLD = "#EFAB00"


def load_favicon():
    return Image.open(FAVICON_PATH)

def palette() -> dict:
    try:
        is_dark = streamlit.context.theme.type == "dark"
    except Exception:
        is_dark = False

    if is_dark:
        return {
            "bg": "linear-gradient(135deg, #071221 0%, #0E2442 60%, #16345E 100%)",
            "bg_flat": "#0B1B33",
            "card": "#102036",
            "shadow": "0 18px 40px rgba(0, 0, 0, 0.55)",
            "title": "#FAF6EB",
            "subtitle": "#CBD5E1",
            "label": "#F5EEDB",
            "input_bg": "#0A1626",
            "input_text": "#FAF6EB",
            "input_border": GOLD,
            "btn_bg": GOLD,
            "btn_text": "#071221",
            "btn_hover": "#FFC42E",
        }
    return {
        "bg": "linear-gradient(135deg, #F5EEDB 0%, #E8D8B0 100%)",
        "bg_flat": "#F5EEDB",
        "card": "#FAF6EB",
        "shadow": "0 16px 36px rgba(0, 57, 118, 0.18)",
        "title": "#003976",
        "subtitle": "#4A5568",
        "label": "#003976",
        "input_bg": "#FFFEF7",
        "input_text": "#1A2433",
        "input_border": "#003976",
        "btn_bg": "#003976",
        "btn_text": "#FAF6EB",
        "btn_hover": "#00244D",
    }


def apply_style(hide_sidebar: bool = False, gradient: bool = True) -> None:
    p = palette()
    background = p["bg"] if gradient else p["bg_flat"]

    sidebar_css = ""
    if hide_sidebar:
        sidebar_css = """
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stHeaderActionElements"] { display: none !important; }
        """

    css = f"""
        [data-testid="stHeader"] {{ background: transparent !important; }}
        .stApp, [data-testid="stAppViewContainer"] {{ background: {background} !important; }}
        [data-testid="stSidebar"] {{ background-color: {p["card"]} !important; }}

        h1, h2, h3 {{ color: {p["title"]} !important; letter-spacing: -0.01em; }}
        [data-testid="stCaptionContainer"] {{ color: {p["subtitle"]} !important; }}

        /* Cards: forms, and any container created with key="card_..." */
        [data-testid="stForm"],
        div[class*="st-key-card"],
        [data-testid="stMetric"] {{
            background-color: {p["card"]} !important;
            border-radius: 16px !important;
            box-shadow: {p["shadow"]} !important;
            border: 2px solid {GOLD} !important;
        }}
        [data-testid="stForm"] {{ padding: 2rem 2.25rem !important; }}
        div[class*="st-key-card"] {{ padding: 1rem 1.25rem !important; }}
        [data-testid="stMetric"] {{ padding: 1rem 1.25rem !important; }}

        [data-testid="stForm"] label,
        [data-testid="stForm"] p,
        a[data-testid="stPageLink-NavLink"] p {{
            color: {p["label"]} !important;
            font-weight: 600 !important;
        }}

        .stTextInput input, .stTextArea textarea, [data-baseweb="select"] > div {{
            background-color: {p["input_bg"]} !important;
            color: {p["input_text"]} !important;
            border: 1.5px solid {p["input_border"]} !important;
            border-radius: 8px !important;
        }}

        /* Primary buttons (regular and form submit) */
        button[kind="primary"], button[kind="primaryFormSubmit"] {{
            background-color: {p["btn_bg"]} !important;
            border: 2px solid {p["btn_bg"]} !important;
            border-radius: 8px !important;
        }}
        button[kind="primary"] p, button[kind="primaryFormSubmit"] p {{
            color: {p["btn_text"]} !important;
            font-weight: 700 !important;
        }}
        button[kind="primary"]:hover, button[kind="primaryFormSubmit"]:hover {{
            background-color: {p["btn_hover"]} !important;
            border-color: {GOLD} !important;
        }}

        /* Secondary buttons: outlined */
        button[kind="secondary"] {{
            background: transparent !important;
            border: 1.5px solid {p["input_border"]} !important;
            border-radius: 8px !important;
        }}
        button[kind="secondary"] p {{
            color: {p["label"]} !important;
            font-weight: 600 !important;
        }}
        button[kind="secondary"]:hover {{ border-color: {GOLD} !important; }}
    """
    streamlit.markdown(f"<style>{sidebar_css}{css}</style>", unsafe_allow_html=True)


def setup_page(
    title: str = "CheckIn",
    icon=None,
    hide_sidebar: bool = False,
    layout: str = "centered",
    gradient: bool = True,
) -> None:
    """Call first on every page, before sidebar() or anything else."""
    streamlit.set_page_config(
        page_title=title,
        page_icon=icon if icon is not None else load_favicon(),
        layout=layout,
        initial_sidebar_state="collapsed" if hide_sidebar else "auto",
    )
    apply_style(hide_sidebar, gradient)

def brand_header(subtitle: str) -> None:
    p = palette()
    streamlit.markdown(
        f"""
        <div style="text-align:center; margin-bottom:0.5rem;">
            <div style="color:{p["title"]}; font-size:3.25rem; font-weight:900;
                        letter-spacing:-1px; line-height:1.05;">
                Check<span style="color:{GOLD};">In</span>
            </div>
            <div style="width:180px; height:4px; background:{GOLD};
                        border-radius:999px; margin:0.45rem auto 0.6rem auto;"></div>
            <p style="color:{p["subtitle"]}; font-size:0.95rem; font-weight:600;
                      letter-spacing:0.5px; text-transform:uppercase; margin:0;">
                {subtitle}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )