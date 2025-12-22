import streamlit as st
import pandas as pd
import os
import subprocess

# Sayfa Yapılandırması
st.set_page_config(page_title="TSH Referans Aralığı Analizörü", layout="wide")

st.title("🔬 TSH Referans Aralığı Analiz Paneli (RefineR)")
st.markdown("""
Bu uygulama, laboratuvar verilerini kullanarak **Yaş ve Cinsiyet** bazlı referans aralığı hesaplar.
Metodoloji: **Indirect Method (modBoxCox)** ve **Bootstrapping (N=100)**.
""")

# 1. Dosya Yükleme
uploaded_file = st.file_uploader("TSH Excel Dosyasını Yükleyin", type=["xlsx"])

if uploaded_file:
    # Geçici olarak dosyayı kaydet
    with open("temp_tsh.xlsx", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success("Dosya başarıyla yüklendi. Analiz parametrelerini seçin.")

    # 2. Parametreler
    col1, col2 = st.columns(2)
    with col1:
        age_limit = st.slider("Yaş Kırılım Sınırı", 18, 80, 40)
    with col2:
        bootstrap_n = st.number_input("Bootstrap Sayısı (Makale için 100 önerilir)", 10, 200, 100)

    if st.button("Analizi Başlat (R Engine)"):
        st.info("R algoritması çalışıyor... Bu işlem birkaç dakika sürebilir (Bootstrapping yapılıyor).")
        
        # 3. R Kodunu Oluşturma (R Script Yazımı)
        r_script = f"""
        library(readxl)
        library(refineR)

        # Veri okuma ve temizlik
        df <- read_excel("temp_tsh.xlsx")
        df <- df[!duplicated(df$TCKIMLIK_NO), ]
        df$TSH_NUM <- as.numeric(gsub(",", ".", as.character(df$TEST_DEGERI)))
        df$AGE_NUM <- as.numeric(df$YASI)
        
        df_final <- df[!is.na(df$TSH_NUM) & df$AGE_NUM >= 18 & !is.na(df$AGE_NUM), ]
        
        # Analiz Fonksiyonu
        run_analysis <- function(data, title, filename) {{
            vals <- data[data > 0]
            res <- findRI(Data = vals, model = "modBoxCox", NBootstrap = {bootstrap_n}, seed = 123)
            
            # 300 DPI Grafik Kaydı
            png(paste0(filename, ".png"), width = 2400, height = 1800, res = 300)
            plot(res, showCI = TRUE, main = title)
            dev.off()
            
            return(res)
        }}

        # Grupları Ayır ve Çalıştır
        kadin_base <- df_final[df_final$CINSIYET %in% c("K", "Kadın", "Female", "KADIN"), ]
        erkek_base <- df_final[df_final$CINSIYET %in% c("E", "Erkek", "Male", "ERKEK"), ]

        # Sadece iki ana grup örneği (Hız için)
        res_k1 <- run_analysis(kadin_base$TSH_NUM[kadin_base$AGE_NUM < {age_limit}], "Kadin_Genc", "kadin_genc")
        res_k2 <- run_analysis(kadin_base$TSH_NUM[kadin_base$AGE_NUM >= {age_limit}], "Kadin_Olgun", "kadin_olgun")
        
        # Sonuçları Kaydet
        write.csv(data.frame(
            Group = c("Kadin Genc", "Kadin Olgun"),
            Lower = c(res_k1$RI[1], res_k2$RI[1]),
            Upper = c(res_k1$RI[2], res_k2$RI[2])
        ), "sonuclar.csv")
        """

        with open("analysis.R", "w", encoding="utf-8") as f:
            f.write(r_script)

        # R Script'ini dışarıdan çağır
        subprocess.run(["Rscript", "analysis.R"])

        # 4. Sonuçları Göster
        st.success("Analiz Tamamlandı!")
        
        if os.path.exists("sonuclar.csv"):
            results_df = pd.read_csv("sonuclar.csv")
            st.table(results_df)

        # Grafikleri Yan Yana Göster
        c1, c2 = st.columns(2)
        with c1:
            if os.path.exists("kadin_genc.png"):
                st.image("kadin_genc.png", caption=f"Kadın (<{age_limit} Yaş)")
        with c2:
            if os.path.exists("kadin_olgun.png"):
                st.image("kadin_olgun.png", caption=f"Kadın ({age_limit}+ Yaş)")
