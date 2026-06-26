import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# Sayfa ayarları
st.set_page_config(page_title="BiP Versiyon Karşılaştırma Merkezi", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP Versiyon Performans Analizi")
st.markdown("""
    Bu panelde BiP uygulamasının versiyon gelişimi analiz edilir:
    * **BiP (V5.1.23) vs BiP (V5.2.6):** İki farklı sürüm arasındaki performans farkları ve iyileşme oranları.
""")

def veri_isle(file_path):
    try:
        if not os.path.exists(file_path):
            return None

        df = pd.read_excel(file_path)

        # Sütun isimlerini temizle
        df.columns = [str(c).split(' (')[0].strip() for c in df.columns]

        fname = os.path.basename(file_path).lower()

        # --- DOSYA ADI FORMATI AYRIŞTIRMA ---
        # Örn: 5.1.23_bip_4.5g_hdphoto.xlsx -> parts[0]="5.1.23", parts[2]="4.5g"
        if "_" in fname and "bip" in fname:
            parts = fname.split('_')
            version = parts[0]  # "5.1.23" veya "5.2.6"
            app_name = "BiP"
            net_raw = parts[2].replace(".xlsx", "").replace(".csv", "")
        else:
            return None  # BiP formatına uymayan dosyaları es geç

        # Şebeke ismini standartlaştır
        if "3g" in net_raw: network = "3G"
        elif "4g" in net_raw or "4.5g" in net_raw: network = "4.5G"
        elif "wifi" in net_raw: network = "Wi-Fi"
        else: network = net_raw.upper()

        # DataFrame sütunlarını doldur
        df['Uygulama'] = app_name
        df['Versiyon'] = version
        df['Şebeke'] = network
        df['Grup'] = f"BiP (V{version})"

        # Dosya uzantısı ve boyutu çıkarma
        df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'DİĞER')
        df['Boyut'] = df['Test Adı'].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x))

        return df[['Test Adı', 'Uzantı', 'Boyut', 'Yükleme Süresi', 'İndirme Süresi', 'Uygulama', 'Versiyon', 'Şebeke', 'Grup']]
    except Exception as e:
        st.error(f"⚠️ {file_path} işlenirken hata oluştu: {e}")
        return None

# --- SÜRÜM GELİŞİM YORUM MOTORU ---
def surum_gelisim_yorumu(df, metrik_kolonu, metrik_adi):
    if df.empty:
        return "Yorumlanacak veri bulunamadı."

    yorumlar = []
    
    # Mevcut verideki sürümleri tespit et ve sırala (Örn: ['5.1.23', '5.2.6'])
    bip_versions = sorted(list(set(df['Versiyon'].dropna().astype(str))))
    
    if len(bip_versions) < 2:
        return "Karşılaştırma yapabilmek için klasörde en az iki farklı BiP sürümüne ait veri olmalıdır."
        
    v_eski = bip_versions[0]
    v_yeni = bip_versions[1]

    bip_eski_df = df[df['Versiyon'] == v_eski]
    bip_yeni_df = df[df['Versiyon'] == v_yeni]

    yorumlar.append(f"### 🔄 BiP V{v_eski} Sürümünden V{v_yeni} Sürümüne Geçiş Analizi")
    
    sebekeler = sorted(list(set(bip_eski_df['Şebeke']).intersection(set(bip_yeni_df['Şebeke']))))
    for seb in sebekeler:
        v_eski_ort = bip_eski_df[bip_eski_df['Şebeke'] == seb][metrik_kolonu].mean()
        v_yeni_ort = bip_yeni_df[bip_yeni_df['Şebeke'] == seb][metrik_kolonu].mean()

        if pd.notna(v_eski_ort) and pd.notna(v_yeni_ort):
            if v_yeni_ort < v_eski_ort:
                iyilesme = ((v_eski_ort - v_yeni_ort) / v_eski_ort) * 100
                yorumlar.append(f"- **{seb} Şebekesinde:** Yeni **V{v_yeni} sürümü**, eski V{v_eski}'e göre {metrik_adi} süresini **%{iyilesme:.1f} azaltarak (hızlandırarak)** performans artışı kaydetmiştir. ✅")
            else:
                yavaslama = ((v_yeni_ort - v_eski_ort) / v_eski_ort) * 100
                yorumlar.append(f"- **{seb} Şebekesinde:** Yeni **V{v_yeni} sürümünde**, V{v_eski}'e kıyasla %{yavaslama:.1f} oranında bir **yavaşlama (süre artışı)** görülmüştür. ⚠️")

    return "\n".join(yorumlar)

# --- VERİ TARAMA VE YÜKLEME ---
all_files = glob.glob("*.xlsx")
all_data = []

for f in all_files:
    res = veri_isle(f)
    if res is not None:
        all_data.append(res)

if all_data:
    full_df = pd.concat(all_data, ignore_index=True)

    # --- FİLTRELER (SIDEBAR) ---
    st.sidebar.header("⚙️ Analiz Ayarları")

    uzanti_listesi = sorted(full_df['Uzantı'].unique())
    secilen_uzanti = st.sidebar.selectbox("Dosya Formatı Seçin:", uzanti_listesi)

    mevcut_gruplar = sorted(full_df['Grup'].unique())
    secilen_gruplar = st.sidebar.multiselect("Grafikte Gösterilecek Versiyonlar:", mevcut_gruplar, default=mevcut_gruplar)

    # Veriyi filtrele
    plot_df = full_df[(full_df['Uzantı'] == secilen_uzanti) & (full_df['Grup'].isin(secilen_gruplar))]

    if not plot_df.empty:
        # Renk Düzeni (Eski sürüm açık mavi, yeni sürüm koyu lacivert)
        color_map = {}
        if len(mevcut_gruplar) > 0: color_map[mevcut_gruplar[0]] = '#3498db'
        if len(mevcut_gruplar) > 1: color_map[mevcut_gruplar[1]] = '#1f3a60'

        # --- GRAFİKLER VE DETAYLI YORUMLAR ---

        # 1. YÜKLEME (UPLOAD)
        st.subheader(f"📤 {secilen_uzanti} Dosyaları - Yükleme Performansı Kıyaslaması")
        fig_up = px.bar(
            plot_df, x='Boyut', y='Yükleme Süresi', color='Grup',
            facet_col='Şebeke', barmode='group', text_auto=True,
            category_orders={"Şebeke": ["3G", "4.5G", "Wi-Fi"], "Grup": mevcut_gruplar},
            color_discrete_map=color_map,
            labels={'Yükleme Süresi': 'Süre (ms)', 'Grup': 'BiP Sürümü'}
        )
        st.plotly_chart(fig_up, use_container_width=True)

        # Yükleme Gelişim Yorumu
        st.info(surum_gelisim_yorumu(plot_df, 'Yükleme Süresi', 'yükleme'))

        st.divider()

        # 2. İNDİRME (DOWNLOAD)
        st.subheader(f"📥 {secilen_uzanti} Dosyaları - İndirme Performansı Kıyaslaması")
        fig_down = px.bar(
            plot_df, x='Boyut', y='İndirme Süresi', color='Grup',
            facet_col='Şebeke', barmode='group', text_auto=True,
            category_orders={"Şebeke": ["3G", "4.5G", "Wi-Fi"], "Grup": mevcut_gruplar},
            color_discrete_map=color_map,
            labels={'İndirme Süresi': 'Süre (ms)', 'Grup': 'BiP Sürümü'}
        )
        st.plotly_chart(fig_down, use_container_width=True)

        # İndirme Gelişim Yorumu
        st.success(surum_gelisim_yorumu(plot_df, 'İndirme Süresi', 'indirme'))

        # Ham Veri Tablosu
        with st.expander("📊 Filtrelenmiş Veri Tablosu"):
            st.dataframe(plot_df.sort_values(['Şebeke', 'Boyut', 'Grup']), use_container_width=True)

    else:
        st.warning("Seçilen kriterlere uygun veri bulunamadı.")
else:
    st.error("❌ Klasörde eşleşen formatta BiP .xlsx dosyası bulunamadı!")
    st.info("""
    **Beklenen dosya ismi formatı:**
    `5.1.23_Bip_4.5G_HDPhoto.xlsx` veya `5.2.6_Bip_Wifi_SDPhoto.xlsx` gibi olmalıdır.
    """)
