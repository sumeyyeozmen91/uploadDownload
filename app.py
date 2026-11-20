import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob
import re

# Sayfa ayarları
st.set_page_config(page_title="BiP & WhatsApp Performans Karşılaştırması", layout="wide")

# --- SABİTLER ---
# Veri klasörleri: Bip_Android_<sürüm> ve Bip_iOS_<sürüm>. Her klasörde hem BiP hem WhatsApp ("_Wa_") dosyaları,
# her biri için hem LTE hem Wi-Fi ölçümleri bulunur. Dosya adı kalıbı:
#   <MEDYA>[_Wa][_iOS]_<Upload|Download>_<Lte|Wifi>.xlsx   (ör. HD_2DkVideo_Wa_iOS_Upload_Lte.xlsx)
MEDYA_TURU_ISIMLERI = {
    "hd_2dkvideo": "HD 2dk Video",
    "hd_photo": "HD Fotoğraf",
    "sd_2dkvideo": "SD 2dk Video",
    "sd_photo": "SD Fotoğraf",
    "mp4": "MP4 Video",
    "pdf": "PDF Belge",
    "rar": "RAR Arşiv",
    "txt": "TXT Metin",
    "xlsx": "XLSX Tablo",
    "zip": "ZIP Arşiv",
}
NUMBERED_PREFIXES = {"sd_photo", "sd_2dkvideo", "hd_photo", "hd_2dkvideo"}
NUMBERED_MEDYA_TURLERI = {MEDYA_TURU_ISIMLERI[p] for p in NUMBERED_PREFIXES}

SEBEKE_ISIMLERI = {"lte": "LTE", "wifi": "Wi-Fi"}
SEBEKE_SIRASI = ["Wi-Fi", "LTE"]
PLATFORM_SIRASI = ["Android", "iOS"]

DOSYA_DESENI = re.compile(
    r"^(?P<medya>" + "|".join(sorted(MEDYA_TURU_ISIMLERI, key=len, reverse=True)) + r")"
    r"(?P<etiketler>(?:_wa|_ios)*)_(?P<islem>upload|download)_(?P<sebeke>lte|wifi)$"
)
KLASOR_DESENI = re.compile(r"bip_(android|ios)_([\d.]+)", re.IGNORECASE)


def _sayiya_cevir(seri):
    temiz = seri.astype(str).str.replace(',', '.', regex=False).str.extract(r'(\d+(?:\.\d+)?)')[0]
    return pd.to_numeric(temiz, errors='coerce')


def speed_test_oku(seri):
    """Speed Test sütunundaki ilk geçerli değeri Mbps olarak döndürür (ör. '52.4Mbps' -> 52.4)."""
    for deger in seri.dropna():
        metin = str(deger).strip().lower().replace(',', '.')
        m = re.search(r'(\d+(?:\.\d+)?)', metin)
        if m:
            sayi = float(m.group(1))
            if 'gbps' in metin:
                sayi *= 1000
            elif 'kbps' in metin:
                sayi /= 1000
            return sayi
    return None


def veri_isle(file_path):
    try:
        base_name = os.path.splitext(os.path.basename(file_path))[0].lower().strip()
        eslesme = DOSYA_DESENI.match(base_name)
        if not eslesme:
            return None

        matched_prefix = eslesme.group('medya')
        etiketler = eslesme.group('etiketler')
        is_wa = "_wa" in etiketler
        islem_turu = "Upload" if eslesme.group('islem') == "upload" else "Download"
        network = SEBEKE_ISIMLERI[eslesme.group('sebeke')]

        # Platform ve BiP sürümü klasör adından (Bip_Android_5.6.19 / Bip_iOS_5.6.41) okunur
        klasor = os.path.basename(os.path.dirname(file_path))
        klasor_eslesme = KLASOR_DESENI.search(klasor)
        if klasor_eslesme:
            platform = "iOS" if klasor_eslesme.group(1).lower() == "ios" else "Android"
            bip_surum = f"V{klasor_eslesme.group(2)}"
        else:
            platform = "iOS" if "_ios" in etiketler else "Android"
            bip_surum = "-"

        df = pd.read_excel(file_path) if file_path.lower().endswith(('.xlsx', '.xls')) else pd.read_csv(file_path)
        if df.empty or len(df.columns) < 2:
            return None

        df.columns = [str(c).strip() for c in df.columns]
        df = df.rename(columns={df.columns[0]: 'Test Adı'})

        # Süre her zaman 2. sütundadır (başlığı bazı Download dosyalarında da "Yükleme Süresi" yazılı);
        # değerler saniye (sn) cinsindendir.
        df['Süre'] = _sayiya_cevir(df[df.columns[1]]).round(2)

        size_col = next((c for c in df.columns if "boyut" in c.lower() or "size" in c.lower()), None)
        speed_col = next((c for c in df.columns if "speed" in c.lower()), None)

        df['Boyut (MB)'] = _sayiya_cevir(df[size_col]).fillna(0).round(2) if size_col else 0.0
        speed_mbps = speed_test_oku(df[speed_col]) if speed_col else None
        df['Speed Test (Mbps)'] = speed_mbps

        df = df.dropna(subset=['Süre'])
        df = df[df['Test Adı'].notna()]
        if df.empty:
            return None

        # --- KOŞUM SIRASI ---
        is_numbered_media = matched_prefix in NUMBERED_PREFIXES
        if is_numbered_media:
            sira = df['Test Adı'].astype(str).str.extract(r'^\s*(\d+)')[0]
            df['Koşum Sırası'] = pd.to_numeric(sira, errors='coerce')
            if df['Koşum Sırası'].isna().any() or df['Koşum Sırası'].nunique() < len(df):
                df['Koşum Sırası'] = range(1, len(df) + 1)
            df['Koşum Sırası'] = df['Koşum Sırası'].astype(int)
            df['Grafik Etiketi'] = df['Koşum Sırası'].astype(str) + ". Koşum"
        else:
            df['Koşum Sırası'] = 0
            df['Grafik Etiketi'] = df['Test Adı'].astype(str)

        app_name = "WhatsApp" if is_wa else "BiP"
        df['Platform'] = platform
        df['Uygulama'] = app_name
        df['Versiyon'] = "Güncel" if is_wa else bip_surum
        df['Grup'] = "WhatsApp" if is_wa else f"BiP ({bip_surum})"
        df['Şebeke'] = network
        df['Medya Türü'] = MEDYA_TURU_ISIMLERI[matched_prefix]
        df['İşlem Türü'] = islem_turu
        df['Kaynak Dosya'] = os.path.relpath(file_path, script_dir)

        return df[['Test Adı', 'Koşum Sırası', 'Grafik Etiketi', 'Süre', 'Boyut (MB)', 'Speed Test (Mbps)',
                   'Platform', 'Uygulama', 'Versiyon', 'Grup', 'Şebeke', 'Medya Türü', 'İşlem Türü', 'Kaynak Dosya']]
    except Exception:
        return None


# --- ÇALIŞMA DİZİNİ VE DOSYA TARAMA ---
script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

found_files = set()
for uzanti in ("xlsx", "XLSX", "csv", "CSV"):
    found_files.update(glob.glob(os.path.join(script_dir, "**", f"*.{uzanti}"), recursive=True))

all_data = [res for res in (veri_isle(f) for f in sorted(found_files)) if res is not None]

if not all_data:
    st.error(f"❌ '{script_dir}' altında (Bip_Android_* / Bip_iOS_* klasörleri) geçerli Excel (.xlsx) veya CSV dosyası bulunamadı!")
    st.stop()

full_df = pd.concat(all_data, ignore_index=True)

# BiP sürümleri (başlık ve renkler için)
bip_surumleri = (
    full_df[full_df['Uygulama'] == 'BiP'].groupby('Platform')['Versiyon'].first().to_dict()
)
and_surum = bip_surumleri.get("Android", "-")
ios_surum = bip_surumleri.get("iOS", "-")

# --- FİLTRELER (SIDEBAR) ---
st.sidebar.header("⚙️ Analiz Ayarları")

tur_listesi = sorted(full_df['Medya Türü'].unique())
varsayilan_tur_idx = tur_listesi.index("SD 2dk Video") if "SD 2dk Video" in tur_listesi else 0
secilen_tur = st.sidebar.selectbox("Dosya / Medya Türü Seçin:", tur_listesi, index=varsayilan_tur_idx)

uygulama_listesi = ["BiP", "WhatsApp"]
secilen_uygulamalar = st.sidebar.multiselect(
    "Grafikte Gösterilecek Uygulamalar:", uygulama_listesi, default=uygulama_listesi
)

# --- BAŞLIK VE CİHAZ BİLGİLERİ ---
st.title(f"🚀 BiP vs WhatsApp — {secilen_tur} Performans Analiz Paneli")
st.markdown(
    f"**{secilen_tur}** için **Android (BiP {and_surum} & WhatsApp)** ve **iOS (BiP {ios_surum} & WhatsApp)** "
    f"platformlarında **Wi-Fi** ve **LTE** şebekelerinde **Upload / Download** süreleri ve test anındaki **Speed Test** değerleri."
)

col_and_info, col_ios_info = st.columns(2)
with col_and_info:
    st.info(
        f"🤖 **Android Test Cihazları (BiP {and_surum} & WhatsApp)**\n"
        "- 📤 **Upload:** `Galaxy S21 FE 5G` (`+905316892026`)\n"
        "- 📥 **Download:** `Galaxy A51` (`+905360301821`)"
    )
with col_ios_info:
    st.success(
        f"🍎 **iOS Test Cihazları (BiP {ios_surum} & WhatsApp)**\n"
        "- 📤 **Upload:** `iPhone 16 Pro Max` (`05396340104`)\n"
        "- 📥 **Download:** `iPhone 15 Pro Max` (`05396341373`)"
    )

st.caption("Süre: saniye (sn)  |  Speed Test: ilgili testin başında ölçülen hat hızı (Mbps)  |  Her senaryo 10 koşum")
st.markdown("---")

tur_df_tum = full_df[full_df['Medya Türü'] == secilen_tur].copy()
tur_df = tur_df_tum[tur_df_tum['Uygulama'].isin(secilen_uygulamalar)].copy()

color_map = {'WhatsApp': '#25D366'}
color_map.update({g: '#1587CB' for g in full_df['Grup'].unique() if g.startswith('BiP')})


def senaryo_df(df, platform_adi, sebeke_adi, islem_adi):
    return df[
        (df['Platform'] == platform_adi) &
        (df['Şebeke'] == sebeke_adi) &
        (df['İşlem Türü'] == islem_adi)
    ]


def _ort_str(seri):
    return f"{seri.mean():.2f} sn" if not seri.empty else "-"


def _speed_str(seri):
    seri = seri.dropna()
    return f"{seri.iloc[0]:.1f} Mbps" if not seri.empty else "-"


def tek_grafik_ciz(container, platform_adi, sebeke_adi, islem_adi, grafik_key):
    sub_df = senaryo_df(tur_df, platform_adi, sebeke_adi, islem_adi).copy()
    if sub_df.empty:
        return

    with container:
        baslik_renk = "#10B5B1" if platform_adi == "iOS" else "#1587CB"
        st.markdown(
            f"<h4 style='color:{baslik_renk}; margin-bottom:4px; font-family:Arial,sans-serif;'>"
            f"{platform_adi} · {sebeke_adi} {islem_adi}</h4>",
            unsafe_allow_html=True
        )

        # --- ORTALAMA SÜRELER + SPEED TEST (UYGULAMA BAZLI) ---
        bip_sub = sub_df[sub_df['Uygulama'] == 'BiP']
        wa_sub = sub_df[sub_df['Uygulama'] == 'WhatsApp']
        bip_surum = bip_sub['Versiyon'].iloc[0] if not bip_sub.empty else ""

        mcol1, mcol2, mcol3, mcol4 = st.columns(4)
        mcol1.metric(f"BiP {bip_surum} Ort. {islem_adi}", _ort_str(bip_sub['Süre']))
        mcol2.metric("BiP Speed Test", _speed_str(bip_sub['Speed Test (Mbps)']))
        mcol3.metric(f"WhatsApp Ort. {islem_adi}", _ort_str(wa_sub['Süre']))
        mcol4.metric("WhatsApp Speed Test", _speed_str(wa_sub['Speed Test (Mbps)']))

        if secilen_tur in NUMBERED_MEDYA_TURLERI:
            sub_df = sub_df.sort_values(by=['Koşum Sırası', 'Grup'])
            kategori_sralama = [f"{i}. Koşum" for i in sorted(sub_df['Koşum Sırası'].unique())]
            x_eksen_basligi = 'Koşum Sırası'
        else:
            sub_df = sub_df.sort_values(by=['Boyut (MB)', 'Test Adı', 'Grup'])
            kategori_sralama = list(dict.fromkeys(sub_df['Grafik Etiketi'].tolist()))
            x_eksen_basligi = 'Dosya'

        max_y = float(sub_df['Süre'].max()) if not sub_df['Süre'].empty else 1.0
        ust_sinir = max(max_y * 1.24, 0.5)

        hover = ['Speed Test (Mbps)'] + (['Boyut (MB)'] if (sub_df['Boyut (MB)'] > 0).any() else [])
        fig = px.bar(
            sub_df, x='Grafik Etiketi', y='Süre', color='Grup',
            barmode='group', text='Süre',
            hover_data=hover,
            category_orders={"Grup": sorted(sub_df['Grup'].unique()), 'Grafik Etiketi': kategori_sralama},
            color_discrete_map=color_map,
            labels={'Süre': 'Süre (sn)', 'Grup': 'Uygulama / Sürüm', 'Grafik Etiketi': x_eksen_basligi}
        )
        fig.update_traces(
            texttemplate='%{y:.2f}', textposition='outside', cliponaxis=False,
            textfont=dict(size=11, color='#192F47', family='Arial, sans-serif'),
            marker_line_color='#FFFFFF', marker_line_width=1.0
        )
        eksen_stili = dict(showline=True, linecolor='#192F47', linewidth=1.5, ticks='outside',
                           tickcolor='#192F47', tickfont=dict(size=11, color='#192F47'))
        fig.update_layout(
            plot_bgcolor='#FFFFFF', paper_bgcolor='#F9FCFE',
            font=dict(family='Arial, sans-serif', size=12, color='#192F47'),
            bargap=0.25, bargroupgap=0.12, height=360,
            margin=dict(l=50, r=20, t=40, b=50),
            legend=dict(title_text='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1.0,
                        bgcolor='rgba(255,255,255,0.85)', bordercolor='#CBD5E1', borderwidth=1,
                        font=dict(size=11, color='#192F47')),
            xaxis=dict(title=dict(text=x_eksen_basligi, font=dict(size=12, color='#192F47')),
                       showgrid=False, **eksen_stili),
            yaxis=dict(title=dict(text='Süre (sn)', font=dict(size=12, color='#192F47')),
                       range=[0, ust_sinir], showgrid=True, gridcolor='#CBD5E1', gridwidth=1,
                       zeroline=True, zerolinecolor='#192F47', zerolinewidth=1.5, **eksen_stili)
        )
        st.plotly_chart(fig, use_container_width=True, key=grafik_key)


# =========================================================================
# GRAFİKLER: HER ŞEBEKE İÇİN (Wi-Fi, LTE) ÜST SATIR ANDROID U/D, ALT SATIR iOS U/D
# =========================================================================
SEBEKE_IKON = {"Wi-Fi": "📶", "LTE": "📡"}
for sebeke in SEBEKE_SIRASI:
    platformlar = [p for p in PLATFORM_SIRASI
                   if not senaryo_df(tur_df, p, sebeke, "Upload").empty
                   or not senaryo_df(tur_df, p, sebeke, "Download").empty]
    if not platformlar:
        continue
    st.subheader(f"{SEBEKE_IKON[sebeke]} BiP & WhatsApp {sebeke} | {secilen_tur} Upload / Download")
    for plat in platformlar:
        c1, c2 = st.columns(2)
        tek_grafik_ciz(c1, plat, sebeke, "Upload", f"chart_{plat}_{sebeke}_up")
        tek_grafik_ciz(c2, plat, sebeke, "Download", f"chart_{plat}_{sebeke}_down")
    st.markdown("---")


# =========================================================================
# YÖNETİCİ ÖZETİ (KISA, ÖZ, NET)
# =========================================================================
def yonetici_ozeti_ciz(df_tur, medya_adi):
    karsilastirmalar = []
    for islem in ["Upload", "Download"]:
        for plat in PLATFORM_SIRASI:
            for seb in SEBEKE_SIRASI:
                s_df = senaryo_df(df_tur, plat, seb, islem)
                bip = s_df[s_df['Uygulama'] == 'BiP']
                wa = s_df[s_df['Uygulama'] == 'WhatsApp']
                if bip.empty or wa.empty:
                    continue
                b, w = bip['Süre'].mean(), wa['Süre'].mean()
                karsilastirmalar.append({
                    'islem': islem, 'plat': plat, 'seb': seb, 'bip': b, 'wa': w,
                    'bip_hizli': b < w,
                    'oran': (max(b, w) / min(b, w) - 1) * 100 if min(b, w) > 0 else 0.0,
                    'bip_st': bip['Speed Test (Mbps)'].dropna().iloc[0] if bip['Speed Test (Mbps)'].notna().any() else None,
                    'wa_st': wa['Speed Test (Mbps)'].dropna().iloc[0] if wa['Speed Test (Mbps)'].notna().any() else None,
                })

    if not karsilastirmalar:
        st.info("Yönetici özeti için BiP ve WhatsApp verisinin birlikte bulunduğu senaryo yok.")
        return

    toplam = len(karsilastirmalar)
    bip_kazanc = sum(k['bip_hizli'] for k in karsilastirmalar)

    def fark_str(oran):
        # %100 ve üzeri farklar kat olarak gösterilir (ör. %1046 -> 11.5x)
        return f"{oran / 100 + 1:.1f}x" if oran >= 100 else f"%{oran:.0f}"

    def islem_satiri(islem):
        parcalar = []
        for k in [k for k in karsilastirmalar if k['islem'] == islem]:
            kazanan, renk = ("BiP", "#0A6CAA") if k['bip_hizli'] else ("WhatsApp", "#1E8E3E")
            parcalar.append(
                f"{k['plat']} {k['seb']}: <span style='color:{renk}; font-weight:700;'>{kazanan} {fark_str(k['oran'])}</span>"
            )
        return " &nbsp;·&nbsp; ".join(parcalar) if parcalar else "Veri yok"

    # En kritik açık: BiP'in en çok geride kaldığı senaryo
    geride = [k for k in karsilastirmalar if not k['bip_hizli']]
    if geride:
        k = max(geride, key=lambda x: x['oran'])
        odak = (f"🎯 <b>Odak:</b> {k['plat']} {k['seb']} {k['islem']} — BiP {k['bip']:.2f} sn vs "
                f"WhatsApp {k['wa']:.2f} sn ({fark_str(k['oran'])} yavaş).")
    else:
        odak = "🎯 <b>Odak:</b> BiP tüm senaryolarda önde; mevcut performans korunmalı."

    # Speed Test uyarısı: BiP ve WhatsApp testleri arasında hat hızı 1.5 katından fazla farklıysa
    farkli_hat = [k for k in karsilastirmalar
                  if k['bip_st'] and k['wa_st'] and max(k['bip_st'], k['wa_st']) / min(k['bip_st'], k['wa_st']) > 1.5]
    if farkli_hat:
        uyari = (f"⚠️ <b>{len(farkli_hat)} senaryoda hat hızı farkı &gt;1.5x</b> (kıyas ihtiyatla okunmalı): "
                 + ", ".join(f"{k['plat']} {k['seb']} {'UL' if k['islem'] == 'Upload' else 'DL'} "
                             f"({k['bip_st']:.0f}/{k['wa_st']:.0f} Mbps)" for k in farkli_hat))
    else:
        uyari = "✅ BiP ve WhatsApp testleri benzer hat hızlarında yapılmıştır."

    ozet_html = f"""
    <div style="background-color:#F9FCFE; border:1px solid #E2E8F0; border-radius:16px; padding:20px 26px; margin:8px 0 20px 0; font-family:Arial, sans-serif; color:#233545;">
        <div style="color:#0D65A1; font-size:22px; font-weight:700; margin-bottom:10px;">Yönetici Özeti | {medya_adi}</div>
        <div style="font-size:17px; margin-bottom:12px;">
            BiP <b>{bip_kazanc}/{toplam}</b> senaryoda WhatsApp'tan daha hızlı.
        </div>
        <ul style="font-size:14.5px; line-height:1.7; margin:0 0 10px 18px; padding:0;">
            <li><b>📤 Upload:</b> {islem_satiri("Upload")}</li>
            <li><b>📥 Download:</b> {islem_satiri("Download")}</li>
        </ul>
        <div style="font-size:14px; line-height:1.6;">{odak}<br>{uyari}</div>
        <div style="font-size:12px; color:#64748B; margin-top:8px;">% / x: kazananın ortalama süre avantajı · Mbps: BiP/WhatsApp Speed Test · UL: Upload, DL: Download</div>
    </div>
    """
    st.markdown(ozet_html, unsafe_allow_html=True)


yonetici_ozeti_ciz(tur_df_tum, secilen_tur)

# --- TABLOLAR ---
if not tur_df.empty:
    with st.expander(f"📌 {secilen_tur} — Senaryo Bazlı Ortalama Süre ve Speed Test Tablosu"):
        summary_df = tur_df.groupby(['Platform', 'Şebeke', 'İşlem Türü', 'Grup']).agg(
            ort_sure=('Süre', 'mean'),
            speed=('Speed Test (Mbps)', 'first'),
            boyut=('Boyut (MB)', 'mean'),
            kosum=('Süre', 'count')
        ).reset_index()
        summary_df['ort_sure'] = summary_df['ort_sure'].round(2)
        summary_df['boyut'] = summary_df['boyut'].round(2)
        summary_df.columns = ['Platform', 'Şebeke', 'İşlem Türü', 'Uygulama/Grup', 'Ortalama Süre (sn)',
                              'Speed Test (Mbps)', 'Dosya Boyutu (MB)', 'Koşum Sayısı']
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

    with st.expander(f"📊 {secilen_tur} — Tüm Veri Tablosu"):
        tablo_df = tur_df[['Platform', 'Şebeke', 'İşlem Türü', 'Grup', 'Test Adı', 'Süre', 'Boyut (MB)',
                           'Speed Test (Mbps)', 'Kaynak Dosya']].rename(columns={'Süre': 'Süre (sn)'})
        st.dataframe(tablo_df, use_container_width=True, hide_index=True)
