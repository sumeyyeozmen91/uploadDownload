import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# Sayfa ayarları
st.set_page_config(page_title="BiP & WhatsApp Performans Karşılaştırma Merkezi", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP (V5.1.23 & V5.2.6) vs WhatsApp İndirme Performansı Karşılaştırması")
st.markdown("""
    Bu panelde BiP ve WhatsApp uygulamalarının **Download_Duration (İndirme Süresi)** performansları 3'lü olarak analiz edilir:
    * **BiP (V5.1.23) vs BiP (V5.2.6):** Sürüm gelişim ve optimizasyon başarısı.
    * **BiP Sürümleri vs WhatsApp:** Rakip analizi ve şebeke bazlı en hızlı uygulama tespiti.
""")

def veri_isle(file_path):
    try:
        if not os.path.exists(file_path):
            return None

        # Excel dosyasını oku
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
        except:
            df = pd.read_excel(file_path)

        if df.empty:
            return None

        # Sütun isimlerinin başındaki ve sonundaki boşlukları temizle
        df.columns = [str(c).strip() for c in df.columns]

        # İlk sütunu 'Test Adı' olarak sabitle
        df.rename(columns={df.columns[0]: 'Test Adı'}, inplace=True)

        # --- DOWNLOAD_DURATION ODAKLI KONTROL ---
        # Büyük/küçük harf fark etmeksizin Download_Duration sütununu bul ve standartlaştır
        duration_col = None
        for col in df.columns:
            if col.lower() == 'download_duration':
                duration_col = col
                break
        
        if duration_col is not None:
            df.rename(columns={duration_col: 'Download_Duration'}, inplace=True)
        else:
            # Eğer tam isim eşleşmezse içinde duration geçen sütuna bak
            for col in df.columns:
                if 'duration' in col.lower():
                    df.rename(columns={col: 'Download_Duration'}, inplace=True)
                    duration_col = col
                    break
        
        # Eğer hiçbir şekilde bulunamazsa bu dosyayı geç
        if 'Download_Duration' not in df.columns:
            return None

        # --- GÜVENLİ SAYISAL DÖNÜŞTÜRME ---
        df['Download_Duration'] = df['Download_Duration'].apply(lambda x: ''.join(c for c in str(x) if c.isdigit() or c in ['.', ',']))
        df['Download_Duration'] = df['Download_Duration'].str.replace(',', '.')
        df['Download_Duration'] = pd.to_numeric(df['Download_Duration'], errors='coerce').astype(float)

        # Boş veya hatalı satırları temizle
        df = df.dropna(subset=['Download_Duration'])

        # Dosya adını al
        fname = os.path.basename(file_path)
        fname_lower = fname.lower()

        # --- DOSYA ADI FORMATI AYRIŞTIRMA (Büyük/Küçük Harf Korumalı) ---
        if "_" in fname:
            clean_name = fname.replace(".xlsx", "").replace(".csv", "")
            parts = clean_name.split('_')
            parts_lower = [p.lower() for p in parts]
            
            # WhatsApp Kontrolü: Dosya adı "Wa" veya "wa" ile başlıyorsa
            if parts_lower[0] == "wa":
                app_name = "WhatsApp"
                version = "Genel"
                net_raw = parts_lower[1]
                type_raw = parts_lower[2]
            # BiP Kontrolü: Dosya adı "5.1.23_Bip..." veya "5.2.6_Bip..." şeklindeyse
            elif "bip" in parts_lower:
                version = parts[0]   # "5.1.23" veya "5.2.6"
                app_name = "BiP"
                net_raw = parts_lower[2]   # "4.5g" veya "wifi"
                type_raw = parts_lower[3] 
            else:
                return None
                
            # Medya Kalitesi ve Türü Ayrıştırma
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

        # Yeni sütunları ekle
        df['Uygulama'] = app_name
        df['Versiyon'] = version
        df['Şebeke'] = network
        df['Grup'] = f"BiP (V{version})" if app_name == "BiP" else app_name
        df['Medya Kalitesi'] = medya_kalitesi
        df['Medya Türü'] = medya_turu

        return df[['Test Adı', 'Download_Duration', 'Uygulama', 'Versiyon', 'Şebeke', 'Grup', 'Medya Kalitesi', 'Medya Türü']]
    except Exception as e:
        return None

# --- GELİŞMİŞ 3'LÜ KARŞILAŞTIRMA MOTORU ---
def surum_gelisim_yorumu(df, metrik_kolonu):
    try:
        if df.empty:
            return "Yorumlanacak veri bulunamadı."

        yorumlar = []
        stats = df.groupby(['Şebeke', 'Grup'])[metrik_kolonu].mean().unstack(level=-1)
        
        yorumlar.append("### 📊 3'lü Performans Karşılaştırma Analiz Raporu (Download_Duration)")
        
        for seb in sorted(df['Şebeke'].unique()):
            if seb in stats.index:
                yorumlar.append(f"\n**📍 {seb} Şebekesi Altındaki Durum:**")
                row = stats.loc[seb]
                
                bip51 = row.get('BiP (V5.1.23)', None)
                bip52 = row.get('BiP (V5.2.6)', None)
                wa = row.get('WhatsApp', None)
                
                # 1. BiP Sürüm Gelişimi Kıyası
                if pd.notna(bip51) and pd.notna(bip52):
                    if bip52 < bip51:
                        degisim = ((bip51 - bip52) / bip51) * 100
                        yorumlar.append(f"- **BiP Gelişimi:** Yeni V5.2.6 sürümü, eski V5.1.23 sürümüne göre **%{degisim:.1f} daha hızlı indiriyor.** ✅")
                    else:
                        degisim = ((bip52 - bip51) / bip51) * 100
                        yorumlar.append(f"- **BiP Gelişimi:** Yeni V5.2.6 sürümünde eski sürüme göre **%{degisim:.1f} oran
