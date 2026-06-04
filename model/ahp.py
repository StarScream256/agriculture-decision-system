import streamlit as st
from typing import List, Optional, Tuple, Literal, TypedDict
import pandas as pd
import numpy as np


class Criterion(TypedDict):
    name: str
    alias: str
    type: Literal["Benefit", "Cost", "Preference", "Categorical"]
    preference: Optional[float]


def reset_session_state():
    st.session_state.is_consistent = False
    st.session_state.is_calculated = False


def resolve_criteria_alias(col, with_scale=False):
    criteria_alias = {
        "N_SOIL": "Kandungan Nitrogen Tanah",
        "P_SOIL": "Kandungan Fosfor Tanah",
        "K_SOIL": "Kandungan Kalium Tanah",
        "TEMPERATURE": "Suhu",
        "HUMIDITY": "Kelembapan",
        "ph": "pH Tanah",
        "RAINFALL": "Curah Hujan",
        "STATE": "Provinsi",
        "CROP_PRICE": "Harga Pasar",
        "CROP": "Jenis Tanaman"
    }

    scaled_criteria_alias = {
        "N_SOIL": "Kandungan Nitrogen Tanah (N)",
        "P_SOIL": "Kandungan Fosfor Tanah (P)",
        "K_SOIL": "Kandungan Kalium Tanah (K)",
        "TEMPERATURE": "Suhu (°C)",
        "HUMIDITY": "Kelembapan (%)",
        "ph": "pH Tanah",
        "RAINFALL": "Curah Hujan (mm)",
        "STATE": "Provinsi",
        "CROP_PRICE": "Harga Pasar",
        "CROP": "Jenis Tanaman"
    }
    alias_map = scaled_criteria_alias if with_scale else criteria_alias
    return alias_map.get(col, col)


def resolve_criteria_type(col):
    if col in []:
        return "Cost"
    elif col in ["N_SOIL", "P_SOIL", "K_SOIL", "TEMPERATURE", "HUMIDITY", "ph", "RAINFALL", "CROP_PRICE"]:
        return "Benefit"
    # elif col in ["N_SOIL", "P_SOIL", "K_SOIL", "TEMPERATURE", "HUMIDITY", "ph", "RAINFALL"]:
    #     return "Preference"
    elif col in ["STATE", "CROP"]:
        return "Categorical"

def parse_ahp_value(selected_option: str):
    number_str = selected_option.split(" - ")[0]
    
    if "/" in number_str: # kalau pecahan
        parts = number_str.split("/")
        return float(parts[0]) / float(parts[1])
    else:
        return float(number_str)


def configure_criteria(df: pd.DataFrame) -> Tuple[List[Criterion], np.ndarray]:
    st.subheader("⚙️ Konfigurasi Kriteria dan Bobot")
    st.write("Tentukan bobot kepentingan untuk setiap kriteria dengan membandingkan secara berpasangan.")

    criteria: List[Criterion] = [{
        "name": col,
        "alias": resolve_criteria_alias(col, with_scale=False),
        "type": resolve_criteria_type(col),
        "preference": None
    } for col in df.columns]
    ahp_criteria = [c for c in criteria if c["type"] != "Categorical"]
    n_criteria = len(ahp_criteria)
    pairwise_comparisons = {}

    for i in range(n_criteria):
        if i == n_criteria - 1:
            break

        current_criterion = ahp_criteria[i]
        with st.expander(f"**{current_criterion['alias']}**"):
            st.write(f"Seberapa penting **{current_criterion['alias']}** dibandingkan dengan ...")

            for j in range(i + 1, n_criteria):
                target_criterion = ahp_criteria[j]
                key = f"comp_{current_criterion['name']}_vs_{target_criterion['name']}" # unique key untuk selectbox
                selected_value = st.selectbox(
                    key=key,
                    label=f"{target_criterion['alias']}",
                    on_change=reset_session_state,
                    options=[
                        "1 - Sama penting",

                        f"1/2 - Antara sama penting dan sedikit lebih penting {target_criterion['alias']}",
                        f"1/3 - Sedikit lebih penting {target_criterion['alias']}",
                        f"1/4 - Antara sedikit lebih penting dan lebih penting {target_criterion['alias']}",
                        f"1/5 - Lebih penting {target_criterion['alias']}",
                        f"1/6 - Antara lebih penting dan sangat lebih penting {target_criterion['alias']}",
                        f"1/7 - Sangat lebih penting {target_criterion['alias']}",
                        f"1/8 - Antara sangat lebih penting dan mutlak lebih penting {target_criterion['alias']}",
                        f"1/9 - Mutlak lebih penting {target_criterion['alias']}",


                        f"2 - Antara sama penting dan sedikit lebih penting {current_criterion['alias']}",
                        f"3 - Sedikit lebih penting {current_criterion['alias']}",
                        f"4 - Antara sedikit lebih penting dan lebih penting {current_criterion['alias']}",
                        f"5 - Lebih penting {current_criterion['alias']}",
                        f"6 - Antara lebih penting dan sangat lebih penting {current_criterion['alias']}",
                        f"7 - Sangat lebih penting {current_criterion['alias']}",
                        f"8 - Antara sangat lebih penting dan mutlak lebih penting {current_criterion['alias']}",
                        f"9 - Mutlak lebih penting {current_criterion['alias']}"
                    ],
                )
                pairwise_comparisons[key] = selected_value
    
    # buat matriks perbandingan berpasangan
    ahp_criteria_matrix: np.ndarray = np.ones((n_criteria, n_criteria))
    for i in range(n_criteria):
        for j in range(i + 1, n_criteria):
            current_criterion = ahp_criteria[i]
            target_criterion = ahp_criteria[j]
            # buat ulang key yang sama untuk akses nilai perbandingan
            key = f"comp_{current_criterion['name']}_vs_{target_criterion['name']}"
            selected_option = pairwise_comparisons[key]
            val = parse_ahp_value(selected_option)
            ahp_criteria_matrix[i, j] = val
            ahp_criteria_matrix[j, i] = 1.0 / val
    
    return ahp_criteria, ahp_criteria_matrix


def transform(alternative: pd.Series) -> np.ndarray:
    # menghindari division by zero karena ada nilai 0
    clean_alt = [x if x != 0 else 0.01 for x in alternative]
    return np.array([[i/j for j in clean_alt] for i in clean_alt])


def normalize_and_get_weight(matrix: np.ndarray):
    normalized = matrix / matrix.sum(axis=0)
    weight = normalized.mean(axis=1)
    return weight


def consistency_check(matrix: np.ndarray, weight: np.ndarray):
    n = len(matrix)
    ri_values = [0.00, 0.00, 0.58, 0.90, 1.12, 1.24, 1.32, 1.41, 1.45, 1.49]

    # lambda max
    cv = np.dot(matrix, weight) / weight
    eigenvalue = cv.mean()
    
    ci = (eigenvalue - n) / (n - 1)
    if abs(ci) < 1e-10: 
        ci = 0.0

    if n <= len(ri_values):
        ri = ri_values[n - 1]
    else:
        # approksimasi Alonso & Lamata untuk matriks > 10
        ri = (1.45 * (n - 1)) / n
    cr = ci / ri if ri > 0 else 0.0

    return ci, cr