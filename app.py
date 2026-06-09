import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Sayfa ayarları
st.set_page_config(page_title="Hız Testi Analiz Merkezi", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP (V5.1 & V5.2) vs WhatsApp Performans Kıyaslama")
st.markdown("""
    Bu panelde yüklenen test dosyaları dinamik olarak analiz edilir. 
    Grafiklerin altında seçilen her dosya formatına özel **otomatik performans yorumları** ve **BiP sürüm gelişim analizleri** yer almaktadır.
""")

# --- YAPILANDIRMA ---
# Kullanıcının belirttiği güncel dosya listesi eşleştirmesi
DOSYA_HARITASI = [
    {"path": "Bip_3G.xlsx - Sıralı Veriler.csv", "app": "BiP", "ver": "5.1", "net": "3G"},
    {"path": "Bip_4.5G.xlsx - Test Verileri.csv", "app": "BiP", "ver": "5.1", "net": "4G"},
    {"path": "Bip_Wifi.xlsx - Test Verileri.csv", "app": "BiP", "ver": "5.1", "net": "Wi-Fi"},
    {"path": "Bip_3G_new.xlsx - Sıralı Veriler.csv", "app": "BiP", "ver": "5.2", "net": "3G"},
    {"path": "Bip_4.5G_new.xlsx - Test Verileri.csv", "app": "BiP", "ver": "5.2", "net": "4G"},
    {"path": "Bip_Wifi_new.xlsx - Test Verileri.csv", "app": "BiP", "ver": "5.2", "net": "Wi-Fi"},
    {"path": "Wa_3G.xlsx - Sıralı Veriler.csv", "app": "WhatsApp", "ver": "Genel", "net": "3G"},
    {"path": "Wa_4.5G.xlsx - Sıralı Test Verileri.csv", "app": "WhatsApp", "ver": "Genel", "net": "4G"},
    {"path": "Wa_Wifi.xlsx - Veri Listesi.csv", "app": "WhatsApp", "ver": "Genel", "net": "Wi-Fi"}
]

def veri_isle(cfg):
    try:
        if not os.path.exists(cfg["path"]):
            return None
            
        df = pd.read_csv(cfg["path"])
        
        # Sütun isimlerini temizle (Örn: "Yükleme Süresi (ms)" -> "Yükleme Süresi")
        df.columns = [str(c).split(' (')[0].strip() for c in df.columns]
        
        # Standart isimlendirme kontrolü
        rename_dict = {}
        for col in df.columns:
            if "İndirme" in col: rename_dict[col] = "İndirme Süresi"
            if "Yükleme" in col: rename_dict[col] = "Yükleme Süresi"
            if "Test Adı" in col: rename_dict[col] = "Test Adı"
        df = df.rename(columns=rename_dict)
        
        # Veri tipi dönüşümleri
        df["İndirme Süresi"] = pd.to_numeric(df["İndirme Süresi"], errors='coerce')
        df["Yükleme Süresi"] = pd.to_numeric(df["Yükleme Süresi"], errors='coerce')
        
        # Meta veriler
        df['Uygulama'] = cfg["app"]
        df['Versiyon'] = cfg["ver"]
        df['Şebeke'] = cfg["net"]
        
        if cfg["app"] == "BiP":
            df['Grup'] = f"BiP (V{cfg['ver']})"
        else:
            df['Grup'] = "WhatsApp"
            
        # Dosya uzantısı ve boyutu çıkarma
        df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'DİĞER')
        df['Boyut'] = df['Test Adı'].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x))
        
        return df[['Test Adı', 'Uzantı', 'Boyut', 'Yükleme Süresi', 'İndirme Süresi', 'Uygulama', 'Versiyon', 'Şebeke', 'Grup']]
    except Exception as e:
        st.error(f"⚠️ {cfg['path']} işlenirken hata oluştu: {e}")
        return None

# --- VERİ YÜKLEME ---
all_data = []
for cfg in DOSYA_HARITASI:
    res = veri_isle(cfg)
    if res is not None:
        all_data.append(res)

if all_data:
    full_df = pd.concat(all_data, ignore_index=True).dropna()
    
    # --- FİLTRELER (SIDEBAR) ---
    st
