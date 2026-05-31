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
    st.navigation()
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


def reset_session_state():
    st.session_state.is_consistent = False
    st.session_state.is_calculated = False


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


def filter_results(df: pd.DataFrame):
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

    filtered_df = df.copy()
    if selected_state != "Semua Provinsi":
        filtered_df = filtered_df[filtered_df["STATE"] == selected_state]
    if selected_crop != "Semua Jenis Tanaman":
        filtered_df = filtered_df[filtered_df["CROP"] == selected_crop]

    with cols[2]:
        show_count = st.number_input(
            label="Jumlah Hasil Tertampil",
            min_value=1,
            max_value=max(1,len(filtered_df)),
            value=min(10, max(1, len(filtered_df))),
            step=1
        )
    
    return filtered_df, show_count


def main():
    df = pd.read_csv("data/indiancrop_dataset.csv")
    df.index = "FARM_" + df.index.astype(str)

    project_name = "Sistem Pendukung Keputusan untuk Pemilihan Lahan dengan Metode AHP"
    st.set_page_config(
        page_title=project_name,
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title(project_name)
    st.write("Sistem ini membantu menentukan prioritas pemilihan lahan pertanian yang paling optimal dengan mempertimbangkan berbagai kriteria (seperti kualitas tanah, ketersediaan air, dan aksesibilitas) menggunakan metode AHP.")

    # get_contributor()
    
    st.divider()
    ahp_overview()
    load_sample_data(df)

    # ahp_criteria: sesuai class Criterion
    # ahp_criteria_matrix: matriks perbandingan berpasangan skala saaty
    # dimana kriteria yang dibandingkan adalah semua kriteria non-Categorical (Benefit, Cost, Preference)
    st.divider()
    ahp_criteria, ahp_criteria_matrix = configure_criteria(df)
    criteria_weight = normalize_and_get_weight(ahp_criteria_matrix)
    
    # simpan state ke session
    if "is_consistent" not in st.session_state:
        st.session_state.is_consistent = False
    if "is_calculated" not in st.session_state:
        st.session_state.is_calculated = False

    # consistency check kriteria
    if st.button("👁️ Cek Konsistensi Perbandingan"):
        ci, cr = consistency_check(ahp_criteria_matrix,criteria_weight)
        if cr < 0.1:
            st.success(f"👌Konsistensi baik (CR = {cr:.4f} < 0.1)")
            st.session_state.is_consistent = not st.session_state.is_consistent
        else:
            st.error(f"👎Konsistensi buruk (CR = {cr:.4f} >= 0.1). Pertimbangkan untuk meninjau kembali perbandingan.")
        
    # pemicu tampil hasil
    if st.session_state.is_consistent:
        # visualisasi bobot kriteria
        cols = st.columns([1, 4, 1])
        with cols[1]:
            fig, ax = plt.subplots()
            ax.pie(
                criteria_weight, 
                labels=[f"{c['alias']}" for c in ahp_criteria], 
                autopct='%1.1f%%'
            )
            ax.axis('equal')
            st.pyplot(fig)

        if st.button("🎯Hitung dan Tampilkan Hasil Rekomendasi"):
            st.session_state.is_calculated = True
    
    # tampil hasil
    if st.session_state.is_consistent and st.session_state.is_calculated:
        filtered_df, show_count = filter_results(df)
        if len(filtered_df) > 0:
            transformed_n_soil = transform(filtered_df["N_SOIL"])
            transformed_p_soil = transform(filtered_df["P_SOIL"])
            transformed_k_soil = transform(filtered_df["K_SOIL"])
            transformed_temperature = transform(filtered_df["TEMPERATURE"])
            transformed_humidity = transform(filtered_df["HUMIDITY"])
            transformed_ph = transform(filtered_df["ph"])
            transformed_rainfall = transform(filtered_df["RAINFALL"])
            transformed_crop_price = transform(filtered_df["CROP_PRICE"])

            n_soil_weight = normalize_and_get_weight(transformed_n_soil)
            p_soil_weight = normalize_and_get_weight(transformed_p_soil)
            k_soil_weight = normalize_and_get_weight(transformed_k_soil)
            temperature_weight = normalize_and_get_weight(transformed_temperature)
            humidity_weight = normalize_and_get_weight(transformed_humidity)
            ph_weight = normalize_and_get_weight(transformed_ph)
            rainfall_weight = normalize_and_get_weight(transformed_rainfall)
            crop_price_weight = normalize_and_get_weight(transformed_crop_price)

            total_weight = np.array([n_soil_weight, p_soil_weight, k_soil_weight, temperature_weight, humidity_weight, ph_weight, rainfall_weight, crop_price_weight])
            final_scores = np.dot(total_weight.T, criteria_weight)

            result_df = pd.DataFrame({
                "STATE": filtered_df["STATE"],
                "CROP": filtered_df["CROP"],
                "Score": final_scores
            }, index=filtered_df.index).sort_values(by="Score", ascending=False)

            if len(result_df) > 0:
                st.write(f"Ditemukan {len(result_df)} alternatif yang sesuai dengan filter Anda.")
                st.success(f"👍Pilihan terbaik bagi anda adalah lahan nomor **{result_df.index[0]}** di **{result_df.iloc[0]['STATE']}** yang cocok untuk menanam **{result_df.iloc[0]['CROP']}** dengan skor {result_df.iloc[0]['Score']:.4f}.")
            else:
                st.warning("⚠️Tidak ditemukan alternatif yang sesuai dengan filter Anda. Silakan ubah pilihan filter untuk melihat hasil lainnya.")

            st.dataframe(result_df.head(show_count))

            # detail perhitungan
            st.subheader("🔎 Detail Perhitungan")
            st.write("Berikut adalah detail untuk setiap perhitungan yang dilakukan")
            with st.expander("Matriks Perbandingan Berpasangan Kriteria"):
                st.dataframe(pd.DataFrame(ahp_criteria_matrix, index=[c["alias"] for c in ahp_criteria], columns=[c["alias"] for c in ahp_criteria]))
            with st.expander("Bobot Kriteria"):
                df = pd.DataFrame({
                    "Bobot Kriteria": criteria_weight
                }, index=[f"{c["name"]} - {c["alias"]}" for c in ahp_criteria])
                df.loc["Total"] = df["Bobot Kriteria"].sum()
                st.dataframe(df)
            # bobot alternatif untuk setiap kriteria
            for i, c in enumerate(ahp_criteria):
                with st.expander(f"Bobot Alternatif untuk Kriteria **{c['alias']}**"):
                    ci, cr = consistency_check(transform(filtered_df[c["name"]]), normalize_and_get_weight(transform(filtered_df[c["name"]])))
                    st.write(f"Consistency index = {ci:.4f}, Consistency ratio = {cr:.4f}")
                    st.dataframe(pd.DataFrame(total_weight[i, :], index=filtered_df.index, columns=[f"Bobot {c['alias']}"]))
            with st.expander("Matriks Rekap Bobot Alternatif"):
                st.dataframe(pd.DataFrame(total_weight.T, index=filtered_df.index, columns=[f"Bobot {c['alias']}" for c in ahp_criteria]))
            with st.expander("Skor Akhir Setiap Alternatif"):
                st.dataframe(pd.DataFrame(final_scores, index=filtered_df.index, columns=["Skor Akhir"]))

        else:
            st.warning("⚠️Tidak ditemukan alternatif yang sesuai dengan filter Anda. Silakan ubah pilihan filter untuk melihat hasil lainnya.")


if __name__ == "__main__":
	main()