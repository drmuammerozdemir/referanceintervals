import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from rpy2.robjects import r, pandas2ri, FloatVector
from rpy2.robjects.packages import importr
import rpy2.robjects as robjects
from rpy2.robjects.conversion import localconverter

# --- R PAKET KONTROLÜ VE KURULUMU ---
def install_r_packages():
    utils = importr('utils')
    utils.chooseCRANmirror(ind=1)
    packnames = ('refineR',)
    # rpy2'nin güncel sürümlerinde r.require kullanımı
    is_installed = robjects.r('function(pkg) { require(pkg, quietly=TRUE) }')
    
    if not is_installed('refineR')[0]:
        st.info("refineR paketi kuruluyor, lütfen bekleyin...")
        utils.install_packages(robjects.vectors.StrVector(packnames))

# Sayfa başında kurulumu dene
try:
    install_r_packages()
    refiner = importr('refineR')
except Exception as e:
    st.error(f"R ortamı hazırlanırken hata: {e}")

# --- ANALİZ FONKSİYONU ---
def run_refine_r(data_series):
    # Yeni yöntem: localconverter kullanarak güvenli dönüşüm
    with localconverter(robjects.default_converter + pandas2ri.py2rpy_metric):
        r_data = robjects.conversion.py2rpy(data_series)
        
    # RefineR findRI fonksiyonunu çağır
    # model='complex' sola çarpık veriler için Box-Cox optimizasyonu yapar
    result = robjects.r['findRI'](r_data, model='complex')
    
    # Sonuçları güvenli bir şekilde çekme
    # refineR sonuç objesi bir listedir, 'Normal' anahtarı RI limitlerini tutar
    ri_results = result.rx2('Normal')
    return ri_results[0], ri_results[1]

# --- STREAMLIT ARAYÜZÜ ---
st.title("🔬 RefineR: İleri Seviye Referans Aralığı Analizi")

uploaded_file = st.file_uploader("Veri Seti (CSV/Excel)", type=['csv', 'xlsx'])

if uploaded_file:
    # Veri okuma ve sütun seçimi (Önceki bölümlerdeki temizlik adımları)
    df = pd.read_excel(uploaded_file) if 'xlsx' in uploaded_file.name else pd.read_csv(uploaded_file)
    test_col = st.selectbox("Test Değeri Sütunu", df.columns)
    
    if st.button("RefineR ile Analiz Et"):
        clean_data = pd.to_numeric(df[test_col], errors='coerce').dropna()
        clean_data = clean_data[clean_data > 0]
        
        if len(clean_data) > 40:
            try:
                low, high = run_refine_r(clean_data)
                st.success(f"RefineR Güven Aralığı (%95): {low:.4f} - {high:.4f}")
                
                # Sola çarpık veriyi görselleştirme
                fig = px.histogram(clean_data, nbins=100, title="Veri Dağılımı ve RefineR Modeli")
                fig.add_vrect(x0=low, x1=high, fillcolor="rgba(0,0,255,0.2)", annotation_text="RefineR RI")
                st.plotly_chart(fig)
                
            except Exception as e:
                st.error(f"Analiz sırasında hata: {e}")
        else:
            st.warning("Analiz için en az 40 geçerli veri noktası gereklidir.")
