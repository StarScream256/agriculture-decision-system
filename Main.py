import pandas as pd
import numpy as np
import streamlit as st
import requests
import matplotlib.pyplot as plt
from typing import TypedDict, List, Optional, Tuple, Union, Literal

# type hint
class Criterion(TypedDict):
    name: str
    alias: str
    type: Literal["Benefit", "Cost", "Preference", "Categorical"]
    preference: Optional[float]

# jangan di uncomment saat development, kena rate limit github 60 req/jam nggak bisa dipake lagi, nunggu 1 jam buat reset
def get_contributor():
    contributor = []
    repo_url = "https://api.github.com/repos/StarScream256/agriculture-decision-system"
    repo_response = requests.get(repo_url)
    if repo_response.status_code == 200:
        repo_data = repo_response.json()
        contributor.append({
            "login": repo_data["owner"]["login"],
            "avatar_url": repo_data["owner"]["avatar_url"],
        })
    
    repo_html = f'<a href="{repo_url}" target="_blank"><img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" style="border-radius:50%; width:40px; height:40px; margin-right:10px;" title="Repo"></a>'
    
    contributors_url = repo_url + "/contributors"
    contributors_response = requests.get(contributors_url)
    if contributors_response.status_code == 200:
        contributors_data = contributors_response.json()
        if contributors_data:
            for contrib in contributors_data:
                contributor.append({
                    "login": contrib["login"],
                    "avatar_url": contrib["avatar_url"],
                })

    unique_contributors = {c["login"]: c for c in contributor}
    contributor = list(unique_contributors.values())
    contrib_image_html = "".join([
        f'<a href="https://github.com/{c["login"]}" target="_blank"><img src="{c["avatar_url"]}" style="border-radius:50%; width:40px; height:40px; margin-right:10px;" title="{c["login"]}"></a>'
        for c in contributor
    ])
    # st.write(contributor)

    st.markdown(
        f'<div style="display: flex; flex-wrap: wrap;">{repo_html}{contrib_image_html}</div>', 
        unsafe_allow_html=True
    )

def ahp_overview():
    # st.subheader("🔍 Overview Analytic Hierarchy Process (AHP)")
    with st.expander("Sekilas tentang Analytic Hierarchy Process (AHP)"):
        st.write(
            """
            AHP adalah metode pengambilan keputusan yang digunakan untuk mengatasi masalah kompleks dengan membagi masalah menjadi hierarki yang lebih sederhana. 

            Dalam AHP, penting untuk memastikan bahwa perbandingan berpasangan dilakukan dengan hati-hati untuk menghasilkan bobot yang akurat dan konsisten. Bobot kriteria dalam AHP menggunakan skala perbandingan yang biasanya berkisar antara 1 hingga 9 (***Skala Saaty***), di mana 1 menunjukkan bahwa dua elemen memiliki kepentingan yang sama, dan 9 menunjukkan bahwa satu elemen sangat lebih penting daripada yang lain.

            **Skala Saaty**:
            - 1: Sama penting
            - 3: Sedikit lebih penting
            - 5: Lebih penting
            - 7: Sangat lebih penting
            - 9: Mutlak lebih penting
            - 2, 4, 6, 8: Nilai antara untuk menunjukkan tingkat kepentingan yang lebih halus
            """
        )

def load_sample_data(df: pd.DataFrame, amount=10):
    with st.expander("Contoh Data Lahan Pertanian"):
        st.dataframe(df.head(amount))

def parse_ahp_value(selected_option: str):
    number_str = selected_option.split(" - ")[0]
    
    if "/" in number_str: # kalau pecahan
        parts = number_str.split("/")
        return float(parts[0]) / float(parts[1])
    else:
        return float(number_str)

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

def normalize_criteria(ahp_criteria: List[Criterion], ahp_criteria_matrix: np.ndarray):
    normalized_weights = ahp_criteria_matrix / ahp_criteria_matrix.sum(axis=0)
    criteria_weights = normalized_weights.mean(axis=1)
    return criteria_weights

def weighted_product(ahp_criteria: List[Criterion], criteria_weights: np.ndarray, df: pd.DataFrame):
    col_names = [c["name"] for c in ahp_criteria]
    vector_s = df.copy()
    vector_s[col_names] = vector_s[col_names].pow(criteria_weights)
    vector_s["Total"] = vector_s[col_names].prod(axis=1)

    vector_v = vector_s["Total"] / vector_s["Total"].sum()
    df_vector_v = df.copy()
    df_vector_v["Vector V"] = vector_v
    vector_v = df_vector_v
    return vector_s, vector_v

def consistency_check(ahp_criteria_matrix: np.ndarray):
    n = ahp_criteria_matrix.shape[0]
    eigenvalues, _ = np.linalg.eig(ahp_criteria_matrix)
    max_eigenvalue = np.max(np.real(eigenvalues))
    ci = (max_eigenvalue - n) / (n - 1)

    ri_values = [0.00, 0.00, 0.58, 0.90, 1.12, 1.24, 1.32, 1.41, 1.45, 1.49]
    ri = ri_values[n - 1] if n <= len(ri_values) else ri_values[-1]

    cr = ci / ri if ri != 0 else 0
    return cr

def show_pairwise_comparison_matrix(ahp_criteria: List[Criterion], ahp_criteria_matrix: np.ndarray):
    # st.subheader("📊 Matriks Perbandingan Berpasangan Kriteria")
    st.dataframe(
        pd.DataFrame(
            ahp_criteria_matrix, 
            index=[c["alias"] for c in ahp_criteria], 
            columns=[c["alias"] for c in ahp_criteria]
        )
    )

def show_normalized_criteria(ahp_criteria: List[Criterion], criteria_weights: np.ndarray):
    # st.subheader("📊 Bobot Kriteria Setelah Normalisasi")
    df = pd.DataFrame({
        "Bobot Kriteria": criteria_weights
    }, index=[f"{c["name"]} - {c["alias"]}" for c in ahp_criteria])
    df.loc["Total"] = df["Bobot Kriteria"].sum()
    st.dataframe(df)

def show_weighted_product(df: pd.DataFrame, vector_s: pd.DataFrame, vector_v: pd.Series):
    # st.subheader("📊 Nilai Alternatif Setelah Dikalikan dengan Bobot Kriteria")
    tabs = st.tabs(["Data Asli", "Vector S (Nilai Alternatif)", "Vector V (Nilai Normalisasi)"])
    with tabs[0]:
        st.dataframe(df)
    with tabs[1]:
        st.dataframe(vector_s)
    with tabs[2]:
        st.dataframe(vector_v)

def show_detailed_calculations(df: pd.DataFrame, ahp_criteria: List[Criterion], ahp_criteria_matrix: np.ndarray):
    with st.expander("Detail Perhitungan"):
        tabs = st.tabs(["Matriks Perbandingan Berpasangan", "Normalisasi Bobot Kriteria", "Ranking Alternatif"])
        with tabs[0]:
            show_pairwise_comparison_matrix(ahp_criteria, ahp_criteria_matrix)

        with tabs[1]:
            criteria_weights = normalize_criteria(ahp_criteria, ahp_criteria_matrix)
            show_normalized_criteria(ahp_criteria, criteria_weights)

        with tabs[2]:
            vector_s, vector_v = weighted_product(ahp_criteria, criteria_weights, df)
            show_weighted_product(df, vector_s, vector_v)

def show_results(df: pd.DataFrame, vector_s: pd.DataFrame, vector_v: pd.DataFrame):
    st.divider()
    st.subheader("📊 Pilihan Lahan Terbaik Untuk Anda")
    st.write("Berdasarkan perhitungan AHP, berikut adalah rekomendasi lahan pertanian yang paling optimal untuk dipilih. Anda dapat menyaring berdasarkan provinsi atau jenis tanaman untuk melihat rekomendasi yang lebih spesifik.")
    cols = st.columns(3)
    with cols[0]:
        selected_state = st.selectbox(
            label="Pilih Provinsi",
            options=np.concatenate([["Semua Provinsi"], df["STATE"].unique()])
        )
    
    with cols[1]:
        selected_crop = st.selectbox(
            label="Pilih Jenis Tanaman",
            options=np.concatenate([["Semua Jenis Tanaman"], df["CROP"].unique()])
        )

    result_df = vector_v.copy()
    if selected_state != "Semua Provinsi":
        result_df = result_df[result_df["STATE"] == selected_state]
    if selected_crop != "Semua Jenis Tanaman":
        result_df = result_df[result_df["CROP"] == selected_crop]

    result_df = result_df.sort_values("Vector V", ascending=False)

    with cols[2]:
        show_count = st.number_input(
            label="Jumlah Hasil Tertampil",
            min_value=1,
            max_value=max(1,len(result_df)),
            value=min(10, max(1, len(result_df))),
            step=1
        )

    st.write(f"Ditemukan {len(result_df)} alternatif yang sesuai dengan filter Anda.")
    st.success(f"👍Pilihan terbaik bagi anda adalah lahan nomor **{result_df.index[0]}** di **{result_df.iloc[0]['STATE']}** yang cocok untuk menanam **{result_df.iloc[0]['CROP']}** dengan skor {result_df.iloc[0]['Vector V']:.4f}.")

    st.dataframe(
        result_df.head(show_count)
    )

def main():
    df = pd.read_csv("indiancrop_dataset.csv")
    df.index = "FARM_" + df.index.astype(str)

    project_name = "Sistem Pendukung Keputusan untuk Pemilihan Lahan dengan Metode AHP"
    st.set_page_config(
        page_title=project_name,
        # page_icon="",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title(project_name)
    st.write("Sistem ini membantu menentukan prioritas pemilihan lahan pertanian yang paling optimal dengan mempertimbangkan berbagai kriteria (seperti kualitas tanah, ketersediaan air, dan aksesibilitas) menggunakan metode AHP.")

    get_contributor()
    
    st.divider()
    ahp_overview()
    load_sample_data(df)

    
    # ahp_criteria: sesuai class Criterion
    # ahp_criteria_matrix: matriks perbandingan berpasangan skala saaty
    # dimana kriteria yang dibandingkan adalah semua kriteria non-Categorical (Benefit, Cost, Preference)
    st.divider()
    ahp_criteria, ahp_criteria_matrix = configure_criteria(df)
    
    # consistency check
    if st.button("👁️ Cek Konsistensi Perbandingan"):
        cr = consistency_check(ahp_criteria_matrix)
        if cr < 0.1:
            st.success(f"👌Konsistensi baik (CR = {cr:.4f} < 0.1)")
            vector_s, vector_v = weighted_product(
                ahp_criteria, 
                normalize_criteria(
                    ahp_criteria, 
                    ahp_criteria_matrix
                ), df)

            cols = st.columns([1, 4, 1])
            with cols[1]:
                figure, axis = plt.subplots(figsize=(4,4))
                axis.pie(
                    normalize_criteria(ahp_criteria, ahp_criteria_matrix), 
                    labels=[c["alias"] for c in ahp_criteria], 
                    autopct='%1.1f%%',
                    textprops={ 'fontsize': 8 }
                )
                axis.axis('equal')
                st.pyplot(figure)

            show_results(df, vector_s, vector_v)
            show_detailed_calculations(df, ahp_criteria, ahp_criteria_matrix)
        else:
            st.error(f"👎Konsistensi buruk (CR = {cr:.4f} >= 0.1). Pertimbangkan untuk meninjau kembali perbandingan.")
        
    

if __name__ == "__main__":
	main()