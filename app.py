import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# Sayfa ayarları
st.set_page_config(page_title="BiP Sürüm Analiz Merkezi", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP Sürüm Gelişimi ve Performans Analizi (V5.1.23 vs V5.2.6)")
st.markdown("""
    Bu panelde, sadece **BiP V5.1.23** ve **BiP V5.2.6** sürümlerinin **4.5G** ve **Wi-Fi** şebekeleri altındaki performans gelişimleri analiz edilir. 
    Medya türlerine (`HDPhoto` ve `SDPhoto`) göre yükleme ve indirme optimizasyonları otomatik olarak kıyaslanır.
""")

def veri_isle(file_path):
    try:
        if not os.path.exists(file_path):
            return None
            
        # Eğer CSV ise read_csv, Excel ise read_excel kullan (İki formata da uyumluluk için)
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        
        # Sütun isimlerini temizle (Örn: "Yükleme Süresi (ms)" -> "Yükleme Süresi")
        df.columns = [str(c).split(' (')[0].strip() for c in df.columns]
        
        # Olası sütun adı farklılıklarını standartlaştır
        rename_dict = {}
        for col in df.columns:
            if "İndirme" in col: rename_dict[col] = "İndirme Süresi"
            elif "Yükleme" in col: rename_dict[col] = "Yükleme Süresi"
            elif "Test Adı" in col: rename_dict[col] = "Test Adı"
        df = df.rename(columns=rename_dict)
        
        # Süreleri sayısal tipe zorla
        df["İndirme Süresi"] = pd.to_numeric(df["İndirme Süresi"], errors='coerce')
        df["Yükleme Süresi"] = pd.to_numeric(df["Yükleme Süresi"], errors='coerce')
        
        fname = os.path.basename(file_path).lower()
        
        # --- DOSYA ADI FORMATI AYRIŞTIRMA ---
        # Örn: 5.1.23_bip_4.5g_hdphoto...
        if "_" in fname and (fname.startswith('5.1.23') or fname.startswith('5.2.6')):
            parts = fname.split('_')
            version = parts[0]     # "5.1.23" veya "5.2.6"
            app_name = "BiP"
            net_raw = parts[2]     # "4.5g" veya "wifi"
            media_raw = parts[3].split('.')[0]  # "hdphoto" veya "sdphoto"
        else:
            return None  # İlgisiz veya eski formatta olan dosyaları es geç
        
        # Şebeke ismini standartlaştır (3G devre dışı)
        if "4.5g" in net_raw or "4g" in net_raw: 
            network = "4.5G"
        elif "wifi" in net_raw: 
            network = "Wi-Fi"
        else: 
            network = net_raw.upper()
            
        # Medya türünü standartlaştır
        media_type = "HD Fotoğraf" if "hd" in media_raw else "SD Fotoğraf"
        
        # DataFrame sütunlarını doldur
        df['Uygulama'] = app_name
        df['Versiyon'] = version
        df['Şebeke'] = network
        df['Medya Türü'] = media_type
        df['Grup'] = f"BiP (V{version})"
        
        # Dosya uzantısı ve boyut etiketini çıkarma
        df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'DİĞER')
        df['Boyut'] = df['Test Adı'].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x))
        
        return df[['Test Adı', 'Uzantı', 'Boyut', 'Yükleme Süresi', 'İndirme Süresi', 'Uygulama', 'Versiyon', 'Şebeke', 'Medya Türü', 'Grup']]
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
    
    yorumlar.append(f"### 🔄 Sürümler Arası {metrik_adi.capitalize()} Süresi Gelişim Analizi")
    
    if not v51_df.empty and not v52_df.empty:
        sebekeler = sorted(list(set(v51_df['Şebeke']).intersection(set(v52_df['Şebeke']))))
        for seb in sebekeler:
            v51_ort = v51_df[v51_df['Şebeke'] == seb][metrik_kolonu].mean()
            v52_ort = v52_df[v52_df['Şebeke'] == seb][metrik_kolonu].mean()
            
            if pd.notna(v51_ort) and pd.notna(v52_ort):
                if v52_ort < v51_ort:
                    iyilesme = ((v51_ort - v52_ort) / v51_ort) * 100
                    yorumlar.append(f"- **{seb} Şebekesinde:** Yeni **V5.2.6 sürümü**, eski V5.1.23'e göre ortalama {metrik_adi} süresini **%{iyilesme:.1f} azaltarak (hızlandırarak)** başarılı bir optimizasyon kaydetmiştir. ✅")
                else:
                    yavaslama = ((v52_ort - v51_ort) / v51_ort) * 100
                    yorumlar.append(f"- **{seb} Şebekesinde:** Yeni **V5.2.6 sürümünde**, V5.1.23'e kıyasla %{yavaslama:.1f} oranında bir **yavaşlama (süre artışı/regresyon)** saptanmıştır. ⚠️")
    else:
        yorum
