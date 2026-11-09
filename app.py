import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob
import re

# Sayfa ayarları
st.set_page_config(page_title="BiP & WhatsApp Performans Karşılaştırması", layout="wide")

# --- İZİN VERİLEN DOSYA LİSTESİ (DİNAMİK ÜRETİM) ---
PREFIXES = ["hd_2dkvideo", "hd_photo", "mp4", "pdf", "rar", "sd_2dkvideo", "sd_photo", "txt", "xlsx", "zip"]
NETWORKS = ["lte", "wifi"]
OPERATIONS = ["download", "upload"]

ALLOWED_FILES = set()
for p in PREFIXES:
    for op in OPERATIONS:
        for net in NETWORKS:
            ALLOWED_FILES.add(f"{p}_{op}_{net}")
            ALLOWED_FILES.add(f"{p}_wa_{op}_{net}")
            ALLOWED_FILES.add(f"{p}_wa_ios_{op}_{net}")
            if p == "sd_2dkvideo":
                ALLOWED_FILES.add(f"{p}_ios_{op}_{net}")

MEDYA_TURU_ISIMLERI = {
    "hd_2dkvideo": "HD 2dk Video",
    "hd_photo": "HD Fotoğraf",
    "mp4": "MP4 Video",
    "pdf": "PDF Belge",
    "rar": "RAR Arşiv",
    "sd_2dkvideo": "SD 2dk Video",
    "sd_photo": "SD Fotoğraf",
    "txt": "TXT Metin",
    "xlsx": "XLSX Tablo",
    "zip": "ZIP Arşiv"
}

NUMBERED_PREFIXES = {"sd_photo", "sd_2dkvideo", "hd_photo", "hd_2dkvideo"}
NUMBERED_MEDYA_TURLERI = {"SD Fotoğraf", "SD 2dk Video", "HD Fotoğraf", "HD 2dk Video"}

# --- SPEEDTEST REFERANS TABLOSU (ANDROID & iOS) ---
# Yükleme yapan cihazın (Android: J2D, iOS: YRC) Upload hızı ve İndirme yapan cihazın (Android: YHV, iOS: HXC) Download hızı baz alınır.
SPEEDTEST_META = {
    # Android - BiP - 4.5G (LTE) (Photo & Video: Güncel Tablo | Diğerleri: ag_hiz_test_sonuclari.xlsx)
    ("Android", "BiP", "SD Fotoğraf", "4.5G (LTE)"): {"upload_mbps": 78.6, "download_mbps": 91.4},
    ("Android", "BiP", "SD 2dk Video", "4.5G (LTE)"): {"upload_mbps": 76.2, "download_mbps": 104.0},
    ("Android", "BiP", "HD Fotoğraf", "4.5G (LTE)"): {"upload_mbps": 84.6, "download_mbps": 103.0},
    ("Android", "BiP", "HD 2dk Video", "4.5G (LTE)"): {"upload_mbps": 77.7, "download_mbps": 103.0},
    ("Android", "BiP", "MP4 Video", "4.5G (LTE)"): {"upload_mbps": 70.3, "download_mbps": 104.6},
    ("Android", "BiP", "PDF Belge", "4.5G (LTE)"): {"upload_mbps": 69.1, "download_mbps": 104.0},
    ("Android", "BiP", "RAR Arşiv", "4.5G (LTE)"): {"upload_mbps": 64.0, "download_mbps": 104.0},
    ("Android", "BiP", "TXT Metin", "4.5G (LTE)"): {"upload_mbps": 57.5, "download_mbps": 100.0},
    ("Android", "BiP", "XLSX Tablo", "4.5G (LTE)"): {"upload_mbps": 47.8, "download_mbps": 75.3},
    ("Android", "BiP", "ZIP Arşiv", "4.5G (LTE)"): {"upload_mbps": 64.8, "download_mbps": 45.3},

    # Android - WhatsApp - 4.5G (LTE) (Photo & Video: Güncel Tablo | Diğerleri: ag_hiz_test_sonuclari.xlsx)
    ("Android", "WhatsApp", "SD Fotoğraf", "4.5G (LTE)"): {"upload_mbps": 53.4, "download_mbps": 85.5},
    ("Android", "WhatsApp", "SD 2dk Video", "4.5G (LTE)"): {"upload_mbps": 76.5, "download_mbps": 105.0},
    ("Android", "WhatsApp", "HD Fotoğraf", "4.5G (LTE)"): {"upload_mbps": 77.9, "download_mbps": 104.0},
    ("Android", "WhatsApp", "HD 2dk Video", "4.5G (LTE)"): {"upload_mbps": 82.3, "download_mbps": 103.0},
    ("Android", "WhatsApp", "MP4 Video", "4.5G (LTE)"): {"upload_mbps": 64.5, "download_mbps": 89.8},
    ("Android", "WhatsApp", "PDF Belge", "4.5G (LTE)"): {"upload_mbps": 84.5, "download_mbps": 103.0},
    ("Android", "WhatsApp", "RAR Arşiv", "4.5G (LTE)"): {"upload_mbps": 69.1, "download_mbps": 94.7},
    ("Android", "WhatsApp", "TXT Metin", "4.5G (LTE)"): {"upload_mbps": 85.6, "download_mbps": 103.0},
    ("Android", "WhatsApp", "XLSX Tablo", "4.5G (LTE)"): {"upload_mbps": 76.7, "download_mbps": 102.0},
    ("Android", "WhatsApp", "ZIP Arşiv", "4.5G (LTE)"): {"upload_mbps": 82.4, "download_mbps": 104.0},

    # Android - BiP - Wifi (Photo & Video: Güncel Tablo | Diğerleri: ag_hiz_test_sonuclari.xlsx)
    ("Android", "BiP", "SD Fotoğraf", "Wifi"): {"upload_mbps": 48.3, "download_mbps": 45.6},
    ("Android", "BiP", "SD 2dk Video", "Wifi"): {"upload_mbps": 26.6, "download_mbps": 85.7},
    ("Android", "BiP", "HD Fotoğraf", "Wifi"): {"upload_mbps": 28.6, "download_mbps": 85.4},
    ("Android", "BiP", "HD 2dk Video", "Wifi"): {"upload_mbps": 49.7, "download_mbps": 70.7},
    ("Android", "BiP", "MP4 Video", "Wifi"): {"upload_mbps": 17.2, "download_mbps": 93.2},
    ("Android", "BiP", "PDF Belge", "Wifi"): {"upload_mbps": 17.1, "download_mbps": 93.1},
    ("Android", "BiP", "RAR Arşiv", "Wifi"): {"upload_mbps": 90.2, "download_mbps": 93.9},
    ("Android", "BiP", "TXT Metin", "Wifi"): {"upload_mbps": 28.7, "download_mbps": 55.4},
    ("Android", "BiP", "XLSX Tablo", "Wifi"): {"upload_mbps": 54.7, "download_mbps": 65.6},
    ("Android", "BiP", "ZIP Arşiv", "Wifi"): {"upload_mbps": 28.9, "download_mbps": 66.0},

    # Android - WhatsApp - Wifi (Photo & Video: Güncel Tablo | Diğerleri: ag_hiz_test_sonuclari.xlsx)
    ("Android", "WhatsApp", "SD Fotoğraf", "Wifi"): {"upload_mbps": 30.1, "download_mbps": 80.7},
    ("Android", "WhatsApp", "SD 2dk Video", "Wifi"): {"upload_mbps": 40.7, "download_mbps": 79.3},
    ("Android", "WhatsApp", "HD Fotoğraf", "Wifi"): {"upload_mbps": 21.3, "download_mbps": 92.9},
    ("Android", "WhatsApp", "HD 2dk Video", "Wifi"): {"upload_mbps": 45.4, "download_mbps": 45.4},
    ("Android", "WhatsApp", "MP4 Video", "Wifi"): {"upload_mbps": 26.5, "download_mbps": 59.4},
    ("Android", "WhatsApp", "PDF Belge", "Wifi"): {"upload_mbps": 36.5, "download_mbps": 40.9},
    ("Android", "WhatsApp", "RAR Arşiv", "Wifi"): {"upload_mbps": 56.3, "download_mbps": 85.5},
    ("Android", "WhatsApp", "TXT Metin", "Wifi"): {"upload_mbps": 54.3, "download_mbps": 84.6},
    ("Android", "WhatsApp", "XLSX Tablo", "Wifi"): {"upload_mbps": 80.8, "download_mbps": 93.6},
    ("Android", "WhatsApp", "ZIP Arşiv", "Wifi"): {"upload_mbps": 28.6, "download_mbps": 70.1},

    # iOS - BiP - 5G & Wifi
    ("iOS", "BiP", "SD 2dk Video", "5G"): {"upload_mbps": 5.05, "download_mbps": 346.0},
    ("iOS", "BiP", "SD 2dk Video", "Wifi"): {"upload_mbps": 57.1, "download_mbps": 49.4},
    ("iOS", "BiP", "SD Fotoğraf", "5G"): {"upload_mbps": 27.3, "download_mbps": 45.7},
    ("iOS", "BiP", "SD Fotoğraf", "Wifi"): {"upload_mbps": 41.6, "download_mbps": 67.1},
    ("iOS", "BiP", "MP4 Video", "5G"): {"upload_mbps": 70.3, "download_mbps": 104.6},
    ("iOS", "BiP", "MP4 Video", "Wifi"): {"upload_mbps": 17.2, "download_mbps": 93.2},
    ("iOS", "BiP", "PDF Belge", "5G"): {"upload_mbps": 69.1, "download_mbps": 104.0},
    ("iOS", "BiP", "PDF Belge", "Wifi"): {"upload_mbps": 17.1, "download_mbps": 93.1},
    ("iOS", "BiP", "RAR Arşiv", "5G"): {"upload_mbps": 64.0, "download_mbps": 104.0},
    ("iOS", "BiP", "RAR Arşiv", "Wifi"): {"upload_mbps": 90.2, "download_mbps": 93.9},
    ("iOS", "BiP", "TXT Metin", "5G"): {"upload_mbps": 57.5, "download_mbps": 100.0},
    ("iOS", "BiP", "TXT Metin", "Wifi"): {"upload_mbps": 28.7, "download_mbps": 55.4},
    ("iOS", "BiP", "XLSX Tablo", "5G"): {"upload_mbps": 47.8, "download_mbps": 75.3},
    ("iOS", "BiP", "XLSX Tablo", "Wifi"): {"upload_mbps": 54.7, "download_mbps": 65.6},
    ("iOS", "BiP", "ZIP Arşiv", "5G"): {"upload_mbps": 64.8, "download_mbps": 45.3},
    ("iOS", "BiP", "ZIP Arşiv", "Wifi"): {"upload_mbps": 28.9, "download_mbps": 66.0},

    # iOS - WhatsApp - 5G & Wifi
    ("iOS", "WhatsApp", "MP4 Video", "5G"): {"upload_mbps": 3.99, "download_mbps": 105.0},
    ("iOS", "WhatsApp", "PDF Belge", "5G"): {"upload_mbps": 6.13, "download_mbps": 92.6},
    ("iOS", "WhatsApp", "SD Fotoğraf", "5G"): {"upload_mbps": 7.54, "download_mbps": 122.0},
    ("iOS", "WhatsApp", "SD 2dk Video", "5G"): {"upload_mbps": 6.80, "download_mbps": 136.0},
    ("iOS", "WhatsApp", "RAR Arşiv", "5G"): {"upload_mbps": 69.1, "download_mbps": 94.7},
    ("iOS", "WhatsApp", "TXT Metin", "5G"): {"upload_mbps": 85.6, "download_mbps": 103.0},
    ("iOS", "WhatsApp", "XLSX Tablo", "5G"): {"upload_mbps": 76.7, "download_mbps": 102.0},
    ("iOS", "WhatsApp", "ZIP Arşiv", "5G"): {"upload_mbps": 82.4, "download_mbps": 104.0},
    ("iOS", "WhatsApp", "MP4 Video", "Wifi"): {"upload_mbps": 75.3, "download_mbps": 82.8},
    ("iOS", "WhatsApp", "PDF Belge", "Wifi"): {"upload_mbps": 36.8, "download_mbps": 75.5},
    ("iOS", "WhatsApp", "SD Fotoğraf", "Wifi"): {"upload_mbps": 56.9, "download_mbps": 75.8},
    ("iOS", "WhatsApp", "SD 2dk Video", "Wifi"): {"upload_mbps": 91.6, "download_mbps": 77.7},
    ("iOS", "WhatsApp", "RAR Arşiv", "Wifi"): {"upload_mbps": 56.3, "download_mbps": 85.5},
    ("iOS", "WhatsApp", "TXT Metin", "Wifi"): {"upload_mbps": 54.3, "download_mbps": 84.6},
    ("iOS", "WhatsApp", "XLSX Tablo", "Wifi"): {"upload_mbps": 80.8, "download_mbps": 93.6},
    ("iOS", "WhatsApp", "ZIP Arşiv", "Wifi"): {"upload_mbps": 28.6, "download_mbps": 70.1},
}

def yukle_ag_performans_tablosu(base_dir):
    tablo_yolu = os.path.join(base_dir, "Ag_Performans_Test_Verileri.xlsx")
    if not os.path.exists(tablo_yolu):
        return
    try:
        raw_df = pd.read_excel(tablo_yolu)
        for _, row in raw_df.iterrows():
            senaryo = str(row.iloc[1]).strip() if len(row) > 1 else ""
            baglanti = str(row.iloc[2]).strip().upper() if len(row) > 2 else ""
            if not senaryo or senaryo == "nan" or "Uygulama" in senaryo:
                continue

            uyg = "BiP" if senaryo.upper().startswith("BIP") or senaryo.upper().startswith("BİP") else ("WhatsApp" if senaryo.upper().startswith("WA") else None)
            if not uyg:
                continue

            senaryo_up = senaryo.upper()
            if "SD PHOTO" in senaryo_up:
                m_turu = "SD Fotoğraf"
            elif "SD VIDEO" in senaryo_up:
                m_turu = "SD 2dk Video"
            elif "HD PHOTO" in senaryo_up:
                m_turu = "HD Fotoğraf"
            elif "HD VIDEO" in senaryo_up:
                m_turu = "HD 2dk Video"
            else:
                continue

            net = "Wifi" if "WIFI" in baglanti else "4.5G (LTE)"
            j2d_up = pd.to_numeric(row.iloc[4], errors="coerce")
            yhv_down = pd.to_numeric(row.iloc[5], errors="coerce")
            if pd.notna(j2d_up) and pd.notna(yhv_down):
                SPEEDTEST_META[("Android", uyg, m_turu, net)] = {
                    "upload_mbps": float(j2d_up),
                    "download_mbps": float(yhv_down)
                }
    except Exception:
        pass

def veri_isle(file_path):
    try:
        if not os.path.exists(file_path):
            return None

        fname = os.path.basename(file_path)
        base_name = fname.split('.')[0].lower().strip()

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

        is_ios = "_ios_" in base_name
        is_wa = "_wa_" in base_name
        is_upload = "_upload_" in base_name
        is_wifi = "_wifi" in base_name

        matched_prefix = "diğer"
        for p in PREFIXES:
            if base_name.startswith(p + "_") or f"_{p}_" in base_name:
                matched_prefix = p
                break

        if matched_prefix.startswith("hd_"):
            medya_kalitesi = "HD"
        elif matched_prefix.startswith("sd_"):
            medya_kalitesi = "SD"
        else:
            medya_kalitesi = "Standart"

        medya_turu = MEDYA_TURU_ISIMLERI.get(matched_prefix, matched_prefix.upper())
        islem_turu = "Upload" if is_upload else "Download"
        network = "Wifi" if is_wifi else ("5G" if is_ios else "4.5G (LTE)")
        platform = "iOS" if is_ios else "Android"

        if is_wa:
            app_name = "WhatsApp"
            version = "Güncel"
            grup_adi = "WhatsApp"
        else:
            app_name = "BiP"
            version = "V5.6.41" if is_ios else "V5.6.19"
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
            return None

        for col in [duration_col, compress_col, size_col]:
            if col and col in df.columns:
                df[col] = df[col].apply(lambda x: ''.join(ch for ch in str(x) if ch.isdigit() or ch in ['.', ',']))
                df[col] = df[col].str.replace(',', '.')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        if compress_col and compress_col in df.columns:
            df['Süre'] = df[duration_col] + df[compress_col]
        else:
            df['Süre'] = df[duration_col]

        # iOS BiP Download verileri halihazırda saniye (sn) cinsindendir;
        # diğer tüm veriler milisaniye (ms) cinsinden olduğu için saniyeye (sn) çevrilir.
        is_already_seconds = (is_ios and not is_wa and not is_upload)
        if not is_already_seconds:
            df['Süre'] = df['Süre'] / 1000.0
        df['Süre'] = df['Süre'].round(2)

        # --- BOYUT ATAMALARI ---
        if size_col and size_col in df.columns:
            df['Boyut (Bytes)'] = df[size_col]
            df['Boyut (MB)'] = (df[size_col] / (1024 * 1024)).round(4)
        else:
            df['Boyut (Bytes)'] = 0
            df['Boyut (MB)'] = 0.0

        # --- SPEEDTEST ATAMALARI ---
        meta = SPEEDTEST_META.get((platform, app_name, medya_turu, network), {})
        speed_val = meta.get("upload_mbps") if is_upload else meta.get("download_mbps")
        df['Speedtest (Mbps)'] = f"{speed_val} Mbps" if speed_val is not None else "-"

        df = df.dropna(subset=['Süre'])

        # --- KOŞUM / ETİKET BELİRLEME (SD/HD Photo ve SD/HD 2dkVideo için numaralandırma) ---
        is_numbered_media = matched_prefix in NUMBERED_PREFIXES

        def sira_numarasi_al(test_adi):
            test_str = str(test_adi).strip()
            if not is_numbered_media:
                return 0
            
            match = re.match(r'^(\d+)', test_str)
            if match:
                return int(match.group(1))
            
            tum_sayilar = re.findall(r'\d+', test_str)
            for s in tum_sayilar:
                val = int(s)
                if val not in [40, 70, 80, 90, 32, 38, 26]:
                    return val
            return int(tum_sayilar[0]) if tum_sayilar else 99

        df['Koşum Sırası'] = df['Test Adı'].apply(sira_numarasi_al)
        if is_numbered_media and df['Koşum Sırası'].nunique() == 1 and len(df) > 1:
            df['Koşum Sırası'] = range(1, len(df) + 1)

        if is_numbered_media:
            df['Grafik Etiketi'] = df['Koşum Sırası'].astype(str) + ". Koşum"
        else:
            df['Grafik Etiketi'] = df['Test Adı'].astype(str)

        df['Platform'] = platform
        df['Uygulama'] = app_name
        df['Versiyon'] = version
        df['Şebeke'] = network
        df['Grup'] = grup_adi
        df['Medya Kalitesi'] = medya_kalitesi
        df['Medya Türü'] = medya_turu
        df['İşlem Türü'] = islem_turu
        df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'DİĞER')

        return df[['Test Adı', 'Koşum Sırası', 'Grafik Etiketi', 'Uzantı', 'Süre', 'Boyut (MB)', 'Boyut (Bytes)', 'Speedtest (Mbps)', 'Platform', 'Uygulama', 'Versiyon', 'Şebeke', 'Grup', 'Medya Kalitesi', 'Medya Türü', 'İşlem Türü']]

    except Exception as e:
        return None

# --- PERFORMANS YORUM MOTORU ---
def performans_yorumu(df, metrik_kolonu, islem_turu, sebeke_turu):
    if df.empty:
        return "Yorumlanacak veri bulunamadı."

    yorumlar = []
    gruplar = list(df['Grup'].unique())
    islem_str = "indirme" if islem_turu == "Download" else "yükleme"

    ort_boyut = df['Boyut (MB)'].mean()
    if ort_boyut > 0:
        yorumlar.append(f"📦 **Ortalama Dosya Büyüklüğü:** `{ort_boyut:.4f} MB` ({int(df['Boyut (Bytes)'].mean()):,} Bytes)")

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
            
            if ort_bip < ort_wa:
                hiz_farki = ((ort_wa / ort_bip) - 1) * 100
                saniye_farki = ort_wa - ort_bip
                yorumlar.append(
                    f"- **{sebeke_turu} Şebekesinde:** **BiP** (`{ort_bip:.2f} sn`), "
                    f"WhatsApp'a (`{ort_wa:.2f} sn`) göre **{saniye_farki:.2f} saniye daha erken tamamlanarak %{hiz_farki:.1f} daha hızlıdır.** 🚀"
                )
            elif ort_wa < ort_bip:
                hiz_farki = ((ort_bip / ort_wa) - 1) * 100
                saniye_farki = ort_bip - ort_wa
                yorumlar.append(
                    f"- **{sebeke_turu} Şebekesinde:** **WhatsApp** (`{ort_wa:.2f} sn`), "
                    f"BiP'e (`{ort_bip:.2f} sn`) göre **{saniye_farki:.2f} saniye daha erken tamamlanarak %{hiz_farki:.1f} daha hızlıdır.** 📉"
                )
            else:
                yorumlar.append(f"- **{sebeke_turu} Şebekesinde:** BiP ve WhatsApp eşit süre kaydetmiştir (`{ort_bip:.2f} sn`). ⚖️")
    elif bip_groups:
        v_bip = bip_groups[-1]
        ort_bip = df[df['Grup'] == v_bip][metrik_kolonu].mean()
        yorumlar.append(f"- **{sebeke_turu} Şebekesinde:** **BiP ({v_bip})** ortalama {islem_str} süresi **`{ort_bip:.2f} sn`** olarak gerçekleşmiştir.")
    elif wa_exists:
        ort_wa = df[df['Grup'] == "WhatsApp"][metrik_kolonu].mean()
        yorumlar.append(f"- **{sebeke_turu} Şebekesinde:** **WhatsApp** ortalama {islem_str} süresi **`{ort_wa:.2f} sn`** olarak gerçekleşmiştir.")

    return "\n\n".join(yorumlar) if yorumlar else "Kıyaslama için yeterli veri bulunmuyor."

# --- ÇALIŞMA DİZİNİ VE DOSYA TARAMA AYARI ---
script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
yukle_ag_performans_tablosu(script_dir)

found_files = (
    glob.glob(os.path.join(script_dir, "*.xlsx")) + 
    glob.glob(os.path.join(script_dir, "*.XLSX")) + 
    glob.glob(os.path.join(script_dir, "*.csv")) + 
    glob.glob(os.path.join(script_dir, "*.CSV"))
)
found_files = list(set(found_files))

all_data = []
for f in found_files:
    res = veri_isle(f)
    if res is not None:
        all_data.append(res)

if all_data:
    full_df = pd.concat(all_data, ignore_index=True)

    # --- FİLTRELER (SIDEBAR) ---
    st.sidebar.header("⚙️ Analiz Ayarları")

    platform_listesi = ["Android", "iOS"]
    mevcut_platformlar = [p for p in platform_listesi if p in full_df['Platform'].unique()]
    secilen_platform = st.sidebar.selectbox("Platform Seçin:", mevcut_platformlar)

    aktif_bip_surumu = "V5.6.41" if secilen_platform == "iOS" else "V5.6.19"
    aktif_mobil_sebeke = "5G" if secilen_platform == "iOS" else "LTE"

    # --- BAŞLIK VE AÇIKLAMA (SEÇİLEN PLATFORMA GÖRE SÜRÜM GÖSTERİMİ) ---
    st.title(f"🚀 BiP ({aktif_bip_surumu}) vs WhatsApp Dosya İndirme & Yükleme Performansı Analiz Paneli")
    st.markdown(f"""
        Bu panelde **BiP (Sürüm: {aktif_bip_surumu})** ve **WhatsApp** uygulamalarının {aktif_mobil_sebeke} ve Wifi şebekeleri üzerindeki 
        farklı dosya türlerinin (SD/HD Fotoğraf, SD/HD 2dk Video, MP4, PDF, ZIP, RAR, Excel, TXT vb.) indirme/yükleme performansları ve süreleri analiz edilir.
    """)

    # --- CİHAZ VE NUMARA BİLGİLERİ (ANA SAYFA) ---
    col_up, col_down = st.columns(2)
    if secilen_platform == "iOS":
        with col_up:
            st.info("📤 **Yükleme (Upload) Yapan Cihaz:**\n- **Numara:** `05396340104` \n- **Model:** iPhone 16 Pro Max")
        with col_down:
            st.success("📥 **İndirme (Download) Yapan Cihaz:**\n- **Numara:** `05396341373` \n- **Model:** iPhone 15 Pro Max")
    else:
        with col_up:
            st.info("📤 **Yükleme (Upload) Yapan Cihaz:**\n- **Numara:** `+905316892026` \n- **Model:** Galaxy S21 FE 5G")
        with col_down:
            st.success("📥 **İndirme (Download) Yapan Cihaz:**\n- **Numara:** `+905360301821` \n- **Model:** Galaxy A51")

    st.markdown("---")

    platform_df = full_df[full_df['Platform'] == secilen_platform].copy()

    sebeke_listesi = sorted(platform_df['Şebeke'].unique())
    secilen_sebeke = st.sidebar.selectbox("Şebeke Türü Seçin:", sebeke_listesi)

    islem_listesi = sorted(platform_df['İşlem Türü'].unique())
    secilen_islem = st.sidebar.selectbox("İşlem Türü Seçin:", islem_listesi)

    tur_listesi = sorted(platform_df['Medya Türü'].unique())
    secilen_tur = st.sidebar.selectbox("Dosya / Medya Türü Seçin:", tur_listesi)

    mevcut_gruplar = sorted(platform_df['Grup'].unique())
    secilen_gruplar = st.sidebar.multiselect("Grafikte Gösterilecek Uygulamalar/Versiyonlar:", mevcut_gruplar, default=mevcut_gruplar)

    plot_df = platform_df[
        (platform_df['Şebeke'] == secilen_sebeke) &
        (platform_df['İşlem Türü'] == secilen_islem) &
        (platform_df['Medya Türü'] == secilen_tur) & 
        (platform_df['Grup'].isin(secilen_gruplar))
    ].copy()

    if not plot_df.empty:
        if secilen_tur in NUMBERED_MEDYA_TURLERI:
            plot_df = plot_df.sort_values(by=['Koşum Sırası', 'Grup'])
            x_ekseni = 'Grafik Etiketi'
            kategori_sralama = [f"{i}. Koşum" for i in sorted(plot_df['Koşum Sırası'].unique())]
            x_eksen_basligi = 'Koşum Sırası'
        else:
            def _dosya_boyut_anahtari(etiket):
                m = re.search(r'(\d+(?:\.\d+)?)', str(etiket))
                return float(m.group(1)) if m else 0.0

            plot_df['_sira_mb'] = plot_df['Grafik Etiketi'].apply(_dosya_boyut_anahtari)
            plot_df = plot_df.sort_values(by=['_sira_mb', 'Boyut (Bytes)', 'Test Adı', 'Grup'])
            x_ekseni = 'Grafik Etiketi'
            kategori_sralama = list(dict.fromkeys(plot_df['Grafik Etiketi'].tolist()))
            x_eksen_basligi = 'Dosya Boyutu (MB)'

        # --- METRİKLER (BIP VE WHATSAPP AYRI AYRI) ---
        st.subheader("⏱️ Ortalama Süreler Özeti")
        col1, col2 = st.columns(2)

        bip_df = plot_df[plot_df['Uygulama'] == 'BiP']
        wa_df = plot_df[plot_df['Uygulama'] == 'WhatsApp']

        if not bip_df.empty:
            bip_ort = bip_df['Süre'].mean()
            col1.metric(f"BiP ({aktif_bip_surumu}) Ortalama {secilen_islem} Süresi", f"{bip_ort:.2f} sn")
        else:
            col1.metric(f"BiP ({aktif_bip_surumu}) Ortalama {secilen_islem} Süresi", "-")

        if not wa_df.empty:
            wa_ort = wa_df['Süre'].mean()
            col2.metric(f"WhatsApp Ortalama {secilen_islem} Süresi", f"{wa_ort:.2f} sn")
        else:
            col2.metric(f"WhatsApp Ortalama {secilen_islem} Süresi", "-")

        st.markdown("---")

        # PowerPoint sunumu renk paleti (#1587CB BiP Mavisi & #25D366 WhatsApp Yeşili / #10B5B1 Turkuaz)
        color_map = {
            'WhatsApp': '#25D366',
            'BiP (V5.6.19)': '#1587CB',
            'BiP (V5.6.41)': '#1587CB'
        }

        # --- GRAFİK (POWERPOINT GÖRSEL FORMATI) ---
        islem_baslik = "İndirme (Download)" if secilen_islem == "Download" else "Yükleme (Upload)"
        st.subheader(f"📊 {secilen_tur} — {secilen_sebeke} {secilen_islem} Performansı Kıyaslaması")

        max_y = float(plot_df['Süre'].max()) if not plot_df['Süre'].empty else 1.0
        ust_sinir = max(max_y * 1.22, 0.5)

        fig = px.bar(
            plot_df, x=x_ekseni, y='Süre', color='Grup',
            barmode='group', text='Süre',
            hover_data=['Boyut (MB)', 'Boyut (Bytes)', 'Speedtest (Mbps)'],
            category_orders={
                "Grup": mevcut_gruplar,
                x_ekseni: kategori_sralama
            },
            color_discrete_map=color_map,
            labels={'Süre': 'Süre (sn)', 'Grup': 'Uygulama / Sürüm', x_ekseni: x_eksen_basligi}
        )

        fig.update_traces(
            texttemplate='%{y:.2f}',
            textposition='outside',
            cliponaxis=False,
            textfont=dict(size=12, color='#192F47', family='Arial, sans-serif'),
            marker_line_color='#FFFFFF',
            marker_line_width=1.0
        )

        fig.update_layout(
            plot_bgcolor='#FFFFFF',
            paper_bgcolor='#F9FCFE',
            font=dict(family='Arial, sans-serif', size=13, color='#192F47'),
            bargap=0.25,
            bargroupgap=0.12,
            height=480,
            margin=dict(l=60, r=30, t=55, b=65),
            legend=dict(
                title_text='',
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1.0,
                bgcolor='rgba(255,255,255,0.85)',
                bordercolor='#CBD5E1',
                borderwidth=1,
                font=dict(size=12, color='#192F47')
            ),
            xaxis=dict(
                title=dict(text=x_eksen_basligi, font=dict(size=13, color='#192F47')),
                showgrid=False,
                showline=True,
                linecolor='#192F47',
                linewidth=1.5,
                ticks='outside',
                tickcolor='#192F47',
                tickfont=dict(size=12, color='#192F47')
            ),
            yaxis=dict(
                title=dict(text='Süre (sn)', font=dict(size=13, color='#192F47')),
                range=[0, ust_sinir],
                showgrid=True,
                gridcolor='#CBD5E1',
                gridwidth=1,
                zeroline=True,
                zerolinecolor='#192F47',
                zerolinewidth=1.5,
                showline=True,
                linecolor='#192F47',
                linewidth=1.5,
                ticks='outside',
                tickcolor='#192F47',
                tickfont=dict(size=12, color='#192F47')
            )
        )

        st.plotly_chart(fig, use_container_width=True)
        st.caption("Süre: saniye (sn)  |  Dosya boyutları küçükten büyüğe sıralıdır  |  Tekrarlanan MB ölçümleri ayrı tutulmuştur")

        st.info(performans_yorumu(plot_df, 'Süre', secilen_islem, secilen_sebeke))

        # --- TABLOLAR ---
        with st.expander("📌 Uygulama Bazlı Ortalama Süreler Tablosu"):
            summary_df = plot_df.groupby(['Grup']).agg(
                Ortalama_Süre_sn=('Süre', 'mean'),
                Ortalama_Boyut_MB=('Boyut (MB)', 'mean'),
                Koşum_Sayısı=('Süre', 'count')
            ).reset_index()

            summary_df['Ortalama_Süre_sn'] = summary_df['Ortalama_Süre_sn'].round(2)
            summary_df['Ortalama_Boyut_MB'] = summary_df['Ortalama_Boyut_MB'].round(4)

            summary_df.columns = ['Uygulama/Grup', 'Ortalama Süre (sn)', 'Ortalama Boyut (MB)', 'Toplam Veri']
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

        with st.expander("📊 Filtrelenmiş Tüm Veri Tablosu (Dosya Büyüklükleri Dahil)"):
            tablo_df = plot_df[['Test Adı', 'Süre', 'Boyut (MB)', 'Boyut (Bytes)', 'Speedtest (Mbps)', 'Grup', 'İşlem Türü', 'Şebeke']].copy()
            tablo_df.rename(columns={'Süre': 'Süre (sn)'}, inplace=True)
            st.dataframe(tablo_df, use_container_width=True, hide_index=True)
    else:
        st.warning("Seçilen kriterlere uygun veri bulunamadı. Lütfen sol menüden farklı kombinasyonlar deneyin.")
else:
    st.error(f"❌ '{script_dir}' klasöründe geçerli Excel (.xlsx) veya CSV dosyaları bulunamadı! Lütfen dosyaların script ile aynı dizinde olduğundan emin olun.")
