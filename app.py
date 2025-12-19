import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats

# --- Sayfa Ayarları ---
st.set_page_config(page_title="LabRef: RI Analyzer", layout="wide")

def hoffmann_method(data):
    """
    Hoffmann yöntemini uygulayarak Referans Aralığı hesaplar.
    """
    # 1. Veriyi sırala ve kümülatif frekansları hesapla
    sorted_data = np.sort(data)
    n = len(sorted_data)
    cumulative_prob = (np.arange(1, n + 1) - 0.5) / n
    
    # 2. Normal dağılımın Z-skorlarını hesapla
    z_scores = stats.norm.ppf(cumulative_prob)
    
    # 3. Lineer regresyon (Z-skorları vs Gözlemlenen Değerler)
    # Genellikle verinin merkez %50'lik kısmı doğrusal ilişki için en iyisidir
    mask = (cumulative_prob > 0.25) & (cumulative_prob < 0.75)
    slope, intercept, r_value, p_value, std_err = stats.linregress(z_scores[mask], sorted_data[mask])
    
    # 4. RI Hesapla (Mean +/- 1.96 * SD)
    ri_lower = intercept + (-1.96 * slope)
    ri_upper = intercept + (1.96 * slope)
    
    return ri_lower, ri_upper, slope, intercept

# --- Arayüz ---
st.title("🧪 LabRef: Dolaylı Referans Aralığı Hesaplayıcı")
st.markdown("""
Bu araç, hastane veri tabanındaki büyük verileri (Big Data) kullanarak laboratuvar tetkikleri için referans aralıkları belirler. 
**Yöntem:** Hoffmann İstatistiksel Model (Python Native).
""")

uploaded_file = st.file_uploader("Veri Setini Yükleyin (CSV)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    # Sütun Seçimi
    col1, col2 = st.columns(2)
    with col1:
        test_col = st.selectbox("Test Sonucu Sütunu", df.columns, index=df.columns.get_loc("TEST_DEGERI") if "TEST_DEGERI" in df.columns else 0)
    with col2:
        test_name = st.selectbox("Analiz Edilecek Tetkik", df['TETKIK_ISMI'].unique())

    # Veri Filtreleme
    subset = df[df['TETKIK_ISMI'] == test_name].copy()
    subset[test_col] = pd.to_numeric(subset[test_col], errors='coerce')
    clean_data = subset[test_col].dropna().values
    
    # Analiz
    if st.button("Analizi Başlat"):
        ri_low, ri_high, slope, intercept = hoffmann_method(clean_data)
        
        # Göstergeler
        m1, m2, m3 = st.columns(3)
        m1.metric("Veri Sayısı", f"{len(clean_data)}")
        m2.metric("Alt Limit (2.5%)", f"{max(0, ri_low):.3f}")
        m3.metric("Üst Limit (97.5%)", f"{ri_high:.3f}")
        
        # Grafik 1: Histogram
        fig_hist = px.histogram(clean_data, nbins=100, title=f"{test_name} Dağılımı ve Hesaplanan Aralık")
        fig_hist.add_vline(x=ri_low, line_dash="dash", line_color="red", annotation_text="Alt Limit")
        fig_hist.add_vline(x=ri_high, line_dash="dash", line_color="red", annotation_text="Üst Limit")
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Grafik 2: Hoffmann Plot (Lineerleştirme)
        st.subheader("Hoffmann Lineerleştirme Grafiği")
        z_scores = stats.norm.ppf((np.arange(1, len(clean_data) + 1) - 0.5) / len(clean_data))
        fig_hoff = go.Figure()
        fig_hoff.add_trace(go.Scatter(x=z_scores, y=np.sort(clean_data), mode='markers', name='Veri Noktaları'))
        fig_hoff.add_trace(go.Scatter(x=z_scores, y=intercept + slope*z_scores, mode='lines', name='Hoffmann Hattı', line=dict(color='red')))
        st.plotly_chart(fig_hoff, use_container_width=True)
