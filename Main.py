import pandas as pd
import numpy as np
import streamlit as st
import requests
from typing import TypedDict, List, Optional, Tuple, Union, Literal

# type hint
class Criterion(TypedDict):
    name: str
    alias: str
    type: Literal["Benefit", "Cost", "Preference", "Categorical"]
    preference: Optional[float]

# jangan di uncomment saat development, kena rate limit github 60 req/jam nggak bisa dipake lagi
# def get_contributor():
#     contributor = []
#     repo_url = "https://api.github.com/repos/StarScream256/agriculture-decision-system"
#     repo_response = requests.get(repo_url)
#     if repo_response.status_code == 200:
#         repo_data = repo_response.json()
#         contributor.append({
#             "login": repo_data["owner"]["login"],
#             "avatar_url": repo_data["owner"]["avatar_url"],
#         })
    
#     repo_html = f'<a href="{repo_url}" target="_blank"><img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" style="border-radius:50%; width:40px; height:40px; margin-right:10px;" title="Repo"></a>'
    
#     contributors_url = repo_url + "/contributors"
#     contributors_response = requests.get(contributors_url)
#     if contributors_response.status_code == 200:
#         contributors_data = contributors_response.json()
#         if contributors_data:
#             for contrib in contributors_data:
#                 contributor.append({
#                     "login": contrib["login"],
#                     "avatar_url": contrib["avatar_url"],
#                 })

#     img_html = "".join([
#         f'<a href="https://github.com/{c["login"]}" target="_blank"><img src="{c["avatar_url"]}" style="border-radius:50%; width:40px; height:40px; margin-right:10px;" title="{c["login"]}"></a>'
#         for c in contributor
#     ])
#     st.write(contributor)

#     st.markdown(
#         f'<div style="display: flex; flex-wrap: wrap;">{repo_html}{img_html}</div>', 
#         unsafe_allow_html=True
#     )

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
    if col in ["CROP_PRICE"]:
        return "Cost"
    elif col in ["N_SOIL", "P_SOIL", "K_SOIL", "TEMPERATURE", "HUMIDITY", "ph", "RAINFALL"]:
        return "Preference"
    elif col in ["STATE", "CROP"]:
        return "Categorical"

def configure_criteria(df: pd.DataFrame) -> Tuple[List[Criterion], np.ndarray]:
    st.subheader("⚙️ Konfigurasi Kriteria dan Bobot")

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

                        "1/2 - Antara",
                        f"1/3 - Sedikit lebih penting {target_criterion['alias']}",
                        "1/4 - Antara",
                        f"1/5 - Lebih penting {target_criterion['alias']}",
                        "1/6 - Antara",
                        f"1/7 - Sangat lebih penting {target_criterion['alias']}",
                        "1/8 - Antara",
                        f"1/9 - Mutlak lebih penting {target_criterion['alias']}",


                        "2 - Antara",
                        f"3 - Sedikit lebih penting {current_criterion['alias']}",
                        "4 - Antara",
                        f"5 - Lebih penting {current_criterion['alias']}",
                        "6 - Antara",
                        f"7 - Sangat lebih penting {current_criterion['alias']}",
                        "8 - Antara",
                        f"9 - Mutlak lebih penting {current_criterion['alias']}"
                    ],
                )
                pairwise_comparisons[key] = selected_value
    
    # buat matriks perbandingan berpasangan
    ahp_matrix: np.ndarray = np.ones((n_criteria, n_criteria))
    for i in range(n_criteria):
        for j in range(i + 1, n_criteria):
            current_criterion = ahp_criteria[i]
            target_criterion = ahp_criteria[j]
            # buat ulang key yang sama untuk akses nilai perbandingan
            key = f"comp_{current_criterion['name']}_vs_{target_criterion['name']}"
            selected_option = pairwise_comparisons[key]
            val = parse_ahp_value(selected_option)
            ahp_matrix[i, j] = val
            ahp_matrix[j, i] = 1.0 / val
    
    return ahp_criteria, ahp_matrix

def configure_preferences(df: pd.DataFrame, ahp_criteria: List[Criterion]):
    st.subheader("🔧 Konfigurasi Nilai Preferensi Ideal Setiap Kriteria")
    st.write(
        """
        Ubah nilai preferensi ideal di bawah ini sesuai dengan tujuan atau kebutuhan lahan yang akan Anda cari. 
        Nilai ini akan digunakan dalam perhitungan AHP untuk menentukan alternatif terbaik di setiap kriteria.
        """
    )

    ideal_preferences = {
        "N_SOIL": 65,
        "P_SOIL": 45,
        "K_SOIL": 35,
        "TEMPERATURE": 25,
        "HUMIDITY": 65,
        "ph": 6.4,
        "RAINFALL": 100,
    }

    for criterion in ahp_criteria:
        pref = st.number_input(
            key=f"pref_{criterion['name']}",
            label=f"{resolve_criteria_alias(criterion['name'], with_scale=True)}", 
            value=ideal_preferences.get(
                criterion['name'], 
                df[criterion["name"]].max() 
                    if criterion["type"] == "Benefit" 
                    else df[criterion["name"]].min()
            )
        )
        criterion["preference"] = pref
        
    return ahp_criteria

def show_results():
    st.subheader("📊 Pilihan Lahan Terbaik Untuk Anda")
    st.markdown("`Mungkin bisa ada filter CROP atau STATE`")

def main():
    df = pd.read_csv("indiancrop_dataset.csv")
    project_name = "Sistem Pendukung Keputusan untuk Pemilihan Lahan dengan Metode AHP"
    st.set_page_config(
        page_title=project_name,
        # page_icon="",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title(project_name)
    st.write(
        """
        Sistem ini membantu menentukan prioritas pemilihan lahan pertanian 
        yang paling optimal dengan mempertimbangkan berbagai kriteria 
        (seperti kualitas tanah, ketersediaan air, dan aksesibilitas) 
        menggunakan metode AHP.
        """
    )

    # get_contributor()

    st.divider()
    
    ahp_overview()

    load_sample_data(df)

    st.divider()

    # ahp_criteria: sesuai class Criterion
    # ahp_matrix: matriks perbandingan berpasangan skala saaty
    # dimana kriteria yang dibandingkan adalah semua kriteria non-Categorical (Benefit, Cost, Preference)
    ahp_criteria, ahp_matrix = configure_criteria(df)

    st.divider()

    ahp_criteria = configure_preferences(df, ahp_criteria)

    # debug
    # st.write(ahp_criteria)
    # st.write(ahp_matrix)

    st.divider()

    show_results()

if __name__ == "__main__":
	main()