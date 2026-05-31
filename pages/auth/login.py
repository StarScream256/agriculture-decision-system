from pathlib import Path

import pandas as pd
import streamlit as st


def get_users_csv_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data/users.csv"


def load_users(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def resolve_columns(df: pd.DataFrame) -> tuple[str | None, str | None, str | None]:
    username_col = "username" if "username" in df.columns else ("usrname" if "usrname" in df.columns else None)
    password_col = "password" if "password" in df.columns else ("pasword" if "pasword" in df.columns else None)
    role_col = "role" if "role" in df.columns else None
    return username_col, password_col, role_col


def authenticate(df: pd.DataFrame, username: str, password: str) -> dict | None:
    username_col, password_col, role_col = resolve_columns(df)
    if not username_col or not password_col:
        return None

    matched = df[
        (df[username_col].astype(str) == str(username).strip())
        & (df[password_col].astype(str) == str(password))
    ]
    if matched.empty:
        return None

    user = matched.iloc[0].to_dict()
    return {
        "username": str(user.get(username_col, "")).strip(),
        "role": str(user.get(role_col, "user")).strip() if role_col else "user",
        "name": str(user.get("name", "")).strip(),
    }


def main():
    if st.session_state.get("authenticated", False):
        st.success("You are already logged in.")
        if st.button("Go to Home", type="primary"):
            st.switch_page("pages/home.py")
        return

    st.title("Login")
    st.write("Please login to access Home and Dataset Manager.")

    users_path = get_users_csv_path()
    users_df = load_users(users_path)

    if users_df.empty:
        st.error("users.csv not found or empty. Please prepare user data first.")
        return

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", type="primary")

        if submitted:
            if not username.strip() or not password:
                st.error("Username and password are required.")
                return

            auth_user = authenticate(users_df, username, password)
            if auth_user is None:
                st.error("Invalid username or password.")
                return

            st.session_state.authenticated = True
            st.session_state.username = auth_user["username"]
            st.session_state.user_role = auth_user["role"].lower()
            st.session_state.user_name = auth_user["name"]
            st.success("Login successful.")
            st.rerun()

    st.divider()
    st.write("Don't have an account?")
    if st.button("Create an account"):
        st.switch_page("pages/auth/register.py")


if __name__ == "__main__":
    main()
