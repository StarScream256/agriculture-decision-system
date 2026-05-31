from pathlib import Path

import pandas as pd
import streamlit as st


def get_users_csv_path() -> Path:
	return Path(__file__).resolve().parents[2] / "data/users.csv"


def load_users(path: Path) -> pd.DataFrame:
	if not path.exists():
		return pd.DataFrame(columns=["id", "name", "username", "password", "role"])
	return pd.read_csv(path)


def save_users(df: pd.DataFrame, path: Path) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	df.to_csv(path, index=False)


def resolve_columns(df: pd.DataFrame) -> tuple[str | None, str | None, str | None]:
	username_col = "username" if "username" in df.columns else ("usrname" if "usrname" in df.columns else None)
	password_col = "password" if "password" in df.columns else ("pasword" if "pasword" in df.columns else None)
	role_col = "role" if "role" in df.columns else None
	return username_col, password_col, role_col


def next_id_from_last_row(df: pd.DataFrame) -> int:
	if df.empty or "id" not in df.columns:
		return 1
	try:
		return int(df["id"].iloc[-1]) + 1
	except (ValueError, TypeError):
		return 1


def username_exists(df: pd.DataFrame, username: str, username_col: str | None) -> bool:
	if df.empty or not username_col:
		return False
	normalized = str(username).strip().lower()
	return normalized in df[username_col].astype(str).str.strip().str.lower().tolist()


def main():
	if st.session_state.get("authenticated", False):
		st.success("You are already logged in.")
		if st.button("Go to Home", type="primary"):
			st.switch_page("pages/home.py")
		return

	st.title("Register")
	st.write("Create a new account. New accounts are registered with role: user.")

	users_path = get_users_csv_path()
	users_df = load_users(users_path)

	username_col, password_col, role_col = resolve_columns(users_df)

	# Use canonical columns when creating a new/empty file.
	if username_col is None:
		username_col = "username"
		if username_col not in users_df.columns:
			users_df[username_col] = ""
	if password_col is None:
		password_col = "password"
		if password_col not in users_df.columns:
			users_df[password_col] = ""
	if role_col is None:
		role_col = "role"
		if role_col not in users_df.columns:
			users_df[role_col] = ""
	if "id" not in users_df.columns:
		users_df["id"] = []
	if "name" not in users_df.columns:
		users_df["name"] = ""

	next_id = next_id_from_last_row(users_df)

	with st.form("register_form"):
		st.text_input("ID", value=str(next_id), disabled=True)
		name = st.text_input("Name")
		username = st.text_input("Username")
		password = st.text_input("Password", type="password")
		confirm_password = st.text_input("Confirm Password", type="password")
		st.text_input("Role", value="user", disabled=True)
		submitted = st.form_submit_button("Register", type="primary")

		if submitted:
			if not name.strip() or not username.strip() or not password:
				st.error("Name, username, and password are required.")
				return
			if password != confirm_password:
				st.error("Password and confirm password do not match.")
				return
			if username_exists(users_df, username, username_col):
				st.error("Username already exists. Please choose another username.")
				return

			new_row = {col: "" for col in users_df.columns}
			new_row["id"] = next_id
			new_row["name"] = str(name).strip()
			new_row[username_col] = str(username).strip()
			new_row[password_col] = str(password)
			new_row[role_col] = "user"

			users_df = pd.concat([users_df, pd.DataFrame([new_row])], ignore_index=True)
			save_users(users_df, users_path)
			st.success("Registration successful. Please login with your new account.")

	st.divider()
	st.write("Already have an account?")
	if st.button("Go to Login"):
		st.switch_page("pages/auth/login.py")


if __name__ == "__main__":
	main()

