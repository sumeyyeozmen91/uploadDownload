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
    Bu panelde BiP ve WhatsApp uygulamalarının indirme performansları 3'lü olarak analiz edilir:
    * **BiP (V5.1.23) vs BiP (V5.2.6):** Sürüm optimizasyon başarısı.
    * **BiP Sürümleri vs WhatsApp:** Rakip analizi ve şebeke bazlı en hızlı uygulama tespiti.
""")

def veri_isle(file_path):
    try:
        if not os.path.exists(file_path):
            return None

        # Excel okuma motorunu açıkça belirterek olası kütüphane kilitlerini kırıyoruz
        df = pd.read_excel(file_path, engine='openpyxl')

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
                st.warning(f"⚠️ {os.path.basename(file_path)} içinde '{col}' sütunu bulunamadı. Sütunlar: {list(df.columns)}")
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
        st.error(f"💥 {os.path.basename(file_path)} okunurken kritik hata: {e}")
        return None

# --- GELİŞMİŞ 3'LÜ KARŞILAŞTIRMA MOTORU ---
def surum_gelisim_yorumu(df, metrik_kolonu):
    if df.empty:
        return "Yorumlanacak veri bulunamadı."

    yorumlar = []
    stats = df.groupby(['Şebeke', 'Grup'])[metrik_kolonu].mean().unstack(level=-1)
    yorumlar.append("### 📊 3'lü Performans Karşılaştırma Analiz Raporu")
    
    for seb in sorted(df['Şebeke'].unique()):
        if seb in stats.index:
            yorumlar.append(f"\n**📍 {seb} Şebekesi Altındaki Durum:**")
            row = stats.loc[seb]
            
            bip51 = row.get('BiP (V5.1.23)', None)
            bip52 = row.get('BiP (V5.2.6)', None)
            wa = row.get('WhatsApp', None)
            
            if pd.notna(bip51) and pd.notna(bip52):
                if bip52 < bip51:
                    degisim = ((bip51 - bip52) / bip51) * 100
                    yorumlar.append(f"- **BiP Gelişimi:** Yeni V5.2.6 sürümü, eski V5.1.23 sürümüne göre **%{degisim:.1f} daha hızlıdır.** ✅")
                else:
                    degisim = ((bip52 - bip51) / bip51) * 100
                    yorumlar.append(f"- **BiP Gelişimi:** Yeni V5.2.6 sürümünde eski sürüme göre **%{degisim:.1f} oranında bir yavaşlama** saptanmıştır. ⚠️")
            
            mevcut_ortalamalar = [(k, v) for k, v in row.items() if pd.notna(v)]
            if mevcut_ortalamalar:
                mevcut_ortalamalar.sort(key=lambda x: x[1])
                lider_grup
