import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# Sayfa ayarları
st.set_page_config(page_title="Hız Testi Analiz Merkezi", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP (V5.1.23 & V5.2.6) vs WhatsApp Performans Analizi")
st.markdown("""
    Bu panelde iki özel senaryo analiz edilir:
    1. **WhatsApp vs BiP (V5.1.23):** İki farklı uygulamanın karşılaştırması.
    2. **BiP (V5.1.23) vs BiP (V5.2.6):** BiP uygulamasının versiyon gelişimi.
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
        # Senaryo 1: Wa_3G.xlsx formatı (WhatsApp)
        if fname.startswith('wa_'):
            parts = fname.split('_')
            app_name = "WhatsApp"
            version = "Mevcut"  # Sabit versiyon
            net_raw = parts[1].replace(".xlsx", "").replace(".csv", "")

        # Senaryo 2: Dinamik Sürüm Yönetimi (Örn: 5.1.23_Bip_4.5G_HDPhoto.xlsx)
        elif "_" in fname and "bip" in fname:
            parts = fname.split('_')
            version = parts[0] # "5.1.23" veya "5.2.6" gibi dinamik olarak ilk bölümü alır
            app_name = "BiP"
            net_raw = parts[2].replace(".xlsx", "").replace(".csv", "")
        else:
            return None # Tanımlanamayan dosya formatlarını es geç

        # Şebeke ismini standartlaştır
        if "3g" in net_raw: network = "3G"
        elif "4g" in net_raw or "4.5g" in net_raw: network = "4G"
        elif "wifi" in net_raw: network = "Wi-Fi"
        else: network = net_raw.upper()

        # DataFrame sütunlarını doldur
        df['Uygulama'] = app_name
        df['Versiyon'] = version
        df['Şebeke'] = network

        # Grafiklerde görünecek grup etiketi
        if app_name == "WhatsApp":
            df['Grup'] = "WhatsApp"
        else:
            df['Grup'] = f"BiP (V{version})"

        # Dosya uzantısı ve boyutu çıkarma
        df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'DİĞER')
        df['Boyut'] = df['Test Adı'].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x))

        return df[['Test Adı', 'Uzantı', 'Boyut', 'Yükleme Süresi', 'İndirme Süresi', 'Uygulama', 'Versiyon', 'Şebeke', 'Grup']]
    except Exception as e:
        st.error(f"⚠️ {file_path} işlenirken hata oluştu: {e}")
        return None

# --- ÖZEL İKİLİ KARŞILAŞTIRMA YORUM MOTORU ---
def ozel_karsilastirma_yorumu(df, metrik_kolonu, metrik_adi):
    if df.empty:
        return "Yorumlanacak veri bulunamadı."

    yorumlar = []

    # Mevcut verideki BiP versiyonlarını tespit et (Örn: ['5.1.23', '5.2.6'])
    bip_versions = sorted([g.replace("BiP (V", "").replace(")", "") for g in df['Grup'].unique() if "BiP" in g])
    
    # Karşılaştırma motoru için versiyon etiketlerini ata
    v_eski = bip_versions[0] if len(bip_versions) > 0 else "5.1.23"
    v_yeni = bip_versions[1] if len(bip_versions) > 1 else "5.2.6"

    wa_df = df[df['Grup'] == 'WhatsApp']
    bip_eski_df = df[df['Grup'] == f'BiP (V{v_eski})']

    yorumlar.append(f"### 📊 1. WhatsApp vs BiP (V{v_eski}) Karşılaştırması")
    if not wa_df.empty and not bip_eski_df.empty:
        sebekeler = sorted(list(set(wa_df['Şebeke']).intersection(set(bip_eski_df['Şebeke']))))
        for seb in sebekeler:
            wa_ort = wa_df[wa_df['Şebeke'] == seb][metrik_kolonu].mean()
            bip_ort = bip_eski_df[bip_eski_df['Şebeke'] == seb][metrik_kolonu].mean()

            if pd.notna(wa_ort) and pd.notna(bip_ort):
                if bip_ort < wa_ort:
                    fark = ((wa_ort - bip_ort) / wa_ort) * 100
                    yorumlar.append(f"- **{seb} Şebekesinde:** **BiP (V{v_eski})**, WhatsApp'a göre ortalama {metrik_adi} süresinde **%{fark:.1f} daha hızlıdır**.")
                else:
                    fark = ((bip_ort - wa_ort) / bip_ort) * 100
                    yorumlar.append(f"- **{seb} Şebekesinde:** **WhatsApp**, BiP (V{v_eski})'e göre ortalama {metrik_adi} süresinde **%{fark:.1f} daha hızlıdır**.")
    else:
        yorumlar.append(f"- Kıyaslama yapılamadı. Klasörde WhatsApp veya BiP V{v_eski} dosyalarından biri eksik.")

    # 2. BIP SÜRÜM GELİŞİM KIYASLAMASI
    bip_yeni_df = df[df['Grup'] == f'BiP (V{v_yeni})']

    yorumlar.append(f"\n### 🔄 2. BiP V{v_eski} Sürümünden V{v_yeni} Sürümüne Geçiş Analizi")
    if not bip_eski_df.empty and not bip_yeni_df.empty:
        sebekeler = sorted(list(set(bip_eski_df['Şebeke']).intersection(set(bip_yeni_df['Şebeke']))))
        for seb in sebekeler:
            v51_ort = bip_eski_df[bip_eski_df['Şebeke'] == seb][metrik_kolonu].mean()
            v52_ort = bip_yeni_df[bip_yeni_df['Şebeke'] == seb][metrik_kolonu].mean()

            if pd.notna(v51_ort) and pd.notna(v52_ort):
                if v52_ort < v51_ort:
                    iyilesme = ((v51_ort - v52_ort) / v51_ort) * 100
                    yorumlar.append(f"- **{seb} Şebekesinde:** Yeni **V{v_yeni} sürümü**, eski V{v_eski}'e göre {metrik_adi} süresini **%{iyilesme:.1f} azaltarak (hızlandırarak)** performans artışı kaydetmiştir. ✅")
                else:
                    yavaslama = ((v52_ort - v51_ort) / v51_ort) * 100
                    yorumlar.append(f"- **{seb} Şebekesinde:** Yeni **V{v_yeni} sürümünde**, V{v_eski}'e kıyasla %{yavaslama:.1f} oranında bir **yavaşlama (süre artışı)** görülmüştür. ⚠️")
    else:
        yorumlar.append(f"- Klasörde BiP V{v_eski} veya V{v_yeni} dosyalarından biri eksik olduğu için sürüm gelişim analizi yapılamadı.")

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
    secilen_gruplar = st.sidebar.multiselect("Grafikte Gösterilecek Gruplar:", mevcut_gruplar, default=mevcut_gruplar)

    # Veriyi filtrele
    plot_df = full_df[(full_df['Uzantı'] == secilen_uzanti) & (full_df['Grup'].isin(secilen_gruplar))]

    if not plot_df.empty:
        # Renk Düzeni (WhatsApp Yeşil, BiP Tonları Mavi)
        # Sürümler dinamikleştiği için mevcut gruplara göre eşleme yapılır
        color_map = {
            'WhatsApp': '#2ecc71',
        }
        # Dinamik olarak listedeki ilk BiP sürümünü açık mavi, ikincisini koyu lacivert yapar
        bip_groups = [g for g in mevcut_gruplar if "BiP" in g]
        if len(bip_groups) > 0: color_map[bip_groups[0]] = '#3498db'
        if len(bip_groups) > 1: color_map[bip_groups[1]] = '#1f3a60'

        # --- GRAFİKLER VE DETAYLI YORUMLAR ---

        # 1. YÜKLEME (UPLOAD)
        st.subheader(f"📤 {secilen_uzanti} Dosyaları - Yükleme Performansı Kıyaslaması")
        fig_up = px.bar(
            plot_df, x='Boyut', y='Yükleme Süresi', color='Grup',
            facet_col='Şebeke', barmode='group', text_auto=True,
            category_orders={"Şebeke": ["3G", "4G", "Wi-Fi"], "Grup": mevcut_gruplar},
            color_discrete_map=color_map,
            labels={'Yükleme Süresi': 'Süre (ms)', 'Grup': 'Uygulama & Sürüm'}
        )
        st.plotly_chart(fig_up, use_container_width=True)

        st.info(ozel_karsilastirma_yorumu(plot_df, 'Yükleme Süresi', 'yükleme'))

        st.divider()

        # 2. İNDİRME (DOWNLOAD)
        st.subheader(f"📥 {secilen_uzanti} Dosyaları - İndirme Performansı Kıyaslaması")
        fig_down = px.bar(
            plot_df, x='Boyut', y='İndirme Süresi', color='Grup',
            facet_col='Şebeke', barmode='group', text_auto=True,
            category_orders={"Şebeke": ["3G", "4G", "Wi-Fi"], "Grup": mevcut_gruplar},
            color_discrete_map=color_map,
            labels={'İndirme Süresi': 'Süre (ms)', 'Grup': 'Uygulama & Sürüm'}
        )
        st.plotly_chart(fig_down, use_container_width=True)

        st.success(ozel_karsilastirma_yorumu(plot_df, 'İndirme Süresi', 'indirme'))

        with st.expander("📊 Filtrelenmiş Veri Tablosu"):
            st.dataframe(plot_df.sort_values(['Şebeke', 'Boyut', 'Grup']), use_container_width=True)

    else:
        st.warning("Seçilen kriterlere uygun veri bulunamadı.")
else:
    st.error("❌ Klasörde eşleşen formatta .xlsx dosyası bulunamadı!")
    st.info("""
    **Beklenen örnek dosya isimleri:**
    - WhatsApp için: `Wa_3G.xlsx`, `Wa_4G.xlsx`, `Wa_Wifi.xlsx`
    - BiP için: `5.1.23_Bip_4.5G_HDPhoto.xlsx`, `5.2.6_Bip_Wifi_SDPhoto.xlsx`
    """)
