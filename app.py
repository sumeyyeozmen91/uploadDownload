import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# Sayfa ayarları
st.set_page_config(page_title="BiP Sürüm Analiz Merkezi", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP Sürüm Gelişim ve Performans Analizi (V5.1.23 vs V5.2.6)")
st.markdown("""
    Bu panelde BiP uygulamasının **V5.1.23** ve **V5.2.6** sürümleri arasındaki performans gelişimi analiz edilir.
    - **Odaklanılan Şebekeler:** 4.5G & Wi-Fi
    - **Fotoğraf Kalite Tipleri:** HDPhoto & SDPhoto
""")

def veri_isle(file_path):
    try:
        if not os.path.exists(file_path):
            return None
            
        # Uzantıya göre esnek okuma (CSV veya Excel)
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # Sütun isimlerini temizle
        df.columns = [str(c).split(' (')[0].strip() for c in df.columns]
        
        # Olası sütun isim farklılıklarını standartlaştır
        rename_dict = {}
        for col in df.columns:
            if "İndirme" in col: rename_dict[col] = "İndirme Süresi"
            elif "Yükleme" in col: rename_dict[col] = "Yükleme Süresi"
            elif "Test Adı" in col: rename_dict[col] = "Test Adı"
        df = df.rename(columns=rename_dict)
        
        df["İndirme Süresi"] = pd.to_numeric(df["İndirme Süresi"], errors='coerce')
        df["Yükleme Süresi"] = pd.to_numeric(df["Yükleme Süresi"], errors='coerce')
        
        fname = os.path.basename(file_path).lower()
        
        # --- DOSYA ADI FORMATI AYRIŞTIRMA (Örn: 5.1.23_bip_4.5g_hdphoto...) ---
        if "_" in fname and (fname.startswith('5.1.23') or fname.startswith('5.2.6')):
            parts = fname.split('_')
            version = parts[0]       # "5.1.23" veya "5.2.6"
            net_raw = parts[2]       # "4.5g" veya "wifi"
            photo_type = parts[3].replace(".xlsx", "").replace(".csv", "").upper() # "HDPHOTO" veya "SDPHOTO"
        else:
            return None # İlgilenilmeyen formatları es geç
        
        # Şebeke ismini standartlaştır
        if "4.5g" in net_raw or "4g" in net_raw: 
            network = "4.5G"
        elif "wifi" in net_raw: 
            network = "Wi-Fi"
        else:
            return None # 3G veya diğer şebekeleri analiz dışı bırak
        
        # DataFrame alanlarını doldur
        df['Uygulama'] = "BiP"
        df['Versiyon'] = version
        df['Şebeke'] = network
        df['Fotoğraf Tipi'] = photo_type
        df['Grup'] = f"BiP (V{version})"
        
        # Dosya uzantısı ve dosya boyutunu ayıkla
        df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'DİĞER')
        df['Boyut'] = df['Test Adı'].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x))
        
        return df[['Test Adı', 'Uzantı', 'Boyut', 'Yükleme Süresi', 'İndirme Süresi', 'Uygulama', 'Versiyon', 'Şebeke', 'Fotoğraf Tipi', 'Grup']]
    except Exception as e:
        st.error(f"⚠️ {file_path} işlenirken hata oluştu: {e}")
        return None

# --- SÜRÜM GELİŞİM YORUM MOTORU ---
def surum_gelisim_yorumu(df, metrik_kolonu, metrik_adi):
    if df.empty:
        return "Yorumlanacak veri bulunamadı."
    
    yorumlar = []
    v51_df = df[df['Versiyon'] == '5.1.23']
    v52_df = df[df['Versiyon'] == '5.2.6']
    
    yorumlar.append(f"### 🔄 BiP V5.1.23 Sürümünden V5.2.6 Sürümüne Geçiş {metrik_adi.upper()} Analizi")
    
    if not v51_df.empty and not v52_df.empty:
        sebekeler = ["4.5G", "Wi-Fi"]
        foto_tipleri = sorted(df['Fotoğraf Tipi'].unique())
        
        for seb in sebekeler:
            for f_tip in foto_tipleri:
                v51_sub = v51_
