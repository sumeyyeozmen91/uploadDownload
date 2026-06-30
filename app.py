import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# Sayfa ayarları
st.set_page_config(page_title="BiP & WhatsApp Performans Karşılaştırma Merkezi", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP & WhatsApp İndirme Performansı Karşılaştırması")
st.markdown("""
    Bu panelde BiP ve WhatsApp uygulamalarının indirme performansları ve versiyon gelişimleri analiz edilir:
    * **Uygulamalar Arası Kıyaslama:** BiP vs WhatsApp indirme süreleri.
    * **Şebeke & Medya Kırılımı:** 4.5G vs Wi-Fi üzerinde HD ve SD fotoğraf indirme performans farkları.
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
                st.error(f"⚠️ {os.path.basename(file_path)} içinde gerekli sütun yapısı çözülemedi! Mevcut Sütunlar: {list(df.columns)}")
                return None

        # --- GÜVENLİ SAYISAL DÖNÜŞTÜRME ---
        df['İndirme Süresi'] = df['İndirme Süresi'].apply(lambda x: ''.join(c for c in str(x) if c.isdigit() or c in ['.', ',']))
        df['İndirme Süresi'] = df['İndirme Süresi'].str.replace(',', '.')
        df['İndirme Süresi'] = pd.to_numeric(df['İndirme Süresi'], errors='coerce').astype(float)

        # İndirme verisi olmayan satırları eliyoruz
        df = df.dropna(subset=['İndirme Süresi'])

        fname = os.path.basename(file_path).lower()

        # --- DOSYA ADI FORMATI AYRIŞTIRMA (BiP & WhatsApp) ---
        if "_" in fname:
            clean_name = fname.replace(".xlsx", "").replace(".csv", "")
            parts = clean_name.split('_')
            
            # WhatsApp Dosya Formatı Kontrolü (Örn: wa_4.5g_hdphoto)
            if parts[0] == "wa":
                app_name = "WhatsApp"
                version = "Genel"  # WhatsApp için spesifik bir sürüm yoksa genel etiket
                net_raw = parts[1] # "4.5g" or "wifi"
                type_raw = parts[2] # "hdphoto" or "sdphoto"
            # BiP Dosya Formatı Kontrolü (Örn: 5.2.6_bip_4.5g_hdphoto)
            elif "bip" in parts:
                version = parts[0]   # "5.1.23" or "5.2.6"
                app_name = "BiP"
                net_raw = parts[2]   # "4.5g" or "wifi"
                type_raw = parts[3]  # "hdphoto" or "sdphoto"
            else:
                return None
            
            # Medya kalitesi ve türü ayrıştırma
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
        elif "4g" in net_raw or "4.5g" in net_raw: network = "4.5G"
        elif "wifi" in net_raw: network = "Wi-Fi"
        else: network = net_raw.upper()

        # DataFrame sütunlarını doldur
        df['Uygulama'] = app_name
        df['Versiyon'] = version
        df['Şebeke'] = network
        df['Grup'] = f"{app_name} (V{version})" if app_name == "BiP" else app_name
        df['Medya Kalitesi'] = medya_kalitesi
        df['Medya Türü'] = medya_turu

        df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'DİĞER')
        df['Boyut'] = df['Test Adı'].apply(lambda x: str(x).split('.')[0] if '.' in str(x
