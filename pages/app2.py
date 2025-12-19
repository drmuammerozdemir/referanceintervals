import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from rpy2.robjects.packages import importr
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri

# --- R PAKET KONTROLÜ VE KURULUMU ---
def install_r_packages():
    # R'ın 'utils' paketini yükle
    utils = importr('utils')
    utils.chooseCRANmirror(ind=1) # Bir ayna (mirror) seç
    
    # refineR yüklü mü kontrol et, değilse yükle
    packnames = ('refineR',)
    names_to_install = [x for x in packnames if not robjects.r.bool(robjects.r['require'](x)[0])]
    
    if names_to_install:
        st.info(f"R paketi kuruluyor: {names_to_install}. Bu işlem bir kez yapılır ve biraz vakit alabilir...")
        utils.install_packages(robjects.vectors.StrVector(names_to_install))

# Uygulama başladığında kurulumu tetikle
try:
    install_r_packages()
    refiner = importr('refineR')
except Exception as e:
    st.error(f"R paketleri yüklenirken hata oluştu: {e}")

# R-Python veri dönüşümünü aktif et
pandas2ri.activate()

# R kütüphanelerini yükle
try:
    refiner = importr('refineR')
    base = importr('base')
except:
    st.error("R 'refineR' paketi yüklü değil. Lütfen R ortamınızı kontrol edin.")

def run_refine_r(data_series):
    # Python serisini R vektörüne çevir
    r_vector = robjects.FloatVector(data_series.tolist())
    
    # RefineR ana fonksiyonunu çalıştır
    # model='complex' seçeneği Box-Cox dönüşümünü ve ileri optimizasyonu içerir
    result = robjects.r['findRI'](r_vector, model='complex')
    
    # Sonuçları Python sözlüğüne geri çek
    # Normal model sonuçlarını alıyoruz (2.5% ve 97.5%)
    estimates = dict(zip(result.names, list(result)))
    
    # RefineR model objesinden limitleri çekme
    # Not: RefineR çıktı yapısı versiyona göre değişebilir
    ri_low = result.rx2('Normal')[0]
    ri_high = result.rx2('Normal')[1]
    
    return ri_low, ri_high

st.title("🔬 RefineR: Advanced Reference Interval Analyzer")
st.markdown("Bu panel, R tabanlı **RefineR** algoritmasını kullanarak en hassas referans aralığı tahminini yapar.")

uploaded_file = st.file_uploader("Veri Seti (CSV/Excel)", type=['csv', 'xlsx'])

if uploaded_file:
    # Veri Okuma (Önceki kodlardaki temizlik adımları aynen geçerli)
    df = pd.read_excel(uploaded_file) if 'xlsx' in uploaded_file.name else pd.read_csv(uploaded_file)
    
    # ... (Sütun seçimi ve filtreleme kodları buraya gelecek) ...
    
    if st.button("RefineR Algoritmasını Çalıştır"):
        with st.spinner("RefineR (R-Environment) hesaplama yapıyor..."):
            try:
                # Sayısal ve pozitif veriyi hazırla
                clean_data = pd.to_numeric(df[test_col], errors='coerce').dropna()
                clean_data = clean_data[clean_data > 0]
                
                low, high = run_refine_r(clean_data)
                
                st.success(f"RefineR Sonucu: {low:.4f} - {high:.4f}")
                
                # Grafik
                fig = px.histogram(clean_data, nbins=100, title="RefineR Modellenmiş Dağılım")
                fig.add_vrect(x0=low, x1=high, fillcolor="blue", opacity=0.2, annotation_text="RefineR RI")
                st.plotly_chart(fig)
                
            except Exception as e:
                st.error(f"RefineR hatası: {e}")
