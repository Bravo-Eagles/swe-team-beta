import bcrypt
import secrets
import datetime
import extra_streamlit_components as stx
import streamlit as st
from sqlite3 import Error, IntegrityError
from api import auth_api
import time

COOKIE = "session_token"
LOGIN_PAGE = "./pages/login.py"

def hash_password(password: str) -> str:
    """Return a bcrypt hash of the password, ready to store."""
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return hashed.decode()

def verify_password(password: str, stored_hash: str) -> bool:
    """Return True if the password matches the stored hash."""
    return bcrypt.checkpw(password.encode(), stored_hash.encode())

def signup_user_account(email, password):
    """Creates a User Account"""
    try:
        hashword = hash_password(password)
        acc = auth_api.make_account(email.strip().lower(), hashword)
        if acc:
            return True
        else:
            return False
    except IntegrityError:
        return False
    except Error:
        print(f"User Signup Failed")
        return False

def handle_login(email, password):
    """Handles Login Lgoic"""
    account = auth_api.get_account(email.strip().lower())
    #print(f"DEBUG: account type is {type(account)}, value is {account}")
    if account is None or not bcrypt.checkpw(password.encode(), account["password_hash"].encode()):
        print(f"Passwords do not match")
        return None #Value for invalid login
    return account["id"] #Value for successful login

def create_login_session(userID):
    token = secrets.token_urlsafe(32) #Creates token for login session
    expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours= 1) #Login Session expires in 1 hour
    return auth_api.create_session(userID, token, expires)

def login_user(email: str, password: str):
    """Call on login page, handles credential check, session, and cookie creation"""
    user_id = handle_login(email, password)
    if user_id is None:
        return False

    result = create_login_session(user_id)
    if result is None:
        return False
    token, expires = result
    cookies = stx.CookieManager(key="cookie_mgr_login")
    cookies.set(COOKIE, token, expires_at=expires, key="set_cookie")

    st.session_state["user"] = {"id": user_id, "email": email.strip().lower()}
    time.sleep(0.5) #Need a hard sleep to bypass weird cookie management ik its gross
    return True

def current_user():
    """Return the logged in user or None"""
    if st.session_state.get("user"):
        return st.session_state["user"]

    token = st.context.cookies.get(COOKIE)
    if token:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        user = auth_api.get_user_by_session(token, now)
        if user:
            st.session_state["user"] = {"id": user["id"], "email": user["email"]}
            return st.session_state["user"]
        return None
    return None

def require_login():
    """Call at the top of every protected page."""
    user = current_user()
    if user is None:
        print("No User in require_Login()")
        st.switch_page(LOGIN_PAGE)   # stops the script and navigates
    return user

def logout():
    token = st.context.cookies.get(COOKIE)
    if token:
        auth_api.delete_session(token)
    cookies = stx.CookieManager(key="cookie_mgr_logout")
    cookies.delete(COOKIE, key="del_cookie")
    st.session_state.pop("user", None)
    time.sleep(0.5) #Need hard sleep to manage cookies, is icky
    st.switch_page(LOGIN_PAGE)