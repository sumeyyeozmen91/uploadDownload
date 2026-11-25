import glob
import os
import re

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="BiP Upload/Download Performans Paneli", layout="wide")

# =========================================================================
# SABİTLER
# =========================================================================
# Klasörler: Bip_Android_<sürüm>, Bip_iOS_<sürüm>, Whatsapp_Android, Whatsapp_iOS
# Dosya adı kalıbı: <MEDYA>[_Wa][_iOS]_<Upload|Download>_<Lte|Wifi>.xlsx
#   (ör. HD_2DkVideo_Wa_iOS_Upload_Lte.xlsx, 90MB_PDF_Wa_Download_Lte.xlsx;
#    bazı adlarda uzantıdan önce boşluk olabilir, uygulama bilgisi klasör adından alınır)
# Medya türü listesi her karşılaştırmada o platformda bulunan dosyalardan oluşur;
# iOS klasörlerinde PDF/XLSX dosyası olmadığı için iOS karşılaştırmalarında bu türler çıkmaz.
MEDYA_TURU_ISIMLERI = {
    "sd_photo": "SD Fotoğraf",
    "hd_photo": "HD Fotoğraf",
    "sd_2dkvideo": "SD 2dk Video",
    "hd_2dkvideo": "HD 2dk Video",
    "90mb_pdf": "PDF (90 MB)",      # yalnızca Android klasörlerinde var
    "90mb_xlsx": "XLSX (90 MB)",    # yalnızca Android klasörlerinde var
}
MEDYA_SIRASI = list(MEDYA_TURU_ISIMLERI.values())
SEBEKE_ISIMLERI = {"lte": "LTE", "wifi": "Wi-Fi"}
SEBEKE_SIRASI = ["LTE", "Wi-Fi"]
SEBEKE_IKON = {"Wi-Fi": "📶", "LTE": "📡"}
PLATFORM_SIRASI = ["Android", "iOS"]
ISLEM_SIRASI = ["Upload", "Download"]
ESIT_ESIGI_YUZDE = 1.0         # |fark| bu yüzdenin altındaysa "eşit" sayılır

DOSYA_DESENI = re.compile(
    r"^(?P<medya>" + "|".join(sorted(MEDYA_TURU_ISIMLERI, key=len, reverse=True)) + r")"
    r"(?P<etiketler>(?:_wa|_ios)*)_(?P<islem>upload|download)_(?P<sebeke>lte|wifi)$"
)
KLASOR_DESENI = re.compile(
    r"^(?P<uygulama>bip|whatsapp)_(?P<platform>android|ios)(?:_(?P<surum>\d+(?:\.\d+)*))?$",
    re.IGNORECASE,
)

RENK_BIP = "#1587CB"
RENK_BIP_ESKI = "#9DB8CF"
RENK_WA = "#25D366"
KOYU = "#192F47"


# =========================================================================
# VERİ OKUMA
# =========================================================================
def _sayiya_cevir(seri):
    temiz = seri.astype(str).str.replace(',', '.', regex=False).str.extract(r'(\d+(?:\.\d+)?)')[0]
    return pd.to_numeric(temiz, errors='coerce')


def surum_anahtari(surum):
    return tuple(int(p) for p in surum.split('.'))


def dosya_oku(dosya_yolu):
    """Tek bir Excel dosyasını okur; (DataFrame, None) veya (None, hata_nedeni) döndürür."""
    ad = os.path.splitext(os.path.basename(dosya_yolu))[0].strip().lower()
    eslesme = DOSYA_DESENI.match(ad)
    if not eslesme:
        return None, "dosya adı beklenen kalıba uymuyor"

    ham = pd.read_excel(dosya_yolu)
    if ham.empty or len(ham.columns) < 2:
        return None, "dosya boş veya sütun eksik"
    ham.columns = [str(c).strip() for c in ham.columns]

    # 1. sütun: test adı, 2. sütun: süre (sn). "Dosya Boyutu" sütunu yalnızca video dosyalarında var.
    boyut_col = next((c for c in ham.columns if "boyut" in c.lower() or "size" in c.lower()), None)
    df = pd.DataFrame({
        'Test Adı': ham.iloc[:, 0],
        'Süre': _sayiya_cevir(ham.iloc[:, 1]).round(2),
        'Boyut (MB)': _sayiya_cevir(ham[boyut_col]) if boyut_col else float('nan'),
    }).dropna(subset=['Test Adı', 'Süre'])
    if df.empty:
        return None, "geçerli süre değeri yok"

    sira = pd.to_numeric(df['Test Adı'].astype(str).str.extract(r'^\s*(\d+)')[0], errors='coerce')
    if sira.isna().any() or sira.nunique() < len(df):
        sira = pd.Series(range(1, len(df) + 1), index=df.index)
    df['Koşum Sırası'] = sira.astype(int)
    df['Grafik Etiketi'] = df['Koşum Sırası'].astype(str) + ". Koşum"
    df['Medya Türü'] = MEDYA_TURU_ISIMLERI[eslesme.group('medya')]
    df['İşlem Türü'] = "Upload" if eslesme.group('islem') == "upload" else "Download"
    df['Şebeke'] = SEBEKE_ISIMLERI[eslesme.group('sebeke')]
    return df, None


@st.cache_data(show_spinner=False)
def veri_yukle(kok, _imza):
    """Kök dizindeki Bip_* / Whatsapp_* klasörlerini okur. _imza: dosya değişince önbelleği yeniler."""
    parcalar, atlananlar = [], []
    for klasor in sorted(os.listdir(kok)):
        tam_yol = os.path.join(kok, klasor)
        m = KLASOR_DESENI.match(klasor)
        if not m or not os.path.isdir(tam_yol):
            continue
        uygulama = "WhatsApp" if m.group('uygulama').lower() == "whatsapp" else "BiP"
        platform = "iOS" if m.group('platform').lower() == "ios" else "Android"
        surum = m.group('surum')
        if uygulama == "BiP" and not surum:
            atlananlar.append((klasor, "BiP klasör adında sürüm yok"))
            continue

        for dosya in sorted(glob.glob(os.path.join(tam_yol, "*.xlsx"))):
            try:
                df, hata = dosya_oku(dosya)
            except Exception as e:  # bozuk / okunamayan dosya
                df, hata = None, f"okunamadı: {e}"
            if df is None:
                atlananlar.append((os.path.relpath(dosya, kok), hata))
                continue
            df['Uygulama'] = uygulama
            df['Platform'] = platform
            df['Grup'] = f"BiP {surum}" if uygulama == "BiP" else "WhatsApp"
            df['Kaynak Dosya'] = os.path.relpath(dosya, kok)
            parcalar.append(df)

    full = pd.concat(parcalar, ignore_index=True) if parcalar else pd.DataFrame()
    return full, atlananlar


script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
imza = tuple(sorted((f, os.path.getmtime(f)) for f in glob.glob(os.path.join(script_dir, "*", "*.xlsx"))))
full_df, atlanan_dosyalar = veri_yukle(script_dir, imza)

if full_df.empty:
    st.error(f"❌ '{script_dir}' altında Bip_Android_* / Bip_iOS_* / Whatsapp_* klasörlerinde geçerli Excel dosyası bulunamadı!")
    st.stop()


# =========================================================================
# KARŞILAŞTIRMALAR (DROPDOWN SEÇENEKLERİ)
# =========================================================================
def karsilastirmalari_olustur(df):
    """Briefing'deki 4 karşılaştırma: her platform için eski BiP vs WhatsApp ve eski BiP vs yeni BiP.
    'test': değerlendirilen grup, 'ref': kıyaslandığı grup, 'sira': grafikteki gösterim sırası."""
    bip_surumleri = {
        p: sorted({g.replace("BiP ", "") for g in df[(df['Uygulama'] == 'BiP') & (df['Platform'] == p)]['Grup']},
                  key=surum_anahtari)
        for p in PLATFORM_SIRASI
    }
    wa_var = {p: ((df['Uygulama'] == 'WhatsApp') & (df['Platform'] == p)).any() for p in PLATFORM_SIRASI}

    liste = []
    for p in PLATFORM_SIRASI:
        s = bip_surumleri[p]
        if s and wa_var[p]:
            test, ref = f"BiP {s[0]}", "WhatsApp"
            liste.append({
                'ad': f"{p}: BiP {s[0]} vs WhatsApp", 'platform': p, 'test': test, 'ref': ref,
                'sira': [test, ref], 'renk': {test: RENK_BIP, ref: RENK_WA},
                'test_kisa': test, 'ref_kisa': "WhatsApp", 'ref_ablatif': "WhatsApp'tan",
            })
    for p in PLATFORM_SIRASI:
        s = bip_surumleri[p]
        if len(s) >= 2:
            ref, test = f"BiP {s[0]}", f"BiP {s[-1]}"
            liste.append({
                'ad': f"{p}: BiP {s[0]} vs BiP {s[-1]}", 'platform': p, 'test': test, 'ref': ref,
                'sira': [ref, test], 'renk': {ref: RENK_BIP_ESKI, test: RENK_BIP},
                'test_kisa': test, 'ref_kisa': ref, 'ref_ablatif': f"{s[0]} sürümünden",
            })
    return liste


karsilastirmalar = karsilastirmalari_olustur(full_df)
if not karsilastirmalar:
    st.error("❌ Karşılaştırma için gerekli klasörler bulunamadı "
             "(Bip_<platform>_<sürüm> + Whatsapp_<platform> veya platform başına iki BiP sürümü).")
    st.stop()


def senaryo_tablosu(df, k):
    """Medya × Şebeke × İşlem bazında test/ref ortalamaları ve farkları."""
    g = df.groupby(['Medya Türü', 'Şebeke', 'İşlem Türü', 'Grup']).agg(ort=('Süre', 'mean')).reset_index()
    satirlar = []
    for (medya, seb, islem), grp in g.groupby(['Medya Türü', 'Şebeke', 'İşlem Türü']):
        test = grp[grp['Grup'] == k['test']]
        ref = grp[grp['Grup'] == k['ref']]
        if test.empty or ref.empty:
            continue
        tt, rr = test.iloc[0], ref.iloc[0]
        fark = (tt['ort'] - rr['ort']) / rr['ort'] * 100 if rr['ort'] > 0 else 0.0
        durum = "eşit" if abs(fark) < ESIT_ESIGI_YUZDE else ("hızlı" if fark < 0 else "yavaş")
        kucuk = min(tt['ort'], rr['ort'])
        satirlar.append({
            'Medya Türü': medya, 'Şebeke': seb, 'İşlem Türü': islem,
            'test_ort': tt['ort'], 'ref_ort': rr['ort'],
            'fark_pct': fark, 'durum': durum,
            'oran': (max(tt['ort'], rr['ort']) / kucuk - 1) * 100 if kucuk > 0 else 0.0,
        })
    return pd.DataFrame(satirlar)


def fark_str(oran):
    # %100 ve üzeri farklar kat olarak gösterilir (ör. %1046 -> 11.5x)
    return f"{oran / 100 + 1:.1f}x" if oran >= 100 else f"%{oran:.0f}"


def sure_str(sn):
    return f"{sn:.2f} sn" if sn < 10 else f"{sn:.1f} sn"


# =========================================================================
# BAŞLIK, SEÇİMLER, CİHAZ BİLGİLERİ
# =========================================================================
st.title("🚀 BiP Fotoğraf & Video Upload / Download Performans Paneli")

sec1, sec2 = st.columns([2, 1])
secilen_ad = sec1.selectbox("Karşılaştırma seçin:", [k['ad'] for k in karsilastirmalar])
k = next(x for x in karsilastirmalar if x['ad'] == secilen_ad)
kiyas_df = full_df[(full_df['Platform'] == k['platform']) & full_df['Grup'].isin(k['sira'])]
secilen_tur = sec2.selectbox("Medya türü:", [m for m in MEDYA_SIRASI if m in set(kiyas_df['Medya Türü'])])

if atlanan_dosyalar:
    with st.sidebar.expander(f"⚠️ Atlanan {len(atlanan_dosyalar)} dosya/klasör"):
        for ad, neden in atlanan_dosyalar:
            st.caption(f"{ad} — {neden}")

if k['platform'] == "Android":
    st.info(
        "🤖 **Android Test Cihazları** · 📤 Upload: `Galaxy S21 FE 5G` (`+905316892026`) · "
        "📥 Download: `Galaxy A51` (`+905360301821`)"
    )
else:
    st.success(
        "🍎 **iOS Test Cihazları** · 📤 Upload: `iPhone 16 Pro Max` (`05396340104`) · "
        "📥 Download: `iPhone 15 Pro Max` (`05396341373`)"
    )
st.caption("Süre: saniye (sn) · Her senaryo 10 koşum")


# =========================================================================
# ORTALAMA SÜRE (+ VARSA DOSYA BOYUTU) KARTLARI VE GRAFİKLER (ŞEBEKE BAZLI)
# =========================================================================
def kpi_kart(baslik, sure, renk):
    return (
        f"<div style='border-left:5px solid {renk}; background:#F9FCFE; border-radius:8px; "
        f"padding:8px 12px; font-family:Arial,sans-serif;'>"
        f"<div style='font-size:12px; color:#64748B;'>{baslik}</div>"
        f"<div style='font-size:22px; font-weight:700; color:{KOYU}; line-height:1.3;'>{sure}</div></div>"
    )


def tek_grafik_ciz(container, df, sebeke_adi, islem_adi, grafik_key):
    sub_df = df[(df['Şebeke'] == sebeke_adi) & (df['İşlem Türü'] == islem_adi)].copy()
    if sub_df.empty:
        return

    with container:
        st.markdown(
            f"<h4 style='color:{RENK_BIP}; margin-bottom:6px; font-family:Arial,sans-serif;'>"
            f"{SEBEKE_IKON[sebeke_adi]} {sebeke_adi} · {islem_adi}</h4>",
            unsafe_allow_html=True
        )

        # --- ORTALAMA SÜRE KARTLARI ---
        ortalamalar = {}
        for grup in k['sira']:
            g = sub_df[sub_df['Grup'] == grup]
            ortalamalar[grup] = g['Süre'].mean() if not g.empty else None
        test_ort, ref_ort = ortalamalar[k['test']], ortalamalar[k['ref']]

        kolonlar = st.columns([2, 2, 1.2])
        for kol, grup in zip(kolonlar[:2], k['sira']):
            ort = ortalamalar[grup]
            kol.markdown(kpi_kart(f"{grup} · Ort. {islem_adi}", sure_str(ort) if ort is not None else "-",
                                  k['renk'][grup]), unsafe_allow_html=True)
        if test_ort is not None and ref_ort:
            fark = (test_ort - ref_ort) / ref_ort * 100
            renk = "#6B7280" if abs(fark) < ESIT_ESIGI_YUZDE else ("#1E8E3E" if fark < 0 else "#C0392B")
            kolonlar[2].markdown(
                f"<div style='background:#F9FCFE; border-radius:8px; padding:8px 10px; text-align:center; "
                f"font-family:Arial,sans-serif;'><div style='font-size:12px; color:#64748B;'>Fark ({k['test']})</div>"
                f"<div style='font-size:22px; font-weight:700; color:{renk}; line-height:1.3;'>{fark:+.0f}%</div></div>",
                unsafe_allow_html=True)

        # --- GRAFİK ---
        sub_df = sub_df.sort_values(by=['Koşum Sırası', 'Grup'])
        kategori_sralama = [f"{i}. Koşum" for i in sorted(sub_df['Koşum Sırası'].unique())]
        ust_sinir = max(float(sub_df['Süre'].max()) * 1.24, 0.5)

        fig = px.bar(
            sub_df, x='Grafik Etiketi', y='Süre', color='Grup', barmode='group', text='Süre',
            hover_data=['Boyut (MB)'] if sub_df['Boyut (MB)'].notna().any() else None,
            category_orders={"Grup": k['sira'], 'Grafik Etiketi': kategori_sralama},
            color_discrete_map=k['renk'],
            labels={'Süre': 'Süre (sn)', 'Grup': 'Uygulama / Sürüm', 'Grafik Etiketi': 'Koşum Sırası'}
        )
        fig.update_traces(
            texttemplate='%{y:.1f}', textposition='outside', cliponaxis=False,
            textfont=dict(size=10, color=KOYU, family='Arial, sans-serif'),
            marker_line_color='#FFFFFF', marker_line_width=1.0
        )
        eksen_stili = dict(showline=True, linecolor=KOYU, linewidth=1.5, ticks='outside',
                           tickcolor=KOYU, tickfont=dict(size=11, color=KOYU))
        fig.update_layout(
            plot_bgcolor='#FFFFFF', paper_bgcolor='#F9FCFE',
            font=dict(family='Arial, sans-serif', size=12, color=KOYU),
            bargap=0.25, bargroupgap=0.12, height=340,
            margin=dict(l=50, r=20, t=40, b=50),
            legend=dict(title_text='', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1.0,
                        bgcolor='rgba(255,255,255,0.85)', bordercolor='#CBD5E1', borderwidth=1,
                        font=dict(size=11, color=KOYU)),
            xaxis=dict(title=dict(text='Koşum Sırası', font=dict(size=12, color=KOYU)), showgrid=False, **eksen_stili),
            yaxis=dict(title=dict(text='Süre (sn)', font=dict(size=12, color=KOYU)),
                       range=[0, ust_sinir], showgrid=True, gridcolor='#CBD5E1', gridwidth=1,
                       zeroline=True, zerolinecolor=KOYU, zerolinewidth=1.5, **eksen_stili)
        )
        st.plotly_chart(fig, use_container_width=True, key=grafik_key)


st.markdown("---")
st.subheader(f"{k['ad']} · {secilen_tur}")
tur_df = kiyas_df[kiyas_df['Medya Türü'] == secilen_tur]
for sebeke in SEBEKE_SIRASI:
    if tur_df[tur_df['Şebeke'] == sebeke].empty:
        continue
    c1, c2 = st.columns(2, gap="large")
    for kol, islem in zip((c1, c2), ISLEM_SIRASI):
        tek_grafik_ciz(kol, tur_df, sebeke, islem, f"chart_{sebeke}_{islem}")
    st.markdown("---")

if not tur_df.empty:
    with st.expander(f"📊 {secilen_tur} — Tüm Koşum Verisi"):
        tablo_df = tur_df[['Şebeke', 'İşlem Türü', 'Grup', 'Test Adı', 'Süre',
                           'Kaynak Dosya']].rename(columns={'Süre': 'Süre (sn)'})
        st.dataframe(tablo_df, use_container_width=True, hide_index=True)


# =========================================================================
# YÖNETİCİ ÖZETİ (SAYFANIN ALTINDA — KISA, ÖZ, NET)
# =========================================================================
def yonetici_ozeti_ciz(ozet):
    if ozet.empty:
        st.info("Yönetici özeti için karşılaştırılabilir senaryo yok.")
        return

    toplam = len(ozet)
    kazanc = int((ozet['durum'] == 'hızlı').sum())
    esit = int((ozet['durum'] == 'eşit').sum())

    def sebeke_satiri(seb):
        s = ozet[ozet['Şebeke'] == seb]
        parcalar = []
        for islem in ISLEM_SIRASI:
            si = s[s['İşlem Türü'] == islem]
            if not si.empty:
                parcalar.append(f"{islem} <b>{(si['durum'] == 'hızlı').sum()}/{len(si)}</b>")
        return f"{SEBEKE_IKON[seb]} <b>{seb}:</b> " + " · ".join(parcalar)

    def senaryo_adi(r):
        return f"{r['Şebeke']} {r['İşlem Türü']}"

    satirlar = [sebeke_satiri(seb) for seb in SEBEKE_SIRASI if (ozet['Şebeke'] == seb).any()]

    hizli = ozet[ozet['durum'] == 'hızlı']
    if not hizli.empty:
        r = hizli.loc[hizli['oran'].idxmax()]
        satirlar.append(f"🏆 <b>En büyük kazanım:</b> {senaryo_adi(r)} — {sure_str(r['test_ort'])} vs "
                        f"{sure_str(r['ref_ort'])} ({fark_str(r['oran'])} hızlı)")
    yavas = ozet[ozet['durum'] == 'yavaş']
    if not yavas.empty:
        r = yavas.loc[yavas['oran'].idxmax()]
        satirlar.append(f"🎯 <b>Odak:</b> {senaryo_adi(r)} — {sure_str(r['test_ort'])} vs "
                        f"{sure_str(r['ref_ort'])} ({fark_str(r['oran'])} yavaş)")
    else:
        satirlar.append(f"🎯 <b>Odak:</b> {k['test_kisa']} geride kaldığı senaryo yok; mevcut performans korunmalı.")

    esit_notu = f" ({esit} senaryoda eşit)" if esit else ""
    maddeler = "".join(f"<li>{s}</li>" for s in satirlar)
    st.markdown(f"""
    <div style="background-color:#F9FCFE; border:1px solid #E2E8F0; border-radius:16px; padding:18px 24px; margin:8px 0 16px 0; font-family:Arial, sans-serif; color:#233545;">
        <div style="color:#0D65A1; font-size:21px; font-weight:700; margin-bottom:6px;">Yönetici Özeti | {k['ad']} · {secilen_tur}</div>
        <div style="font-size:17px; margin-bottom:10px;">{k['test_kisa']} <b>{kazanc}/{toplam}</b> senaryoda {k['ref_ablatif']} daha hızlı{esit_notu}.</div>
        <ul style="font-size:14.5px; line-height:1.75; margin:0 0 6px 18px; padding:0;">{maddeler}</ul>
        <div style="font-size:12px; color:#64748B;">Senaryo = şebeke × işlem ({secilen_tur}) · x / %: ortalama süre farkı</div>
    </div>
    """, unsafe_allow_html=True)


yonetici_ozeti_ciz(senaryo_tablosu(tur_df, k))
