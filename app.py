import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# Sayfa ayarları
st.set_page_config(page_title="BiP vs WhatsApp Karşılaştırma Merkezi", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP (V5.1.23 & V5.2.6) vs WhatsApp İndirme Performansı Karşılaştırması")
st.markdown("""
    Bu panelde BiP'in iki farklı sürümü ile WhatsApp uygulamasının indirme performansları aynı anda analiz edilir:
    * **Üçlü Kıyaslama:** BiP (V5.1.23) vs BiP (V5.2.6) vs WhatsApp
    * **Şebeke & Medya Kırılımı:** 4.5G ve Wi-Fi ağlarında, her koşumda değişen HD/SD fotoğraf indirme süreleri.
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
            
            # WhatsApp formatı (Örn: wa_4.5g_hdphoto)
            if parts[0] == "wa":
                app_name = "WhatsApp"
                version = "Genel"
                net_raw = parts[1]
                type_raw = parts[2]
            # BiP formatı (Örn: 5.1.23_bip_4.5g_hdphoto)
            elif "bip" in parts:
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
        
        # Etiketleme Mantığı
        if app_name == "WhatsApp":
            df['Grup'] = "WhatsApp"
        else:
            df['Grup'] = f"BiP (V{version})"
            
        df['Medya Kalitesi'] = medya_kalitesi
        df['Medya Türü'] = medya_turu

        df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'DİĞER')
        df['Boyut'] = df['Test Adı'].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x))

        return df[['Test Adı', 'Uzantı', 'Boyut', 'İndirme Süresi', 'Uygulama', 'Versiyon', 'Şebeke', 'Grup', 'Medya Kalitesi', 'Medya Türü']]
    except Exception as e:
        return None

# --- DİNAMİK ÜÇLÜ PERFORMANS YORUM MOTORU ---
def uclu_performans_yorumu(df, metrik_kolonu):
    if df.empty:
        return "Yorumlanacak veri bulunamadı."

    yorumlar = []
    mevcut_gruplar = list(df['Grup'].dropna().unique())
    
    yorumlar.append("### 📊 Üçlü Performans Karşılaştırma Analizi")
    
    sebekeler = sorted(list(df['Şebeke'].unique()))
    for seb in sebekeler:
        seb_df = df[df['Şebeke'] == seb]
        yorumlar.append(f"\n**📍 {seb} Altyapısı Altındaki Durum:**")
        
        # Her grup (BiP V5.1.23, BiP V5.2.6, WhatsApp) için ortalamaları hesapla
        ortalamalar = []
        for grp in mevcut_gruplar:
            grp_ort = seb_df[seb_df['Grup'] == grp][metrik_kolonu].mean()
            if pd.notna(grp_ort):
                ortalamalar.append((grp, grp_ort))
        
        # En hızlıdan (en düşük ms) en yavaşa sıralama
        ortalamalar.sort(key=lambda x: x[1])
        
        for i, (grp, ort) in enumerate(ortalamalar):
            sim
