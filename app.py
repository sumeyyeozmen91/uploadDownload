import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob
import re

# Sayfa ayarları
st.set_page_config(page_title="BiP (V5.6.19) & WhatsApp Performans Karşılaştırması", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP (V5.6.19) vs WhatsApp İndirme & Yükleme Performansı Analiz Paneli")
st.markdown("""
    Bu panelde **BiP (Sürüm: V5.6.19)** ve **WhatsApp** uygulamalarının LTE ve Wifi şebekeleri üzerindeki 
    Fotoğraf ve 2dk Video indirme/yükleme performansları, ortalama süreleri ve dosya boyutları ritmik koşum sırasına göre analiz edilir.
""")

# --- CİHAZ VE NUMARA BİLGİLERİ (ANA SAYFA) ---
col_up, col_down = st.columns(2)
with col_up:
    st.info("📤 **Yükleme (Upload) Yapan Cihaz:**\n- **Numara:** `+905316892026` \n- **Model:** Galaxy S21 FE 5G")
with col_down:
    st.success("📥 **İndirme (Download) Yapan Cihaz:**\n- **Numara:** `+905360301821` \n- **Model:** Galaxy A51")

st.markdown("---")

# İzin verilen tam dosya isimleri (Büyük/küçük harf duyarsız kontrol edilir)
ALLOWED_FILES = {
    "sd_2dkvideo_download_lte",
    "sd_2dkvideo_download_wifi",
    "sd_2dkvideo_upload_lte",
    "sd_2dkvideo_upload_wifi",
    "sd_2dkvideo_wa_download_lte",
    "sd_2dkvideo_wa_download_wifi",
    "sd_2dkvideo_wa_upload_lte",
    "sd_2dkvideo_wa_upload_wifi",
    "sd_photo_download_lte",
    "sd_photo_download_wifi",
    "sd_photo_upload_lte",
    "sd_photo_upload_wifi",
    "sd_photo_wa_download_lte",
    "sd_photo_wa_download_wifi",
    "sd_photo_wa_upload_lte",
    "sd_photo_wa_upload_wifi"
}

def veri_isle(file_path):
    try:
        if not os.path.exists(file_path):
            return None

        fname = os.path.basename(file_path)
        base_name = fname.split('.')[0].lower().strip()

        # Sadece izin verilen 16 dosyayı filtrele
        if base_name not in ALLOWED_FILES:
            return None

        # Dosya okuma (XLSX veya CSV)
        if file_path.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        elif file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            return None

        if df.empty:
            return None

        # --- SÜTUN İSİMLERİNİ TEMİZLEME VE DÜZENLEME ---
        df.rename(columns={df.columns[0]: 'Test Adı'}, inplace=True)
        df.columns = [str(c).strip() for c in df.columns]

        # 16 Özel Dosya Mimarisine Göre Metadata Belirleme
        is_wa = "_wa_" in base_name
        is_video = "2dkvideo" in base_name
        is
