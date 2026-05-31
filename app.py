import streamlit as st


st.set_page_config(page_title="Agriculture Decision System", page_icon="🌾", layout="wide")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user_role" not in st.session_state:
    st.session_state.user_role = None

home_page = st.Page("pages/home.py", title="Home", icon="🏠")
crops_page = st.Page("pages/crops.py", title="Crop Dataset", icon="📁")
users_page = st.Page("pages/users.py", title="User Management", icon="👥")
login_page = st.Page("pages/auth/login.py", title="Login", icon="🔐", default=True)
register_page = st.Page("pages/auth/register.py", title="Register", icon="📝")

if st.session_state.authenticated:
    st.sidebar.success(f"Welcome, {st.session_state.get('username', '-')}")
    if st.sidebar.button("Logout", type="primary", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.username = None
        st.rerun()

    protected_pages = [home_page, crops_page]
    if st.session_state.user_role == "admin":
        protected_pages.append(users_page)

    pg = st.navigation(protected_pages)
else:
    pg = st.navigation([login_page, register_page])

pg.run()