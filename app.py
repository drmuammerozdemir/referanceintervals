import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import io

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="LabAnalyzer Pro", layout="wide")

# --- HOFFMANN ALGORİTMASI ---
def calculate_hoffmann(data, use_log=True):
    # Veri temizliği: Sadece pozitif ve sayısal değerler
    data = data[data > 0]
    working_data = np.log(data) if use_log else data
    sorted_data = np.sort(working_data)
    n = len(sorted_data)
    
    # Olasılık değerleri (Hazen)
    p = (np.arange(1, n + 1) - 0.5) / n
    z = stats.norm.ppf(p)
    
    # Lineer regresyon (Merkez %40-60 dilimi odaklı)
    mask = (p > 0.20) & (p < 0.80)
    if len(z[mask]) < 5: return None # Yetersiz veri kontrolü
    
    slope, intercept, r_val, p_val, std_err = stats.linregress(z[mask], sorted_data[mask])
    
    low_z = intercept + (-1.96 * slope)
    high_z = intercept + (1.96 * slope)
    
    if use_log:
        return np.exp(low_z), np.exp(high_z), r_val**2
    return low_z, high_z, r_val**2

# --- ARAYÜZ ---
st.title("🧪 Laboratuvar Referans Aralığı Analizörü")
st.markdown("CSV, Excel (.xls, .xlsx) ve SPSS (.sav) dosyalarını destekler.")

# 1. DOSYA YÜKLEME SİSTEMİ
uploaded_file = st.file_uploader("Dosyanızı buraya bırakın", type=['csv', 'xlsx', 'xls', 'sav'])

if uploaded_file:
    file_extension = uploaded_file.name.split('.')[-1]
    
    try:
        if file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
        elif file_extension in ['xls', 'xlsx']:
            df = pd.read_excel(uploaded_file)
        elif file_extension == 'sav':
            import pyreadstat
            # Geçici dosyaya yazıp okuma (Streamlit/Pyreadstat uyumu için)
            with open("temp_file.sav", "wb") as f:
                f.write(uploaded_file.getbuffer())
            df, meta = pyreadstat.read_sav("temp_file.sav")
        
        st.success(f"Dosya başarıyla yüklendi: {len(df)} satır bulundu.")
        
        # 2. SÜTUN SEÇİMLERİ
        col1, col2, col3 = st.columns(3)
        with col1:
            test_col = st.selectbox("Test Sonucu (Sayısal Değer)", df.columns)
        with col2:
            name_col = st.selectbox("Tetkik İsmi Sütunu", df.columns)
        with col3:
            selected_test = st.selectbox("Analiz Edilecek Test", df[name_col].unique())

        # 3. VERİ ÖN İŞLEME
        analysis_df = df[df[name_col] == selected_test].copy()
        analysis_df[test_col] = pd.to_numeric(analysis_df[test_col], errors='coerce')
        clean_values = analysis_df[test_col].dropna().values

        # 4. HESAPLAMA VE GÖRSELLEŞTİRME
        if len(clean_values) > 50:
            log_choice = st.toggle("Log-Normal Dönüşümü Uygula (Hormonlar için önerilir)", value=True)
            
            result = calculate_hoffmann(clean_values, use_log=log_choice)
            
            if result:
                low, high, r2 = result
                
                # Özet Kartları
                st.divider()
                m1, m2, m3 = st.columns(3)
                m1.metric("Örneklem Sayısı", len(clean_values))
                m2.metric("Yeni Alt Limit (2.5%)", f"{low:.3f}")
                m3.metric("Yeni Üst Limit (97.5%)", f"{high:.3f}")
                
                # Grafik: Dağılım ve Referans Alanı
                fig = px.histogram(clean_values, nbins=100, title=f"{selected_test} Popülasyon Dağılımı",
                                   color_discrete_sequence=['#3498db'])
                fig.add_vrect(x0=low, x1=high, fillcolor="rgba(46, 204, 113, 0.3)", 
                             line_width=0, annotation_text="Hesaplanan Normal Aralığı")
                st.plotly_chart(fig, use_container_width=True)
                
                # Hoffmann Lineerlik Kontrolü
                st.subheader("Model Doğruluğu (Hoffmann Plot)")
                st.write(f"R-Kare Değeri: **{r2:.4f}** (1.0'a ne kadar yakınsa o kadar güvenilirdir)")
            else:
                st.warning("Veri seti Hoffmann analizi için uygun doğrusal yapıda değil.")
        else:
            st.error("Seçilen test için 50'den fazla geçerli sonuç bulunamadı.")
            
    except Exception as e:
        st.error(f"Dosya okunurken bir hata oluştu: {e}")

# --- FOOTER ---
st.divider()
st.caption("Bu uygulama 'Indirect Method' kullanarak referans aralığı tahmini yapar. Klinik kararlar için uzman onayı gereklidir.")
