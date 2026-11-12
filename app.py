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

        # iOS BiP Download verileri (ve saniye mertebesinde loglanmış <50 sn iOS BiP verileri) halihazırda saniye (sn) cinsindendir;
        # diğer tüm veriler milisaniye (ms) cinsinden olduğu için saniyeye (sn) çevrilir.
        is_already_seconds = (is_ios and not is_wa and (not is_upload or df['Süre'].max() < 50))
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

        return df[['Test Adı', 'Koşum Sırası', 'Grafik Etiketi', 'Uzantı', 'Süre', 'Boyut (MB)', 'Boyut (Bytes)', 'Platform', 'Uygulama', 'Versiyon', 'Şebeke', 'Grup', 'Medya Kalitesi', 'Medya Türü', 'İşlem Türü']]

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

    # Sadece hem BiP hem de WhatsApp verisi bulunan ortak senaryoları tut
    uygulama_sayilari = full_df.groupby(['Platform', 'Medya Türü', 'Şebeke', 'İşlem Türü'])['Uygulama'].transform('nunique')
    full_df = full_df[uygulama_sayilari >= 2].copy()

    # --- FİLTRELER (SIDEBAR) - TEK EKRANDA 8 GRAFİK İÇİN SADECE DOSYA TÜRÜ FİLTRESİ ---
    st.sidebar.header("⚙️ Analiz Ayarları")

    tur_listesi = sorted(full_df['Medya Türü'].unique())
    varsayilan_tur_idx = tur_listesi.index("SD 2dk Video") if "SD 2dk Video" in tur_listesi else 0
    secilen_tur = st.sidebar.selectbox("Dosya / Medya Türü Seçin:", tur_listesi, index=varsayilan_tur_idx)

    uygulama_listesi = ["BiP", "WhatsApp"]
    secilen_uygulamalar = st.sidebar.multiselect(
        "Grafikte Gösterilecek Uygulamalar:",
        uygulama_listesi,
        default=uygulama_listesi
    )

    # --- BAŞLIK VE CİHAZ BİLGİLERİ (POWERPOINT SLAYT ÜST BİLGİSİ FORMATI) ---
    st.title(f"🚀 BiP vs WhatsApp — {secilen_tur} Performans Analiz Paneli")
    st.markdown(
        f"**{secilen_tur}** dosya tipi için **Android (BiP V5.6.19 & WhatsApp)** ve **iOS (BiP V5.6.41 & WhatsApp)** "
        f"platformlarında **Wi-Fi** ve **LTE / 5G** şebekeleri üzerindeki **Upload / Download** performanslarının 8 grafiklik tam görünümü."
    )

    col_and_info, col_ios_info = st.columns(2)
    with col_and_info:
        st.info(
            "🤖 **Android Test Cihazları (BiP V5.6.19 & WhatsApp)**\n"
            "- 📤 **Upload:** `Galaxy S21 FE 5G` (`+905316892026`)\n"
            "- 📥 **Download:** `Galaxy A51` (`+905360301821`)"
        )
    with col_ios_info:
        st.success(
            "🍎 **iOS Test Cihazları (BiP V5.6.41 & WhatsApp)**\n"
            "- 📤 **Upload:** `iPhone 16 Pro Max` (`05396340104`)\n"
            "- 📥 **Download:** `iPhone 15 Pro Max` (`05396341373`)"
        )

    st.caption("Süre: saniye (sn)  |  Dosya boyutları küçükten büyüğe sıralıdır  |  Tekrarlanan MB ölçümleri ayrı tutulmuştur")
    st.markdown("---")

    tur_df = full_df[
        (full_df['Medya Türü'] == secilen_tur) &
        (full_df['Uygulama'].isin(secilen_uygulamalar))
    ].copy()

    color_map = {
        'WhatsApp': '#25D366',
        'BiP (V5.6.19)': '#1587CB',
        'BiP (V5.6.41)': '#1587CB'
    }

    def _dosya_boyut_anahtari(etiket):
        m = re.search(r'(\d+(?:\.\d+)?)', str(etiket))
        return float(m.group(1)) if m else 0.0

    def veri_var_mi(platform_adi, sebeke_adi, islem_adi):
        return not tur_df[
            (tur_df['Platform'] == platform_adi) &
            (tur_df['Şebeke'] == sebeke_adi) &
            (tur_df['İşlem Türü'] == islem_adi)
        ].empty

    def tek_grafik_ciz(container, platform_adi, sebeke_adi, islem_adi, baslik_etiketi, grafik_key):
        sub_df = tur_df[
            (tur_df['Platform'] == platform_adi) &
            (tur_df['Şebeke'] == sebeke_adi) &
            (tur_df['İşlem Türü'] == islem_adi)
        ].copy()

        if sub_df.empty:
            return

        with container:
            bip_surum = "V5.6.41" if platform_adi == "iOS" else "V5.6.19"
            baslik_renk = "#10B5B1" if platform_adi == "iOS" else "#1587CB"
            st.markdown(
                f"<h4 style='color:{baslik_renk}; margin-bottom:4px; font-family:Arial,sans-serif;'>"
                f"{baslik_etiketi}</h4>",
                unsafe_allow_html=True
            )

            # --- UYGULAMA BAZLI AYRI ORTALAMA SÜRELER (2 SÜTUN) ---
            mcol1, mcol2 = st.columns(2)
            bip_sub = sub_df[sub_df['Uygulama'] == 'BiP']
            wa_sub = sub_df[sub_df['Uygulama'] == 'WhatsApp']

            bip_ort_str = f"{bip_sub['Süre'].mean():.2f} sn" if not bip_sub.empty else "-"
            wa_ort_str = f"{wa_sub['Süre'].mean():.2f} sn" if not wa_sub.empty else "-"

            mcol1.metric(f"BiP ({bip_surum}) Ortalama {islem_adi}", bip_ort_str)
            mcol2.metric(f"WhatsApp Ortalama {islem_adi}", wa_ort_str)

            if secilen_tur in NUMBERED_MEDYA_TURLERI:
                sub_df = sub_df.sort_values(by=['Koşum Sırası', 'Grup'])
                x_ekseni = 'Grafik Etiketi'
                kategori_sralama = [f"{i}. Koşum" for i in sorted(sub_df['Koşum Sırası'].unique())]
                x_eksen_basligi = 'Koşum Sırası'
            else:
                sub_df['_sira_mb'] = sub_df['Grafik Etiketi'].apply(_dosya_boyut_anahtari)
                sub_df = sub_df.sort_values(by=['_sira_mb', 'Boyut (Bytes)', 'Test Adı', 'Grup'])
                x_ekseni = 'Grafik Etiketi'
                kategori_sralama = list(dict.fromkeys(sub_df['Grafik Etiketi'].tolist()))
                x_eksen_basligi = 'Dosya Boyutu (MB)'

            mevcut_gruplar = sorted(sub_df['Grup'].unique())
            max_y = float(sub_df['Süre'].max()) if not sub_df['Süre'].empty else 1.0
            ust_sinir = max(max_y * 1.24, 0.5)

            fig = px.bar(
                sub_df, x=x_ekseni, y='Süre', color='Grup',
                barmode='group', text='Süre',
                hover_data=['Boyut (MB)', 'Boyut (Bytes)'],
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
                textfont=dict(size=11, color='#192F47', family='Arial, sans-serif'),
                marker_line_color='#FFFFFF',
                marker_line_width=1.0
            )

            fig.update_layout(
                plot_bgcolor='#FFFFFF',
                paper_bgcolor='#F9FCFE',
                font=dict(family='Arial, sans-serif', size=12, color='#192F47'),
                bargap=0.25,
                bargroupgap=0.12,
                height=360,
                margin=dict(l=50, r=20, t=40, b=50),
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
                    font=dict(size=11, color='#192F47')
                ),
                xaxis=dict(
                    title=dict(text=x_eksen_basligi, font=dict(size=12, color='#192F47')),
                    showgrid=False,
                    showline=True,
                    linecolor='#192F47',
                    linewidth=1.5,
                    ticks='outside',
                    tickcolor='#192F47',
                    tickfont=dict(size=11, color='#192F47')
                ),
                yaxis=dict(
                    title=dict(text='Süre (sn)', font=dict(size=12, color='#192F47')),
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
                    tickfont=dict(size=11, color='#192F47')
                )
            )

            st.plotly_chart(fig, use_container_width=True, key=grafik_key)

    # =========================================================================
    # BÖLÜM 1: WI-FI PERFORMANSI (ÜST SATIR ANDROID U/D, ALT SATIR iOS U/D)
    # =========================================================================
    and_wifi_var = veri_var_mi("Android", "Wifi", "Upload") or veri_var_mi("Android", "Wifi", "Download")
    ios_wifi_var = veri_var_mi("iOS", "Wifi", "Upload") or veri_var_mi("iOS", "Wifi", "Download")

    if and_wifi_var or ios_wifi_var:
        st.subheader(f"📶 BiP & WhatsApp Wi-Fi | {secilen_tur} Upload / Download")
        if and_wifi_var:
            wifi_row1_col1, wifi_row1_col2 = st.columns(2)
            tek_grafik_ciz(wifi_row1_col1, "Android", "Wifi", "Upload", "Android · Wi-Fi Upload", "chart_and_wifi_up")
            tek_grafik_ciz(wifi_row1_col2, "Android", "Wifi", "Download", "Android · Wi-Fi Download", "chart_and_wifi_down")

        if ios_wifi_var:
            wifi_row2_col1, wifi_row2_col2 = st.columns(2)
            tek_grafik_ciz(wifi_row2_col1, "iOS", "Wifi", "Upload", "iOS · Wi-Fi Upload", "chart_ios_wifi_up")
            tek_grafik_ciz(wifi_row2_col2, "iOS", "Wifi", "Download", "iOS · Wi-Fi Download", "chart_ios_wifi_down")

        st.markdown("---")

    # =========================================================================
    # BÖLÜM 2: LTE / 5G PERFORMANSI (ÜST SATIR ANDROID U/D, ALT SATIR iOS U/D)
    # =========================================================================
    and_lte_var = veri_var_mi("Android", "4.5G (LTE)", "Upload") or veri_var_mi("Android", "4.5G (LTE)", "Download")
    ios_lte_var = veri_var_mi("iOS", "5G", "Upload") or veri_var_mi("iOS", "5G", "Download")

    if and_lte_var or ios_lte_var:
        st.subheader(f"📡 BiP & WhatsApp LTE / 5G | {secilen_tur} Upload / Download")
        if and_lte_var:
            lte_row1_col1, lte_row1_col2 = st.columns(2)
            tek_grafik_ciz(lte_row1_col1, "Android", "4.5G (LTE)", "Upload", "Android · 4.5G (LTE) Upload", "chart_and_lte_up")
            tek_grafik_ciz(lte_row1_col2, "Android", "4.5G (LTE)", "Download", "Android · 4.5G (LTE) Download", "chart_and_lte_down")

        if ios_lte_var:
            lte_row2_col1, lte_row2_col2 = st.columns(2)
            tek_grafik_ciz(lte_row2_col1, "iOS", "5G", "Upload", "iOS · 5G (LTE) Upload", "chart_ios_lte_up")
            tek_grafik_ciz(lte_row2_col2, "iOS", "5G", "Download", "iOS · 5G (LTE) Download", "chart_ios_lte_down")

        st.markdown("---")

    # --- TABLOLAR (8 SENARYONUN TOPLU ÖZETİ VE DETAY VERİLERİ) ---
    if not tur_df.empty:
        with st.expander(f"📌 {secilen_tur} — Tüm Senaryolar İçin Uygulama Bazlı Ortalama Süreler Tablosu"):
            summary_df = tur_df.groupby(['Platform', 'Şebeke', 'İşlem Türü', 'Grup']).agg(
                Ortalama_Süre_sn=('Süre', 'mean'),
                Ortalama_Boyut_MB=('Boyut (MB)', 'mean'),
                Koşum_Sayısı=('Süre', 'count')
            ).reset_index()

            summary_df['Ortalama_Süre_sn'] = summary_df['Ortalama_Süre_sn'].round(2)
            summary_df['Ortalama_Boyut_MB'] = summary_df['Ortalama_Boyut_MB'].round(4)

            summary_df.columns = ['Platform', 'Şebeke', 'İşlem Türü', 'Uygulama/Grup', 'Ortalama Süre (sn)', 'Ortalama Boyut (MB)', 'Toplam Veri']
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

        with st.expander(f"📊 {secilen_tur} — Tüm Veri Tablosu (Dosya Büyüklükleri Dahil)"):
            tablo_df = tur_df[['Platform', 'Şebeke', 'İşlem Türü', 'Grup', 'Test Adı', 'Süre', 'Boyut (MB)', 'Boyut (Bytes)']].copy()
            tablo_df.rename(columns={'Süre': 'Süre (sn)'}, inplace=True)
            st.dataframe(tablo_df, use_container_width=True, hide_index=True)
else:
    st.error(f"❌ '{script_dir}' klasöründe geçerli Excel (.xlsx) veya CSV dosyaları bulunamadı! Lütfen dosyaların script ile aynı dizinde olduğundan emin olun.")
