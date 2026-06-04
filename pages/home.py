import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from model.ahp import configure_criteria, consistency_check, normalize_and_get_weight, transform


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