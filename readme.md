# LabRef Analyzer v2.0

Laboratuvar verilerinden (Big Data) otomatik referans aralığı belirleme aracı.

## 📁 Desteklenen Formatlar
- **Excel:** `.xls`, `.xlsx`
- **SPSS:** `.sav`
- **Metin:** `.csv`

## 🛠 Kullanılan Teknolojiler
- **Streamlit:** Web arayüzü
- **Pandas & Pyreadstat:** Çoklu format veri okuma
- **Scipy:** Hoffmann istatistiksel modelleme
- **Plotly:** İnteraktif grafikler

## 🚀 Nasıl Çalışır?
Uygulama, ham laboratuvar verilerini yüklediğinizde önce "Test İsmi" sütununa göre filtreleme yapar. Ardından seçilen testin değerlerini Hoffmann yöntemiyle (ve opsiyonel logaritmik dönüşümle) analiz ederek sağlıklı popülasyonu izole eder ve %95 güven aralığını hesaplar.
