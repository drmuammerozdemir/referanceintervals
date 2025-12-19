import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr

# --- R ORTAMI HAZIRLIĞI ---
def initialize_r_environment():
    """R paketlerini güvenli bir şekilde yükler."""
    try:
        utils = importr('utils')
        # Paket yüklü mü kontrol et
        is_installed = robjects.r('function(pkg) { pkg %in% rownames(installed.packages()) }')
        if not is_installed('refineR')[0]:
            st.info("refineR paketi kuruluyor (bu işlem birkaç dakika sürebilir)...")
            utils.chooseCRANmirror(ind=1)
            utils.install_packages(robjects.vectors.StrVector(['refineR']))
        return importr('refineR')
    except Exception as e:
        st.error(f"R konfigürasyon hatası: {e}")
        return None

# --- MANUEL VERİ DÖNÜŞÜMÜ VE ANALİZ ---
def run_refiner_analysis(data_series):
    """
    ContextVar hatasını önlemek için veriyi manuel çevirir ve 
    refineR'ın 'complex' modelini (Box-Cox) çalıştırır.
    """
    # 1. Python serisini saf listeye ve ardından R FloatVector'a çevir
    # Bu adım rpy2'nin otomatik dönüştürücülerine olan ihtiyacı ortadan kaldırır
    data_list = data_series.tolist()
    r_data = robjects.FloatVector(data_list)
    
    # 2. refineR paketini çağır ve analizi yap
    refineR = importr('refineR')
    
    # model='complex' sola çarpık veriler için Box-Cox optimizasyonu yapar
    # Box-Cox veriyi simetrik hale getirerek RI limitlerini belirler
    result = refineR.findRI(r_data, model='complex')
    
    # 3. Sonuçları R objesinden çek
    ri_limits = result.rx2('Normal')
    return float(ri_limits[0]), float(ri_limits[1])

# --- STREAMLIT ARAYÜZÜ ---
st.title("🔬 RefineR: Sola Çarpık Veri Analiz Paneli")

refine_pkg = initialize_r_environment()

uploaded_file = st.file_uploader("Veri Setinizi Yükleyin (.csv, .xlsx)", type=['csv', 'xlsx'])

if uploaded_file and refine_pkg:
    # Dosya okuma
    df = pd.read_excel(uploaded_file) if 'xlsx' in uploaded_file.name else pd.read_csv(uploaded_file)
    test_col = st.selectbox("Analiz Edilecek Test Değeri", df.columns)
    
    if st.button("RefineR Algoritmasını Başlat"):
        # Veri Temizliği
        df[test_col] = pd.to_numeric(df[test_col].astype(str).str.replace(',', '.'), errors='coerce')
        clean_data = df[df[test_col] > 0][test_col].dropna()
        
        if len(clean_data) > 50:
            with st.spinner("RefineR (Box-Cox) optimizasyonu yapılıyor..."):
                try:
                    low, high = run_refiner_analysis(clean_data)
                    
                    st.success(f"Hesaplanan Referans Aralığı: {low:.4f} - {high:.4f}")
                    
                    # Görselleştirme
                    fig = px.histogram(clean_data, nbins=100, title="Veri Dağılımı ve RefineR Modeli")
                    fig.add_vrect(x0=low, x1=high, fillcolor="rgba(0,255,0,0.15)", annotation_text="95% RI")
                    st.plotly_chart(fig)
                    
                except Exception as e:
                    st.error(f"İstatistiksel hata: {e}")
        else:
            st.warning("Seçilen filtrelerle yeterli veri (n > 50) bulunamadı.")
