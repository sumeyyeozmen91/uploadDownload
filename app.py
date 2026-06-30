import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# Sayfa ayarları
st.set_page_config(page_title="BiP & WhatsApp Üçlü Performans Karşılaştırması", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP (V5.1.23 & V5.2.6) vs WhatsApp İndirme Performansı")
st.markdown("""
    Bu panelde, her koşumda **farklı fotoğraflar** kullanılarak yapılan stres testlerinin sonuçları analiz edilir:
    * **Üçlü Kıyaslama:** BiP (V5.1.23), BiP (V5.2.6) ve WhatsApp indirme süreleri (Download Duration).
    * **Şebeke & Kalite:** 4.5G ve Wi-Fi şebekeleri üzerinde HD / SD performans kırılımları.
""")

def veri_isle(file_path):
    try:
        if not os.path.exists(file_path):
            return None

        df = pd.read_excel(file_path)

        if df.empty:
            return None

        # --- SÜTUN İSİMLERİNİ EŞLEŞTİRME VE TEMİZLEME ---
        df.rename(columns={df.columns[0]: 'Test Adı'}, inplace=True)
        df.columns = [str(c).strip() for c in df.columns]

        # Sadece Download_Duration sütununu hedef alıyoruz
        sutun_haritasi = {
            'Download_Duration': 'İndirme Süresi'
        }
        df.rename(columns=sutun_haritasi, inplace=True)

        gerekli_sutunlar = ['Test Adı', 'İndirme Süresi']
        for col in gerekli_sutunlar:
            if col not in df.columns:
                return None

        # --- GÜVENLİ SAYISAL DÖNÜŞTÜRME ---
        df['İndirme Süresi'] = df['İndirme Süresi'].apply(lambda x: ''.join(c for c in str(x) if c.isdigit() or c in ['.', ',']))
        df['İndirme Süresi'] = df['İndirme Süresi'].str.replace(',', '.')
        df['İndirme Süresi'] = pd.to_numeric(df['İndirme Süresi'], errors='coerce').astype(float)

        # İndirme verisi olmayan satırları eliyoruz
        df = df.dropna(subset=['İndirme Süresi'])

        fname = os.path.basename(file_path).lower()

        # --- DOSYA ADI FORMATI AYRIŞTIRMA ---
        if "_" in fname:
            clean_name = fname.replace(".xlsx", "").replace(".csv", "")
            parts = clean_name.split('_')
            
            # WhatsApp formatı kontrolü (Örn: wa_4.5g_hdphoto)
            if parts[0] == "wa":
                app_name = "WhatsApp"
                version = "Genel"
                net_raw = parts[1]
                type_raw = parts[2]
            # BiP formatı kontrolü (Örn: 5.1.23_bip_4.5g_hdphoto)
            elif "bip" in parts:
                version = parts[0]   # "5.1.23" or "5.2.6"
                app_name = "BiP"
                net_raw = parts[2]   # "4.5g" or "wifi"
                type_raw = parts[3] 
            else:
                return None
                
            if "hd" in type_raw:
                medya_kalitesi = "HD"
                medya_turu = type_raw.replace("hd", "").capitalize()
            elif "sd" in type_raw:
                medya_kalitesi = "SD"
                medya_turu = type_raw.replace("sd", "").capitalize()
            else:
                medya_kalitesi = "Genel"
                medya_turu = type_raw.capitalize()
        else:
            return None

        # Şebeke ismini standartlaştır
        if "3g" in net_raw: network = "3G"
        elif "4g" in net_raw or "4.5g" in net_raw: network = "4.5G
