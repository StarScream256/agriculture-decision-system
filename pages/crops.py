import os
from pathlib import Path
import time
import pandas as pd
import streamlit as st

class Data:
    def __init__(self, N_SOIL: int, P_SOIL: int, K_SOIL: int, TEMPERATURE: float, HUMIDITY: float, ph: float, RAINFALL: float, STATE: str, CROP_PRICE: int, CROP: str):
        self.N_SOIL = N_SOIL
        self.P_SOIL = P_SOIL
        self.K_SOIL = K_SOIL
        self.TEMPERATURE = TEMPERATURE
        self.HUMIDITY = HUMIDITY
        self.ph = ph
        self.RAINFALL = RAINFALL
        self.STATE = STATE
        self.CROP_PRICE = CROP_PRICE
        self.CROP = CROP


def get_csv_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data/indiancrop_dataset.csv"


def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def save_data(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)


def form(df: pd.DataFrame, data: Data | None = None) -> dict:
    form = {}
    form["N_SOIL"] = st.number_input(
        f"N_SOIL (Integer: 0-{df['N_SOIL'].max()})", 
        value=data.N_SOIL if data else None
    )
    form["P_SOIL"] = st.number_input(
        f"P_SOIL (Integer: 0-{df['P_SOIL'].max()})", 
        value=data.P_SOIL if data else None
    )
    form["K_SOIL"] = st.number_input(
        f"K_SOIL (Integer: 0-{df['K_SOIL'].max()})", 
        value=data.K_SOIL if data else None
    )
    form["TEMPERATURE"] = st.number_input(
        f"TEMPERATURE (Float: {df['TEMPERATURE'].min():.2f}-{df['TEMPERATURE'].max():.2f})", 
        value=data.TEMPERATURE if data else None
    )
    form["HUMIDITY"] = st.number_input(
        f"HUMIDITY (Float: {df['HUMIDITY'].min():.2f}-{df['HUMIDITY'].max():.2f})", 
        value=data.HUMIDITY if data else None
    )
    form["ph"] = st.number_input(
        f"ph (Float: {df['ph'].min():.2f}-{df['ph'].max():.2f})", 
        value=data.ph if data else None
    )
    form["RAINFALL"] = st.number_input(
        f"RAINFALL (Float: {df['RAINFALL'].min():.2f}-{df['RAINFALL'].max():.2f})", 
        value=data.RAINFALL if data else None
    )
    form["STATE"] = st.text_input(
        f"STATE (Text)", 
        value=data.STATE if data else None
    )
    form["CROP_PRICE"] = st.number_input(
        f"CROP_PRICE (Integer)", 
        value=data.CROP_PRICE if data else None
    )
    form["CROP"] = st.text_input(
        f"CROP (Text)", 
        value=data.CROP if data else None
    )
    return form


def main():
    st.title("Dataset Manager")
    csv_path = get_csv_path()
    df = load_data(csv_path)

    if st.session_state.get("show_toast", False):
        st.toast(st.session_state.get("toast_message", "✅ CSV has been modified!"), duration="short")
        st.session_state["show_toast"] = False
        st.session_state["toast_message"] = ""

    st.markdown(f"**CSV file path:** {csv_path}")

    if df.empty:
        st.warning("CSV is empty or not found. You can create rows using the form below.")

    with st.expander("View dataset"):
        st.dataframe(df)

    action = st.selectbox("Choose action", ["Create", "Edit", "Delete", "Export"], key="action_select")

    if action == "Create":
        st.subheader("Create new row")
        cols = df.columns.tolist() if not df.empty else []
        if not cols:
            st.info("Dataset has no columns yet. Enter comma-separated column names first.")
            cols_input = st.text_input("Columns (comma-separated)")
            if cols_input:
                cols = [c.strip() for c in cols_input.split(",") if c.strip()]
        if cols:
            with st.form("create_form", clear_on_submit=True):
                values = form(df)
                submitted = st.form_submit_button("Add row")
                if submitted:
                    cleaned_values = {
                        k: (v.replace(',', '.') if isinstance(v, str) else v) 
                        for k, v in values.items()
                    }
                    new_row = {
                        k: pd.to_numeric(v, errors='ignore') 
                        for k, v in cleaned_values.items()
                    }

                    df2 = df.copy()
                    df2 = pd.concat([df2, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df2, csv_path)
                    st.session_state["show_toast"] = True
                    st.session_state["toast_message"] = "✅ Row added and saved to CSV!"
                    st.rerun()

    if action == "Edit":
        st.subheader("Edit existing row")
        if df.empty:
            st.info("No rows to edit")
        else:
            idx = st.selectbox("Select row index", df.index.tolist())
            row = df.loc[idx]
            with st.form("edit_form"):
                updated = form(df, Data(**row.to_dict()))
                submit = st.form_submit_button("Save changes")
                if submit:
                    for c, v in updated.items():
                        df.at[idx, c] = v
                    save_data(df, csv_path)
                    st.session_state["show_toast"] = True
                    st.session_state["toast_message"] = "✅ Row updated and saved to CSV!"
                    st.rerun()

    if action == "Delete":
        st.subheader("Delete row(s)")
        if df.empty:
            st.info("No rows to delete")
        else:
            choices = [f"{i}: {', '.join(map(str, df.loc[i].values))}" for i in df.index]
            sel = st.multiselect("Select rows to delete (by index)", choices)
            if st.button("Delete selected"):
                if not sel:
                    st.info("No selection made")
                else:
                    indices = [int(s.split(":", 1)[0]) for s in sel]
                    df2 = df.drop(index=indices).reset_index(drop=True)
                    save_data(df2, csv_path)
                    st.session_state["show_toast"] = True
                    st.session_state["toast_message"] = f"✅ Deleted {len(indices)} row(s)"
                    st.rerun()

    if action == "Export":
        st.subheader("Export / Download CSV")
        st.download_button("Download current CSV", data=df.to_csv(index=False).encode("utf-8"), file_name="indiancrop_dataset.csv", mime="text/csv")

if __name__ == "__main__":
    main()
