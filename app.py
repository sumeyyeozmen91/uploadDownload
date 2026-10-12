import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob
import re

# Sayfa ayarları
st.set_page_config(page_title="BiP (V5.6.19) & WhatsApp Performans Karşılaştırması", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP (V5.6.19) vs WhatsApp İndirme & Yükleme Performansı Analiz Paneli")
st.markdown("""
    Bu panelde **BiP (Sürüm: V5.6.19)** ve **WhatsApp** uygulamalarının LTE ve Wifi şebekeleri üzerindeki 
    Fotoğraf ve 2dk Video indirme/yükleme performansları, ortalama süreleri ve dosya boyutları ritmik koşum sırasına göre analiz edilir.
""")

# --- CİHAZ VE NUMARA BİLGİLERİ (ANA SAYFA) ---
col_up, col_down = st.columns(2)
with col_up:
    st.info("📤 **Yükleme (Upload) Yapan Cihaz:**\n- **Numara:** `+905316892026` \n- **Model:** Galaxy S21 FE 5G")
with col_down:
    st.success("📥 **İndirme (Download) Yapan Cihaz:**\n- **Numara:** `+905360301821` \n- **Model:** Galaxy A51")

st.markdown("---")

# İzin verilen tam dosya isimleri (Büyük/küçük harf duyarsız kontrol edilir)
ALLOWED_FILES = {
    "sd_2dkvideo_download_lte",
    "sd_2dkvideo_download_wifi",
    "sd_2dkvideo_upload_lte",
    "sd_2dkvideo_upload_wifi",
    "sd_2dkvideo_wa_download_lte",
    "sd_2dkvideo_wa_download_wifi",
    "sd_2dkvideo_wa_upload_lte",
    "sd_2dkvideo_wa_upload_wifi",
    "sd_photo_download_lte",
    "sd_photo_download_wifi",
    "sd_photo_upload_lte",
    "sd_photo_upload_wifi",
    "sd_photo_wa_download_lte",
    "sd_photo_wa_download_wifi",
    "sd_photo_wa_upload_lte",
    "sd_photo_wa_upload_wifi"
}

def veri_isle(file_path):
    try:
        if not os.path.exists(file_path):
            return None

        fname = os.path.basename(file_path)
        base_name = fname.split('.')[0].lower().strip()

        # Sadece izin verilen 16 dosyayı filtrele
        if base_name not in ALLOWED_FILES:
            return None

        # Dosya okuma (XLSX veya CSV)
        if file_path.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        elif file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            return None

        if df.empty:
            return None

        # --- SÜTUN İSİMLERİNİ TEMİZLEME VE DÜZENLEME ---
        df.rename(columns={df.columns[0]: 'Test Adı'}, inplace=True)
        df.columns = [str(c).strip() for c in df.columns]

        # 16 Özel Dosya Mimarisine Göre Metadata Belirleme
        is_wa = "_wa_" in base_name
        is_video = "2dkvideo" in base_name
        is_upload = "_upload_" in base_name
        is_wifi = "_wifi" in base_name

        medya_kalitesi = "SD"
        medya_turu = "2dkVideo" if is_video else "Photo"
        islem_turu = "Upload" if is_upload else "Download"
        network = "Wifi" if is_wifi else "4.5G (LTE)"

        if is_wa:
            app_name = "WhatsApp"
            version = "Güncel"
            grup_adi = "WhatsApp"
        else:
            app_name = "BiP"
            version = "V5.6.19"
            grup_adi = f"BiP ({version})"

        # --- SÜRE VE BOYUT HESAPLAMA ---
        duration_col = None
        compress_col = None
        size_col = None

        for c in df.columns:
            c_check = c.lower().replace('i̇', 'i').replace('ı', 'i')
            if "compressduration" in c_check or "sikistirma" in c_check:
                compress_col = c
            elif any(k in c_check for k in ["duration", "sure", "yukleme", "indirme"]):
                duration_col = c
            elif any(k in c_check for k in ["size", "boyut"]):
                size_col = c

        if duration_col is None and len(df.columns) >= 2:
            duration_col = df.columns[1]

        if duration_col is None:
            st.error(f"⚠️ {fname} içinde süre sütun yapısı çözülemedi!")
            return None

        # Sayısal veri temizliği
        for col in [duration_col, compress_col, size_col]:
            if col and col in df.columns:
                df[col] = df[col].apply(lambda x: ''.join(ch for ch in str(x) if ch.isdigit() or ch in ['.', ',']))
                df[col] = df[col].str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        if compress_col and compress_col in df.columns:
            df['Süre'] = df[duration_col] + df[compress_col]
        else:
            df['Süre'] = df[duration_col]

        if size_col and size_col in df.columns:
            df['Boyut (Bytes)'] = df[size_col]
            df['Boyut (MB)'] = (df[size_col] / (1024 * 1024)).round(2)
        else:
            df['Boyut (Bytes)'] = 0
            df['Boyut (MB)'] = 0.0

        df = df.dropna(subset=['Süre'])

        # Ritmik Sıralama için Test Adındaki Sayıyı Çekme (Örn: '1.SDPhoto' -> 1)
        def sira_numarasi_al(test_adi):
            match = re.search(r'(\d+)', str(test_adi))
            return int(match.group(1)) if match else 99

        df['Koşum Sırası'] = df['Test Adı'].apply(sira_numarasi_al)

        # Tabloya Metadata Sütunlarını Ekle
        df['Uygulama'] = app_name
        df['Versiyon'] = version
        df['Şebeke'] = network
        df['Grup'] = grup_adi
        df['Medya Kalitesi'] = medya_kalitesi
        df['Medya Türü'] = medya_turu
        df['İşlem Türü'] = islem_turu
        df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'DİĞER')

        return df[['Test Adı', 'Koşum Sırası', 'Uzantı', 'Süre', 'Boyut (MB)', 'Boyut (Bytes)', 'Uygulama', 'Versiyon', 'Şebeke', 'Grup', 'Medya Kalitesi', 'Medya Türü', 'İşlem Türü']]

    except Exception as e:
        st.error(f"⚠️ {os.path.basename(file_path)} işlenirken hata oluştu: {e}")
        return None

# --- PERFORMANS VE BiP vs WA YORUM MOTORU ---
def performans_yorumu(df, metrik_kolonu, islem_turu, sebeke_turu):
    if df.empty:
        return "Yorumlanacak veri bulunamadı."

    yorumlar = []
    gruplar = list(df['Grup'].unique())
    islem_str = "indirme" if islem_turu == "Download" else "yükleme"

    # Ortalama dosya boyutunu belirleme
    ort_boyut = df['Boyut (MB)'].mean()
    if ort_boyut > 0:
        yorumlar.append(f"📦 **Ortalama Dosya Büyüklüğü:** `{ort_boyut:.2f} MB` ({int(df['Boyut (Bytes)'].mean()):,} Bytes)")

    # BiP vs WhatsApp Doğrudan Karşılaştırma
    bip_groups = [g for g in gruplar if "BiP" in g]
    wa_exists = "WhatsApp" in gruplar

    if bip_groups and wa_exists:
        v_bip = bip_groups[-1]
        yorumlar.append(f"### ⚔️ BiP ({v_bip}) vs WhatsApp Karşılaştırması ({islem_str.capitalize()})")
        
        bip_sub = df[df['Grup'] == v_bip][metrik_kolonu]
        wa_sub = df[df['Grup'] == "WhatsApp"][metrik_kolonu]
        
        if not bip_sub.empty and not wa_sub.empty:
            ort_bip = bip_sub.mean()
            ort_wa = wa_sub.mean()
            
            bip_sec = ort_bip / 1000
            wa_sec = ort_wa / 1000
            
            if ort_bip < ort_wa:
                hiz_farki = ((ort
