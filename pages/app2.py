import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

# rpy2 bileşenlerini dikkatli içe aktarın
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
from rpy2.robjects.conversion import localconverter

# --- R PAKET KURULUMU (SADELEŞTİRİLMİŞ) ---
def setup_r():
    try:
        # R içindeki temel paketleri yükle
        base = importr('base')
        utils = importr('utils')
        
        # refineR yüklü mü kontrol et
        is_installed = robjects.r('function(pkg) { pkg %in% rownames(installed.packages()) }')
        if not is_installed('refineR')[0]:
            st.info("İlk kurulum: refineR paketi yükleniyor (yaklaşık 1-2 dk sürebilir)...")
            utils.chooseCRANmirror(ind=1)
            utils.install_packages(robjects.vectors.StrVector(['refineR']))
        
        return importr('refineR')
    except Exception as e:
        st.error(f"R konfigürasyon hatası: {e}")
        return None

# --- HATAYI ÇÖZEN ANALİZ FONKSİYONU ---
def run_refine_r_safe(data_series):
    # Hata Çözümü: pandas2ri dönüşümünü burada manuel ve yerel olarak yapıyoruz
    # Bu sayede 'ContextVar' hatası engellenir
    
    # 1. Veriyi listeye çevirerek rpy2'nin karmaşık dönüşüm kurallarından kaçın
    data_list = data_series.tolist()
    r_data = robjects.FloatVector(data_list)
    
    # 2. findRI fonksiyonunu çağır (model='complex' sola çarpık veri için idealdir)
    # RefineR burada Box-Cox dönüşümü ile veriyi simetrikleştirir
    refineR = importr('refineR')
    result = refineR.findRI(r_data, model='complex')
    
    # 3. Sonuçları çek
    # Normal model sonuçları (2.5% ve 97.5%)
    ri_low = result.rx2('Normal')[0]
    ri_high = result.rx2('Normal')[1]
    
    return ri_low, ri_high

# --- ARAYÜZ ---
st.title("🔬 RefineR: Sola Çarpık Veri Analizi")

# R kurulumunu yap
refineR_pkg = setup_r()

uploaded_file = st.file_uploader("Veri Seti Yükleyin", type=['csv', 'xlsx'])

if uploaded_file and refineR_pkg:
    df = pd.read_excel(uploaded_file) if 'xlsx' in uploaded_file.name else pd.read_csv(uploaded_file)
    
    # Sütun Seçimi
    test_col = st.selectbox("Analiz Edilecek Sütun (Sayısal Değerler)", df.columns)
    
    if st.button("RefineR Analizini Başlat"):
        # Veri Temizliği (Virgül/Nokta ve Sayısal Kontrol)
        if df[test_col].dtype == object:
            df[test_col] = df[test_col].str.replace(',', '.', regex=False)
        
        clean_data = pd.to_numeric(df[test_col], errors='coerce').dropna()
        clean_data = clean_data[clean_data > 0]
        
        if len(clean_data) > 50:
            with st.spinner("RefineR algoritması Box-Cox optimizasyonu yapıyor..."):
                try:
                    low, high = run_refine_r_safe(clean_data)
                    
                    st.success(f"Hesaplanan Referans Aralığı: {low:.4f} - {high:.4f}")
                    
                    # Görselleştirme
                    fig = px.histogram(clean_data, nbins=100, title="Sola Çarpık Veri ve RefineR Modeli")
                    fig.add_vrect(x0=low, x1=high, fillcolor="rgba(255,0,0,0.1)", annotation_text="95% RI")
                    st.plotly_chart(fig)
                    
                except Exception as e:
                    st.error(f"İstatistiksel hata: {e}")
        else:
            st.error("Yetersiz veri. Filtreler sonrası en az 50 örnek gereklidir.")
