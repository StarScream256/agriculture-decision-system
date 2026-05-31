from pathlib import Path

import pandas as pd
import streamlit as st


class UserData:
    def __init__(self, id: int, name: str, username: str, password: str, role: str):
        self.id = id
        self.name = name
        self.username = username
        self.password = password
        self.role = role


def get_csv_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data/users.csv"


def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["id", "name", "username", "password", "role"])
    return pd.read_csv(path)


def save_data(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)


def get_next_id_from_last_row(df: pd.DataFrame) -> int:
    if df.empty or "id" not in df.columns:
        return 1
    try:
        return int(df["id"].iloc[-1]) + 1
    except (ValueError, TypeError):
        return 1


def form(df: pd.DataFrame, data: UserData | None = None) -> dict:
    next_id = get_next_id_from_last_row(df)
    role_options = ["admin", "user"]
    if not df.empty and "role" in df.columns:
        csv_roles = [str(r) for r in df["role"].dropna().unique().tolist()]
        for role in csv_roles:
            if role not in role_options:
                role_options.append(role)

    selected_role = data.role if data and data.role in role_options else role_options[0]

    payload = {}
    payload["id"] = int(data.id) if data else next_id
    st.text_input("ID", value=str(payload["id"]), disabled=True)
    payload["name"] = st.text_input("Name", value=data.name if data else "")
    payload["username"] = st.text_input("Username", value=data.username if data else "")
    payload["password"] = st.text_input("Password", value=data.password if data else "")
    payload["role"] = st.selectbox(
        "Role",
        options=role_options,
        index=role_options.index(selected_role),
    )
    return payload


def normalize_payload(values: dict) -> dict:
    return {
        "id": int(values["id"]),
        "name": str(values["name"]).strip(),
        "username": str(values["username"]).strip(),
        "password": str(values["password"]).strip(),
        "role": str(values["role"]).strip(),
    }


def username_exists(df: pd.DataFrame, username: str, exclude_idx: int | None = None) -> bool:
    if df.empty or "username" not in df.columns:
        return False
    check_df = df.drop(index=exclude_idx) if exclude_idx is not None else df
    normalized = str(username).strip().lower()
    return normalized in check_df["username"].astype(str).str.strip().str.lower().tolist()


def main():
    st.title("Users Manager")
    csv_path = get_csv_path()
    df = load_data(csv_path)

    if st.session_state.get("show_toast", False):
        st.toast(st.session_state.get("toast_message", "✅ Users CSV has been modified."), duration="short")
        st.session_state["show_toast"] = False
        st.session_state["toast_message"] = ""

    st.markdown(f"**CSV file path:** {csv_path}")

    if df.empty:
        st.warning("users.csv is empty or not found. You can create rows using the form below.")

    with st.expander("View users dataset"):
        st.dataframe(df.drop(columns=["password"], errors="ignore"), hide_index=True)

    action = st.selectbox("Choose action", ["Create", "Edit", "Delete", "Export"], key="users_action_select")

    if action == "Create":
        st.subheader("Create new user")
        with st.form("users_create_form", clear_on_submit=True):
            values = form(df)
            submitted = st.form_submit_button("Add user")
            if submitted:
                new_row = normalize_payload(values)

                if not df.empty and int(new_row["id"]) in df["id"].astype(int).tolist():
                    st.error("ID already exists. Please use a unique ID.")
                elif username_exists(df, new_row["username"]):
                    st.error("username already exists. Please use a unique username.")
                elif not new_row["name"] or not new_row["username"] or not new_row["password"]:
                    st.error("name, username, and password cannot be empty.")
                else:
                    df2 = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df2, csv_path)
                    st.session_state["show_toast"] = True
                    st.session_state["toast_message"] = "✅ User added and saved to CSV."
                    st.rerun()

    if action == "Edit":
        st.subheader("Edit existing user")
        if df.empty:
            st.info("No users to edit")
        else:
            id_options = df["id"].astype(int).tolist()
            selected_id = st.selectbox("Select user ID", id_options, key="users_edit_id")
            idx = df.index[df["id"].astype(int) == int(selected_id)][0]
            row = df.loc[idx]
            row_data = UserData(
                id=int(row["id"]),
                name=str(row["name"]),
                username=str(row["username"]),
                password=str(row["password"]),
                role=str(row["role"]),
            )
            with st.form("users_edit_form"):
                updated = form(df, row_data)
                submit = st.form_submit_button("Save changes")
                if submit:
                    updated_row = normalize_payload(updated)
                    id_exists_elsewhere = (
                        int(updated_row["id"]) in df.drop(index=idx)["id"].astype(int).tolist()
                    )

                    if id_exists_elsewhere:
                        st.error("ID already exists in another row. Please use a unique ID.")
                    elif username_exists(df, updated_row["username"], exclude_idx=idx):
                        st.error("username already exists. Please use a unique username.")
                    elif not updated_row["name"] or not updated_row["username"] or not updated_row["password"]:
                        st.error("name, username, and password cannot be empty.")
                    else:
                        for col, value in updated_row.items():
                            df.at[idx, col] = value
                        save_data(df, csv_path)
                        st.session_state["show_toast"] = True
                        st.session_state["toast_message"] = "✅ User updated and saved to CSV."
                        st.rerun()

    if action == "Delete":
        st.subheader("Delete user(s)")
        if df.empty:
            st.info("No users to delete")
        else:
            choices = [
                f"{i}: id={df.loc[i, 'id']}, username={df.loc[i, 'username']}, role={df.loc[i, 'role']}"
                for i in df.index
            ]
            selected = st.multiselect("Select rows to delete (by index)", choices)
            if st.button("Delete selected users"):
                if not selected:
                    st.info("No selection made")
                else:
                    indices = [int(item.split(":", 1)[0]) for item in selected]
                    df2 = df.drop(index=indices).reset_index(drop=True)
                    save_data(df2, csv_path)
                    st.session_state["show_toast"] = True
                    st.session_state["toast_message"] = f"✅ Deleted {len(indices)} user(s)."
                    st.rerun()

    if action == "Export":
        st.subheader("Export / Download CSV")
        st.download_button(
            "Download current users.csv",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="users.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
