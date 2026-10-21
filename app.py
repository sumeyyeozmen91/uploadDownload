import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob
import re

# Sayfa ayarları
st.set_page_config(page_title="BiP (V5.6.19) & WhatsApp Performans Karşılaştırması", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP (V5.6.19) vs WhatsApp Dosya İndirme & Yükleme Performansı Analiz Paneli")
st.markdown("""
    Bu panelde **BiP (Sürüm: V5.6.19)** ve **WhatsApp** uygulamalarının LTE ve Wifi şebekeleri üzerindeki 
    farklı dosya türlerinin (Fotoğraf, Video, PDF, ZIP, RAR, Excel, TXT vb.) indirme/yükleme performansları ve süreleri analiz edilir.
""")

# --- CİHAZ VE NUMARA BİLGİLERİ (ANA SAYFA) ---
col_up, col_down = st.columns(2)
with col_up:
    st.info("📤 **Yükleme (Upload) Yapan Cihaz:**\n- **Numara:** `+905316892026` \n- **Model:** Galaxy S21 FE 5G")
with col_down:
    st.success("📥 **İndirme (Download) Yapan Cihaz:**\n- **Numara:** `+905360301821` \n- **Model:** Galaxy A51")

st.markdown("---")

# --- İZİN VERİLEN DOSYA LİSTESİ (DİNAMİK ÜRETİM) ---
PREFIXES = ["mp4", "pdf", "rar", "sd_2dkvideo", "sd_photo", "txt", "xlsx", "zip"]
NETWORKS = ["lte", "wifi"]
OPERATIONS = ["download", "upload"]

ALLOWED_FILES = set()
for p in PREFIXES:
    for op in OPERATIONS:
        for net in NETWORKS:
            ALLOWED_FILES.add(f"{p}_{op}_{net}")
            ALLOWED_FILES.add(f"{p}_wa_{op}_{net}")

MEDYA_TURU_ISIMLERI = {
    "mp4": "MP4 Video",
    "pdf": "PDF Belge",
    "rar": "RAR Arşiv",
    "sd_2dkvideo": "SD 2dk Video",
    "sd_photo": "SD Fotoğraf",
    "txt": "TXT Metin",
    "xlsx": "XLSX Tablo",
    "zip": "ZIP Arşiv"
}

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

        is_wa = "_wa_" in base_name
        is_upload = "_upload_" in base_name
        is_wifi = "_wifi" in base_name

        matched_prefix = "diğer"
        for p in PREFIXES:
            if base_name.startswith(p + "_") or f"_{p}_" in base_name:
                matched_prefix = p
                break

        medya_kalitesi = "Standart"
        medya_turu = MEDYA_TURU_ISIMLERI.get(matched_prefix, matched_prefix.upper())
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

        # --- BOYUT ATAMALARI ---
        if is_wa and matched_prefix == "sd_2dkvideo":
            df['Boyut (MB)'] = 32.0
            df['Boyut (Bytes)'] = 32 * 1024 * 1024
        elif is_wa and matched_prefix == "sd_photo":
            if is_upload:
                df['Boyut (MB)'] = round(38 / 1024, 4)
                df['Boyut (Bytes)'] = 38 * 1024
            else:
                df['Boyut (MB)'] = round(26 / 1024, 4)
                df['Boyut (Bytes)'] = 26 * 1024
        else:
            if size_col and size_col in df.columns:
                df['Boyut (Bytes)'] = df[size_col]
                df['Boyut (MB)'] = (df[size_col] / (1024 * 1024)).round(2)
            else:
                df['Boyut (Bytes)'] = 0
                df['Boyut (MB)'] = 0.0

        df = df.dropna(subset=['Süre'])

        # --- KOŞUM / ETİKET BELİRLEME (Sadece Photo ve SD_2dkVideo için numaralandırma) ---
        is_numbered_media = matched_prefix in ["sd_photo", "sd_2dkvideo"]

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

        if is_numbered_media:
            df['Grafik Etiketi'] = df['Koşum Sırası'].astype(str) + ". Koşum"
        else:
            df['Grafik Etiketi'] = df['Test Adı'].astype(str)

        df['Uygulama'] = app_name
        df['Versiyon'] = version
        df['Şebeke'] = network
        df['Grup'] = grup_adi
        df['Medya Kalitesi'] = medya_kalitesi
        df['Medya Türü'] = medya_turu
        df['İşlem Türü'] = islem_turu
        df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'DİĞER')

        return df[['Test Adı', 'Koşum Sırası', 'Grafik Etiketi', 'Uzantı', 'Süre', 'Boyut (MB)', 'Boyut (Bytes)', 'Uygulama', 'Versiyon', 'Şebeke', 'Grup', 'Medya Kalitesi', 'Medya Türü', 'İşlem Türü']]

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
            
            bip_sec = ort_bip / 1000
            wa_sec = ort_wa / 1000
            
            if ort_bip < ort_wa:
                hiz_farki = ((ort_wa / ort_bip) - 1) * 100
                saniye_farki = (ort_wa - ort_bip) / 1000
                yorumlar.append(
                    f"- **{sebeke_turu} Şebekesinde:** **BiP** ({ort_bip:.1f} ms / {bip_sec:.2f} sn), "
                    f"WhatsApp'a ({ort_wa:.1f} ms / {wa_sec:.2f} sn) göre **{saniye_farki:.2f} saniye daha erken tamamlanarak %{hiz_farki:.1f} daha hızlıdır.** 🚀"
                )
            elif ort_wa < ort_bip:
                hiz_farki = ((ort_bip / ort_wa) - 1) * 100
                saniye_farki = (ort_bip - ort_wa) / 1000
                yorumlar.append(
                    f"- **{sebeke_turu} Şebekesinde:** **WhatsApp** ({ort_wa:.1f} ms / {wa_sec:.2f} sn), "
                    f"BiP'e ({ort_bip:.1f} ms / {bip_sec:.2f} sn) göre **{saniye_farki:.2f} saniye daha erken tamamlanarak %{hiz_farki:.1f} daha hızlıdır.** 📉"
                )
            else:
                yorumlar.append(f"- **{sebeke_turu} Şebekesinde:** BiP ve WhatsApp eşit süre kaydetmiştir ({bip_sec:.2f} sn). ⚖️")

    return "\n".join(yorumlar) if yorumlar else "Kıyaslama için yeterli veri bulunmuyor."

# --- ÇALIŞMA DİZİNİ VE DOSYA TARAMA AYARI ---
script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()

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

    sebeke_listesi = sorted(full_df['Şebeke'].unique())
    secilen_sebeke = st.sidebar.selectbox("Şebeke Türü Seçin:", sebeke_listesi)

    islem_listesi = sorted(full_df['İşlem Türü'].unique())
    secilen_islem = st.sidebar.selectbox("İşlem Türü Seçin:", islem_listesi)

    tur_listesi = sorted(full_df['Medya Türü'].unique())
    secilen_tur = st.sidebar.selectbox("Dosya / Medya Türü Seçin:", tur_listesi)

    mevcut_gruplar = sorted(full_df['Grup'].unique())
    secilen_gruplar = st.sidebar.multiselect("Grafikte Gösterilecek Uygulamalar/Versiyonlar:", mevcut_gruplar, default=mevcut_gruplar)

    plot_df = full_df[
        (full_df['Şebeke'] == secilen_sebeke) &
        (full_df['İşlem Türü'] == secilen_islem) &
        (full_df['Medya Türü'] == secilen_tur) & 
        (full_df['Grup'].isin(secilen_gruplar))
    ].copy()

    if not plot_df.empty:
        if secilen_tur in ["SD Fotoğraf", "SD 2dk Video"]:
            plot_df = plot_df.sort_values(by=['Koşum Sırası', 'Grup'])
            x_ekseni = 'Grafik Etiketi'
            kategori_sralama = [f"{i}. Koşum" for i in sorted(plot_df['Koşum Sırası'].unique())]
        else:
            plot_df = plot_df.sort_values(by=['Test Adı', 'Grup'])
            x_ekseni = 'Grafik Etiketi'
            kategori_sralama = list(plot_df['Grafik Etiketi'].unique())

        # --- METRİKLER ---
        st.subheader("⏱️ Ortalama Süreler Özeti")
        col1, col2 = st.columns(2)

        genel_ort = plot_df['Süre'].mean()
        col1.metric(f"Genel Ortalama {secilen_islem} Süresi", f"{genel_ort:.1f} ms", f"{genel_ort/1000:.2f} sn")

        bip_df = plot_df[plot_df['Uygulama'] == 'BiP']
        if not bip_df.empty:
            bip_ort = bip_df['Süre'].mean()
            col2.metric(f"BiP (V5.6.19) Ortalama Süre", f"{bip_ort:.1f} ms", f"{bip_ort/1000:.2f} sn")

        st.markdown("---")

        color_map = {
            'WhatsApp': '#25D366',
            'BiP (V5.6.19)': '#3498db'
        }

        # --- GRAFİK ---
        islem_baslik = "İndirme (Download)" if secilen_islem == "Download" else "Yükleme (Upload)"
        st.subheader(f"📊 {secilen_tur} Dosyaları ({secilen_sebeke}) - {islem_baslik} Performansı Kıyaslaması")
        
        fig = px.bar(
            plot_df, x=x_ekseni, y='Süre', color='Grup',
            barmode='group', text_auto=True,
            hover_data=['Boyut (MB)', 'Boyut (Bytes)'],
            category_orders={
                "Grup": mevcut_gruplar,
                x_ekseni: kategori_sralama
            },
            color_discrete_map=color_map,
            labels={'Süre': 'Süre (ms)', 'Grup': 'Uygulama / Sürüm', x_ekseni: 'Test Dosyası / Koşum'}
        )
        st.plotly_chart(fig, use_container_width=True)

        st.info(performans_yorumu(plot_df, 'Süre', secilen_islem, secilen_sebeke))

        # --- TABLOLAR ---
        with st.expander("📌 Uygulama Bazlı Ortalama Süreler Tablosu"):
            summary_df = plot_df.groupby(['Grup']).agg(
                Ortalama_Süre_ms=('Süre', 'mean'),
                Ortalama_Süre_sn=('Süre', lambda x: x.mean() / 1000),
                Ortalama_Boyut_MB=('Boyut (MB)', 'mean'),
                Koşum_Sayısı=('Süre', 'count')
            ).reset_index()

            summary_df['Ortalama_Süre_ms'] = summary_df['Ortalama_Süre_ms'].round(1)
            summary_df['Ortalama_Süre_sn'] = summary_df['Ortalama_Süre_sn'].round(2)
            summary_df['Ortalama_Boyut_MB'] = summary_df['Ortalama_Boyut_MB'].round(4)

            summary_df.columns = ['Uygulama/Grup', 'Ortalama Süre (ms)', 'Ortalama Süre (sn)', 'Ortalama Boyut (MB)', 'Toplam Veri']
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

        with st.expander("📊 Filtrelenmiş Tüm Veri Tablosu (Dosya Büyüklükleri Dahil)"):
            gosterilecek_sutunlar = ['Test Adı', 'Süre', 'Boyut (MB)', 'Boyut (Bytes)', 'Grup', 'İşlem Türü', 'Şebeke']
            mevcut_sutunlar = [col for col in gosterilecek_sutunlar if col in plot_df.columns]
            
            st.dataframe(plot_df[mevcut_sutunlar], use_container_width=True, hide_index=True)
    else:
        st.warning("Seçilen kriterlere uygun veri bulunamadı. Lütfen sol menüden farklı kombinasyonlar deneyin.")
else:
    st.error(f"❌ '{script_dir}' klasöründe geçerli Excel (.xlsx) veya CSV dosyaları bulunamadı! Lütfen dosyaların script ile aynı dizinde olduğundan emin olun.")
