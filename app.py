import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# Sayfa ayarları
st.set_page_config(page_title="BiP & WhatsApp İndirme Performansı Karşılaştırması", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP (V5.1.23 & V5.2.6) vs WhatsApp İndirme Performansı Karşılaştırması")
st.markdown("""
    Bu panelde BiP ve WhatsApp uygulamalarının **Download_Duration (İndirme Süresi)** performansları analiz edilir:
    * **BiP (V5.1.23) vs BiP (V5.2.6):** İki farklı sürüm arasındaki indirme performans farkları ve iyileşme oranları.
    * **BiP (V5.2.6) vs WhatsApp:** Güncel BiP sürümü ile rakip WhatsApp arasındaki hız kıyaslaması.
    
    ⚠️ **Önemli Not:** Ölçülen değerler milisaniye (ms) cinsinden **süre** belirttiği için, **küçük olan değer daha hızlı** anlamına gelmektedir.
""")

def veri_isle(file_path):
    try:
        if not os.path.exists(file_path):
            return None

        try:
            df = pd.read_excel(file_path, engine='openpyxl')
        except:
            df = pd.read_excel(file_path)

        if df.empty:
            return None

        # --- SÜTUN İSİMLERİNİ EŞLEŞTİRME VE TEMİZLEME ---
        df.rename(columns={df.columns[0]: 'Test Adı'}, inplace=True)
        df.columns = [str(c).strip() for c in df.columns]

        # Download_Duration sütununu dinamik olarak bulup standartlaştırıyoruz
        duration_col = None
        for col in df.columns:
            if col.lower() == 'download_duration':
                duration_col = col
                break
        
        if duration_col is not None:
            df.rename(columns={duration_col: 'İndirme Süresi'}, inplace=True)
        else:
            for col in df.columns:
                if 'duration' in col.lower():
                    df.rename(columns={col: 'İndirme Süresi'}, inplace=True)
                    duration_col = col
                    break
        
        if 'İndirme Süresi' not in df.columns:
            return None

        # --- GÜVENLİ SAYISAL DÖNÜŞTÜRME ---
        df['İndirme Süresi'] = df['İndirme Süresi'].apply(lambda x: ''.join(c for c in str(x) if c.isdigit() or c in ['.', ',']))
        df['İndirme Süresi'] = df['İndirme Süresi'].str.replace(',', '.')
        df['İndirme Süresi'] = pd.to_numeric(df['İndirme Süresi'], errors='coerce').astype(float)

        # İndirme verisi olmayan satırları eliyoruz
        df = df.dropna(subset=['İndirme Süresi'])

        fname = os.path.basename(file_path).lower()

        # --- DOSYA ADI FORMATI AYRIŞTIRMA ---
        clean_name = fname.replace(".xlsx", "").replace(".csv", "")
        parts = clean_name.split('_')
        
        if len(parts) >= 3 and parts[0] == "wa":
            app_name = "WhatsApp"
            version = "Genel"
            net_raw = parts[1]
            type_raw = parts[2]
        elif len(parts) >= 4 and "bip" in parts:
            version = parts[0]   # "5.1.23" veya "5.2.6"
            app_name = "BiP"
            net_raw = parts[2]   # "4.5g" veya "wifi"
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

        # Şebeke ismini standartlaştır
        if "3g" in net_raw: network = "3G"
        elif "4g" in net_raw or "4.5g" in net_raw: network = "4.5G"
        elif "wifi" in net_raw: network = "Wi-Fi"
        else: network = net_raw.upper()

        # DataFrame sütunlarını doldur
        df['Uygulama'] = app_name
        df['Versiyon'] = version
        df['Şebeke'] = network
        df['Grup'] = f"BiP (V{version})" if app_name == "BiP" else app_name
        df['Medya Kalitesi'] = medya_kalitesi
        df['Medya Türü'] = medya_turu

        df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'DİĞER')
        df['Boyut'] = df['Test Adı'].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x))

        return df[['Test Adı', 'Uzantı', 'Boyut', 'İndirme Süresi', 'Uygulama', 'Versiyon', 'Şebeke', 'Grup', 'Medya Kalitesi', 'Medya Türü']]
    except Exception as e:
        return None

# --- ÇİFT KADEMELİ DETAYLI YORUM MOTORU ---
def surum_gelisim_yorumu(df, metrik_kolonu):
    if df
