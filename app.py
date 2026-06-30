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
    * **Uygulamalar:** BiP ve WhatsApp (Wa)
    * **Şebekeler:** 4.5G & Wi-Fi
    * **Medya Türleri:** HD & SD Fotoğraflar
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

        # --- DOSYA ADI FORMATI AYRIŞTIRMA (BiP & Wa Destekli) ---
        if "_" in fname:
            clean_name = fname.replace(".xlsx", "").replace(".csv", "")
            parts = clean_name.split('_')
            
            # Uygulama tespiti
            if "bip" in fname:
                app_name = "BiP"
                version = parts[0]   # Örn: "5.1.23" veya "5.2.6"
                net_raw = parts[2]   # "4.5g" veya "wifi"
                type_raw = parts[3]  # "hdphoto" veya "sdphoto"
            elif "wa" in fname or parts[0] == "wa":
                app_name = "WhatsApp"
                version = "Mevcut"   # Belirli bir sürüm yoksa genel etiket
                net_raw = parts[1]   # "4.5g" veya "wifi"
                type_raw = parts[2]  # "hdphoto" veya "sdphoto"
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
        
        # Grafik renk gruplaması için uygulama ve versiyon birleşimi
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
        st.error(f"⚠️ {os.path.basename(file_path)} işlenirken hata oluştu: {e}")
        return None

# --- SÜRÜM VE UYGULAMA GELİŞİM YORUM MOTORU ---
def surum_gelisim_yorumu(df, metrik_kolonu):
    if df.empty:
        return "Yorumlanacak veri bulunamadı."

    yorumlar = []
    gruplar = sorted(list(df['Grup'].unique()))
    sebekeler = sorted(list(df['Şebeke'].unique()))
    
    yorumlar.append("### 📊 Genel Performans ve Rekabet Özeti")
    
    for seb in sebekeler:
        seb_df = df[df['Şebeke'] == seb]
        yorumlar.append(f"\n**{seb} Şebekesi Analizi:**")
        
        # Her grubun ortalamasını hesapla
        ortalamalar = {}
        for g in gruplar:
            g_ort = seb_df[seb_df['Grup'] == g][metrik_kolonu].mean()
            if pd.notna(g_ort):
                ortalamalar[g] = g_ort
                
        # Ortalamaları küçükten büyüğe (hızlıdan yavaşa) sırala
        sirali_ort = sorted(ortalamalar.items(), key=lambda x: x[1])
        
        for idx, (grup_adi, ort_sure) in enumerate(sirali_ort):
            madde = f"- {idx+1}. **{grup_adi}**: Ortalama {ort_sure:.1f} ms"
            if idx == 0:
                madde += " 🥇 (En Hızlı)"
            yorumlar.append(madde)
            
    return "\n".join(yorumlar)

# --- VERİ TARAMA VE YÜKLEME ---
all_files = glob.glob("*.xlsx") + glob.glob("*.XLSX")
all_files = list(set(all_files))

all_data = []
for f in all_files:
    res = veri_isle(f)
    if res is not None:
        all_data.append(res)

if all_data:
    full_df = pd.concat(all_data, ignore_index=True)

    # --- FİLTRELER (SIDEBAR) ---
    st.sidebar.header("⚙️ Analiz Ayarları")

    kalite_listesi = sorted(full_df['Medya Kalitesi'].unique())
    secilen_kalite = st.sidebar.selectbox("Medya Kalitesi Seçin:", kalite_listesi)

    tur_listesi = sorted(full_df['Medya Türü'].unique())
    secilen_tur = st.sidebar.selectbox("Medya Türü Seçin:", tur_listesi)

    mevcut_gruplar = sorted(full_df['Grup'].unique())
    secilen_gruplar = st.sidebar.multiselect("Grafikte Gösterilecek Gruplar / Versiyonlar:", mevcut_gruplar, default=mevcut_gruplar)

    # Temel Filtreleme
    plot_df = full_df[
        (full_df['Medya Kalitesi'] == secilen_kalite) & 
        (full_df['Medya Türü'] == secilen_tur) & 
        (full_df['Grup'].isin(secilen_gruplar))
    ].copy()

    if not plot_df.empty:
        # --- DİNAMİK KOŞUM SAYISI (SIRA NO) ATAMA ---
        plot_df = plot_df.sort_values(by=['Şebeke', 'Grup', 'Boyut'])
        plot_df['Koşum Sayısı'] = plot_df.groupby(['Şebeke', 'Grup']).cumcount() + 1
        plot_df['Koşum Sayısı'] = plot_df['Koşum Sayısı'].astype(str) + ". Koşum"

        # Dinamik Renk Paleti (BiP Sürümleri Mavi Tonları, WhatsApp Yeşil)
        color_map = {}
        for grup in mevcut_gruplar:
            if "WhatsApp" in grup:
                color_map[grup] = '#2ecc71' # WhatsApp Yeşili
            elif "5.1.23" in grup:
                color_map[grup] = '#349
