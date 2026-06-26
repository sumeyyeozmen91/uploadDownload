import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Sayfa genel ayarları
st.set_page_config(page_title="BiP Sürüm Analiz Merkezi", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP Sürüm Gelişim ve Performans Analizi (V5.1.23 vs V5.2.6)")
st.markdown("""
    Bu panelde BiP uygulamasının **V5.1.23** ve **V5.2.6** sürümleri arasındaki performans gelişimi analiz edilir.
    - **Odaklanılan Şebekeler:** 4.5G & Wi-Fi
    - **Fotoğraf Kalite Tipleri:** HDPhoto & SDPhoto
""")

# --- TAM DOSYA İSİMLERİ YAPILANDIRMASI (.xlsx) ---
# Kısaltma olmadan, tam isimleri sadece .xlsx uzantılı olarak tanımlıyoruz
HEDEF_DOSYALAR = [
    {"dosya": "5.1.23_Bip_4.5G_HDPhoto.xlsx", "ver": "5.1.23", "net": "4.5G", "photo": "HDPhoto"},
    {"dosya": "5.1.23_Bip_4.5G_SDPhoto.xlsx", "ver": "5.1.23", "net": "4.5G", "photo": "SDPhoto"},
    {"dosya": "5.1.23_Bip_Wifi_HDPhoto.xlsx", "ver": "5.1.23", "net": "Wi-Fi", "photo": "HDPhoto"},
    {"dosya": "5.1.23_Bip_Wifi_SDPhoto.xlsx", "ver": "5.1.23", "net": "Wi-Fi", "photo": "SDPhoto"},
    
    {"dosya": "5.2.6_Bip_4.5G_HDPhoto.xlsx", "ver": "5.2.6", "net": "4.5G", "photo": "HDPhoto"},
    {"dosya": "5.2.6_Bip_4.5G_SDPhoto.xlsx", "ver": "5.2.6", "net": "4.5G", "photo": "SDPhoto"},
    {"dosya": "5.2.6_Bip_Wifi_HDPhoto.xlsx", "ver": "5.2.6", "net": "Wi-Fi", "photo": "HDPhoto"},
    {"dosya": "5.2.6_Bip_Wifi_SDPhoto.xlsx", "ver": "5.2.6", "net": "Wi-Fi", "photo": "SDPhoto"}
]

def veri_isle(cfg):
    try:
        file_path = cfg["dosya"]
        if not os.path.exists(file_path):
            return None
            
        # Doğrudan Excel (.xlsx) okuma motoru
        df = pd.read_excel(file_path)
        
        # Sütun isimlerini boşluklardan ve (ms) gibi eklerden arındır
        df.columns = [str(c).split(' (')[0].strip() for c in df.columns]
        
        # Sütun isim farklılıklarını standardize et
        rename_dict = {}
        for col in df.columns:
            if "İndirme" in col: rename_dict[col] = "İndirme Süresi"
            elif "Yükleme" in col: rename_dict[col] = "Yükleme Süresi"
            elif "Test Adı" in col: rename_dict[col] = "Test Adı"
        df = df.rename(columns=rename_dict)
        
        # Süre kolonlarını sayısal tipe zorla
        df["İndirme Süresi"] = pd.to_numeric(df["İndirme Süresi"], errors='coerce')
        df["Yükleme Süresi"] = pd.to_numeric(df["Yükleme Süresi"], errors='coerce')
        
        # Sabit haritadan gelen güvenli meta verileri doldur
        df['Uygulama'] = "BiP"
        df['Versiyon'] = cfg["ver"]
        df['Şebeke'] = cfg["net"]
        df['Fotoğraf Tipi'] = cfg["photo"]
        df['Grup'] = f"BiP (V{cfg['ver']})"
        
        # Dosya uzantısı ve dosya boyutunu test adından ayıkla
        df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'DİĞER')
        df['Boyut'] = df['Test Adı'].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x))
        
        return df[['Test Adı', 'Uzantı', 'Boyut', 'Yükleme Süresi', 'İndirme Süresi', 'Uygulama', 'Versiyon', 'Şebeke', 'Fotoğraf Tipi', 'Grup']]
    except Exception as e:
        return None

# --- SÜRÜM GELİŞİM ANALİZ MOTORU ---
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
                v51_sub = v51_df[(v51_df['Şebeke'] == seb) & (v51_df['Fotoğraf Tipi'] == f_tip)]
                v52_sub = v52_df[(v52_df['Şebeke'] == seb) & (v52_df
