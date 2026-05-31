import streamlit as st


st.set_page_config(page_title="Agriculture Decision System", page_icon="🌾", layout="wide")

home_page = st.Page("pages/home.py", title="Home", icon="🏠", default=True)
crops_page = st.Page("pages/crops.py", title="Crop Dataset", icon="📁")
users_page = st.Page("pages/users.py", title="User Management", icon="👥")

pg = st.navigation(
    [home_page, crops_page, users_page]
)

pg.run()