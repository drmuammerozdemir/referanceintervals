import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy import stats

# --- HOFFMANN FONKSİYONU ---
def calculate_hoffmann(data, use_log=True):
    data = data[data > 0]
    working_data = np.log(data) if use_log else data
    sorted_data = np.sort(working_data)
    n = len(sorted_data)
    p = (np.arange(1, n + 1) - 0.5) / n
    z = stats.norm.ppf(p)
    mask = (p > 0.20) & (p < 0.80)
    if len(z[mask]) < 5: return None
    slope, intercept, r_val, _, _ = stats.linregress(z[mask], sorted_data[mask])
    low_z = intercept + (-1.96 * slope)
    high_z = intercept + (1.96 * slope)
    return (np.exp(low_z), np.exp(high_z), r_val**2) if use_log else (low_z, high_z, r_val**2)

st.set_page_config(page_title="LabRef Pro", layout="wide")
st.title("🧪 Laboratuvar Referans Aralığı Analizörü")

uploaded_file = st.file_uploader("Dosya Yükleyin (.xlsx, .xls, .csv, .sav)", type=['csv', 'xlsx', 'xls', 'sav'])

if uploaded_file:
    # Dosya okuma (Önceki versiyondaki gibi)
    ext = uploaded_file.name.split('.')[-1]
    if ext == 'csv': df = pd.read_csv(uploaded_file)
    elif ext in ['xls', 'xlsx']: df = pd.read_excel(uploaded_file)
    elif ext == 'sav':
        import pyreadstat
        with open("temp.sav", "wb") as f: f.write(uploaded_file.getbuffer())
        df, _ = pyreadstat.read_sav("temp.sav")

    # --- SÜTUN SEÇİMİ ---
    c1, c2, c3 = st.columns(3)
    with c1: test_col = st.selectbox("Test Sonucu (Sayısal Değer)", df.columns, index=df.columns.get_loc("TEST_DEGERI") if "TEST_DEGERI" in df.columns else 0)
    with c2: name_col = st.selectbox("Tetkik İsmi Sütunu", df.columns, index=df.columns.get_loc("TETKIK_ISMI") if "TETKIK_ISMI" in df.columns else 0)
    with c3: selected_test = st.selectbox("Analiz Edilecek Test", df[name_col].unique())

    # --- VERİ TEMİZLEME ÖZETİ (YENİ BÖLÜM) ---
    st.subheader("📊 Veri Temizleme Özeti")
    
    # Ham veriyi işle
    raw_subset = df[df[name_col] == selected_test].copy()
    total_raw = len(raw_subset)
    
    # Sayıya çevirme (Virgül/Nokta temizliği dahil)
    if raw_subset[test_col].dtype == object:
        raw_subset[test_col] = raw_subset[test_col].str.replace(',', '.', regex=False)
    
    raw_subset['numeric_val'] = pd.to_numeric(raw_subset[test_col], errors='coerce')
    
    valid_data = raw_subset[raw_subset['numeric_val'] > 0].dropna(subset=['numeric_val'])
    total_valid = len(valid_data)
    lost_data = total_raw - total_valid

    # Özet Kartları
    v1, v2, v3 = st.columns(3)
    v1.metric("Toplam Ham Veri", f"{total_raw} satır")
    v2.metric("Hatalı/Eksik Veri (Elenen)", f"{lost_data} satır", delta_color="inverse")
    v3.metric("Analize Hazır Veri", f"{total_valid} satır")

    if lost_data > 0:
        st.warning(f"⚠️ Dikkat: {lost_data} adet veri sayısal olmadığı veya sıfırdan küçük olduğu için analiz dışı bırakıldı. (Örn: <0.01, Metinler veya boş hücreler)")

    # --- HESAPLAMA ---
    if total_valid > 50:
        log_on = st.toggle("Log-Normal Dönüşüm", value=True)
        res = calculate_hoffmann(valid_data['numeric_val'].values, use_log=log_on)
        
        if res:
            low, high, r2 = res
            st.divider()
            st.success(f"**Hesaplanan Referans Aralığı: {low:.3f} - {high:.3f}** (R²: {r2:.4f})")
            
            # Grafik
            fig = px.histogram(valid_data['numeric_val'], nbins=100, title="Filtrelenmiş Veri Dağılımı")
            fig.add_vrect(x0=low, x1=high, fillcolor="green", opacity=0.2, annotation_text="RI")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Seçilen test için 50'den fazla geçerli sonuç bulunamadı. Lütfen 'Test Sonucu' sütununun doğru seçildiğinden emin olun.")
