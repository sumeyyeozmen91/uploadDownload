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
    Bu panelde BiP ve WhatsApp uygulamalarının **Download_Duration (İndirme Süresi)** performansları analiz edilir.
    
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

        df.columns = [str(c).strip() for c in df.columns]
        df.rename(columns={df.columns[0]: 'Test Adı'}, inplace=True)

        # --- DOWNLOAD_DURATION ODAKLI KONTROL ---
        duration_col = None
        for col in df.columns:
            if col.lower() == 'download_duration':
                duration_col = col
                break
        
        if duration_col is not None:
            df.rename(columns={duration_col: 'Download_Duration'}, inplace=True)
        else:
            for col in df.columns:
                if 'duration' in col.lower():
                    df.rename(columns={col: 'Download_Duration'}, inplace=True)
                    duration_col = col
                    break
        
        if 'Download_Duration' not in df.columns:
            return None

        # --- GÜVENLİ SAYISAL DÖNÜŞTÜRME ---
        df['Download_Duration'] = df['Download_Duration'].apply(lambda x: ''.join(c for c in str(x) if c.isdigit() or c in ['.', ',']))
        df['Download_Duration'] = df['Download_Duration'].str.replace(',', '.')
        df['Download_Duration'] = pd.to_numeric(df['Download_Duration'], errors='coerce').astype(float)

        df = df.dropna(subset=['Download_Duration'])
        fname = os.path.basename(file_path)

        # --- DOSYA ADI FORMATI AYRIŞTIRMA ---
        if "_" in fname:
            clean_name = fname.replace(".xlsx", "").replace(".csv", "")
            parts = clean_name.split('_')
            parts_lower = [p.lower() for p in parts]
            
            if parts_lower[0] == "wa":
                app_name = "WhatsApp"
                version = "Genel"
                net_raw = parts_lower[1]
                type_raw = parts_lower[2]
            elif "bip" in parts_lower:
                version = parts[0]
                app_name = "BiP"
                net_raw = parts_lower[2]
                type_raw = parts_lower[3]
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

        if "3g" in net_raw: network = "3G"
        elif "4g" in net_raw or "4.5g" in net_raw: network = "4.5G"
        elif "wifi" in net_raw: network = "Wi-Fi"
        else: network = net_raw.upper()

        df['Uygulama'] = app_name
        df['Versiyon'] = version
        df['Şebeke'] = network
        df['Grup'] = f"BiP (V{version})" if app_name == "BiP" else app_name
        df['Medya Kalitesi'] = medya_kalitesi
        df['Medya Türü'] = medya_turu

        return df[['Test Adı', 'Download_Duration', 'Uygulama', 'Versiyon', 'Şebeke', 'Grup', 'Medya Kalitesi', 'Medya Türü']]
    except Exception as e:
        return None

# --- GÜVENLİ HİZALANMIŞ KIYASLAMA MOTORU ---
def surum_gelisim_yorumu(df, metrik_kolonu):
    if df.empty:
        return "Yorumlanacak veri bulunamadı."

    yorumlar = []
    stats = df.groupby(['Şebeke', 'Grup'])[metrik_kolonu].mean().unstack(level=-1)
    
    yorumlar.append("## 📊 Detaylı Performans Analiz Raporu")
    
    for seb in sorted(df['Şebeke'].unique()):
        if seb in stats.index:
            yorumlar.append(f"\n### 📍 {seb} Şebekesi Analiz Sonuçları")
            row = stats.loc[seb]
            
            bip51 = row.get('BiP (V5.1.23)', None)
            bip52 = row.get('BiP (V5.2.6)', None)
            wa = row.get('WhatsApp', None)
            
            # 1. BiP Sürüm Karşılaştırması
            yorumlar.append("**🔄 1. BiP Sürüm Karşılaştırması (Sürüm Gelişimi):**")
            if pd.notna(bip51) and pd.notna(bip52):
                if bip52 < bip51:
                    fark_ms = int(bip51 - bip52)
                    yuzde = (bip51 - bip52) / bip51 * 100
                    txt = f"- **Durum:** Güncel **BiP (V5.2.6)**, eski sürüme göre süreyi **{fark_ms} ms** kısalttı (%{yuzde:.1f} hızlı). ✅"
                    yorumlar.append(txt)
                else:
                    fark_ms = int(bip52 - bip51)
                    yuzde = (bip52 - bip51) / bip51 * 100
                    txt = f"- **Durum:** Güncel **BiP (V5.2.6)**, eski sürüme göre süreyi **{fark_ms} ms** uzattı (%{yuzde:.1f} yavaş). ⚠️"
                    yorumlar.append(txt)
            else:
                yorumlar.append("- Karşılaştırma için yeterli BiP sürüm verisi bulunamadı.")
            
            # 2. BiP V5.2.6 vs WhatsApp Karşılaştırması
            yorumlar.append("\n**⚔️ 2. Rakip Karşılaştırması (BiP V5.2.6 vs WhatsApp):**")
            if
