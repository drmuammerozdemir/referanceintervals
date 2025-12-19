import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy import stats

# --- GELİŞMİŞ HOFFMANN FONKSİYONU ---
def calculate_hoffmann(data, use_log=True):
    if len(data) < 20: return None
    
    data = data[data > 0]
    working_data = np.log(data) if use_log else data
    sorted_data = np.sort(working_data)
    n = len(sorted_data)
    
    p = (np.arange(1, n + 1) - 0.5) / n
    z = stats.norm.ppf(p)
    
    # Lineer regresyon (Merkez %40-60 dilimi odaklı)
    mask = (p > 0.20) & (p < 0.80)
    if len(z[mask]) < 5: return None
    
    slope, intercept, r_val, _, _ = stats.linregress(z[mask], sorted_data[mask])
    
    # RI Hesaplama: Mean +/- 1.96 * SD
    low_z = intercept + (-1.96 * slope)
    high_z = intercept + (1.96 * slope)
    
    # İstatistiksel parametreler
    # Log-normal durumda geometrik ortalama ve SD yaklaşımları kullanılır
    res = {
        "low": np.exp(low_z) if use_log else low_z,
        "high": np.exp(high_z) if use_log else high_z,
        "r2": r_val**2,
        "n": n,
        "mean": np.exp(intercept) if use_log else intercept,
        "sd": np.exp(slope) if use_log else slope # Log-SD (Dağılım genişliği)
    }
    return res

st.set_page_config(page_title="LabRef Pro: Multi-Group Analyzer", layout="wide")
st.title("🔬 Gelişmiş Referans Aralığı Analiz Paneli")

uploaded_file = st.file_uploader("Veri Setini Yükleyin (.xlsx, .csv, .sav)", type=['csv', 'xlsx', 'xls', 'sav'])

if uploaded_file:
    # Veri Okuma
    ext = uploaded_file.name.split('.')[-1]
    if ext == 'csv': df = pd.read_csv(uploaded_file)
    elif ext in ['xls', 'xlsx']: df = pd.read_excel(uploaded_file)
    elif ext == 'sav':
        import pyreadstat
        with open("temp.sav", "wb") as f: f.write(uploaded_file.getbuffer())
        df, _ = pyreadstat.read_sav("temp.sav")

    # --- FİLTRELEME PANELİ ---
    st.sidebar.header("🔍 Analiz Filtreleri")
    
    test_col = st.sidebar.selectbox("Test Sonucu Sütunu", df.columns, index=df.columns.get_loc("TEST_DEGERI") if "TEST_DEGERI" in df.columns else 0)
    name_col = st.sidebar.selectbox("Tetkik İsmi Sütunu", df.columns, index=df.columns.get_loc("TETKIK_ISMI") if "TETKIK_ISMI" in df.columns else 0)
    selected_test = st.sidebar.selectbox("Test Seçin", df[name_col].unique())
    
    st.sidebar.divider()
    
    # Cinsiyet Seçimi
    cinsiyet_opsiyon = df['CINSIYET'].unique().tolist()
    selected_genders = st.sidebar.multiselect("Cinsiyet Filtresi", options=cinsiyet_opsiyon, default=cinsiyet_opsiyon)
    
    # Yaş Aralığı (Manuel Giriş)
    st.sidebar.write("Yaş Aralığı")
    age_col = "YASI" if "YASI" in df.columns else df.columns[0]
    col_a1, col_a2 = st.sidebar.columns(2)
    min_age = col_a1.number_input("Min Yaş", value=0)
    max_age = col_a2.number_input("Max Yaş", value=120)

    # --- VERİ İŞLEME ---
    mask = (df[name_col] == selected_test) & \
           (df['CINSIYET'].isin(selected_genders)) & \
           (df[age_col] >= min_age) & \
           (df[age_col] <= max_age)
    
    working_df = df[mask].copy()
    
    # Sayısal Temizlik
    if working_df[test_col].dtype == object:
        working_df[test_col] = working_df[test_col].str.replace(',', '.', regex=False)
    working_df['val'] = pd.to_numeric(working_df[test_col], errors='coerce')
    clean_values = working_df[working_df['val'] > 0]['val'].dropna().values

    # --- ANA EKRAN ---
    st.subheader(f"📊 Analiz Raporu: {selected_test}")
    st.write(f"**Filtre:** {', '.join(selected_genders)} | Yaş: {min_age}-{max_age}")

    if len(clean_values) > 20:
        log_on = st.checkbox("Log-Normal Dönüşüm Uygula", value=True)
        res = calculate_hoffmann(clean_values, use_log=log_on)
        
        if res:
            # Grafik
            fig = px.histogram(clean_values, nbins=100, title="Seçilen Grubun Dağılımı")
            fig.add_vrect(x0=res['low'], x1=res['high'], fillcolor="green", opacity=0.2, annotation_text="Ref. Aralığı")
            st.plotly_chart(fig, use_container_width=True)
            
            # AKADEMİK ÖZET TABLOSU
            st.divider()
            st.subheader("📋 Akademik Sonuç Tablosu")
            
            # Tablo verisini hazırla
            summary_data = {
                "Parametre": ["Alt Limit (2.5%)", "Üst Limit (97.5%)", "R² (Model Uyumu)", "Örnek Sayısı (n)", "Ortalama (Modellenen)", "Standart Sapma"],
                "Değer": [
                    f"{res['low']:.4f}", 
                    f"{res['high']:.4f}", 
                    f"{res['r2']:.4f}", 
                    f"{int(res['n'])}", 
                    f"{res['mean']:.4f}", 
                    f"{res['sd']:.4f}"
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            st.table(summary_df)
            
            # CSV İndirme Butonu (Makale için tabloyu dışa aktarma)
            csv = summary_df.to_csv(index=False).encode('utf-8')
            st.download_button("Tabloyu Excel/CSV Olarak İndir", csv, f"RI_Sonuc_{selected_test}.csv", "text/csv")

        else:
            st.error("Model bu veri grubu için yakınsayamadı. Lütfen veri miktarını veya filtreleri kontrol edin.")
    else:
        st.warning(f"Seçilen kriterlere göre sadece {len(clean_values)} veri bulundu. Analiz için en az 20-50 veri gereklidir.")
