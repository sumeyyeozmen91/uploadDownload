import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# Sayfa ayarları
st.set_page_config(page_title="BiP & WhatsApp İndirme Performansı Karşılaştırması", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP (V5.1.23) vs BiP (V5.2.6) vs WhatsApp İndirme Performansı Karşılaştırması")
st.markdown("""
    Bu panelde BiP uygulamasının versiyon gelişimi ve WhatsApp ile olan performans kıyaslaması eş zamanlı olarak analiz edilir:
    * **BiP Sürüm Gelişimi (V5.1.23 vs V5.2.6):** İki farklı BiP sürümü arasındaki indirme süreleri ve iyileşme oranları.
    * **BiP (V5.2.6) vs WhatsApp:** Güncel BiP sürümünün, rakip uygulama olan WhatsApp karşısındaki hız ve performans durumu.
""")

def veri_isle(file_path):
    try:
        if not os.path.exists(file_path):
            return None

        df = pd.read_excel(file_path)

        if df.empty:
            return None

        # --- SÜTUN İSİMLERİNİ EŞLEŞTİRME VE TEMİZLEME ---
        df.rename(columns={df.columns[0]: 'Test Adı'}, inplace=True)
        df.columns = [str(c).strip() for c in df.columns]

        # Sadece Download_Duration sütununu hedef alıyoruz
        df.rename(columns={c: 'İndirme Süresi' for c in df.columns if 'download_duration' in c.lower() or c == 'Download_Duration'}, inplace=True)

        gerekli_sutunlar = ['Test Adı', 'İndirme Süresi']
        for col in gerekli_sutunlar:
            if col not in df.columns:
                st.error(f"⚠️ {os.path.basename(file_path)} içinde gerekli sütun yapısı çözülemedi! Mevcut Sütunlar: {list(df.columns)}")
                return None

        # --- GÜVENLİ SAYISAL DÖNÜŞTÜRME ---
        df['İndirme Süresi'] = df['İndirme Süresi'].apply(lambda x: ''.join(c for c in str(x) if c.isdigit() or c in ['.', ',']))
        df['İndirme Süresi'] = df['İndirme Süresi'].str.replace(',', '.')
        df['İndirme Süresi'] = pd.to_numeric(df['İndirme Süresi'], errors='coerce').astype(float)

        # İndirme verisi olmayan satırları eliyoruz
        df = df.dropna(subset=['İndirme Süresi'])

        fname = os.path.basename(file_path).lower()
        clean_name = fname.replace(".xlsx", "").replace(".csv", "")
        parts = clean_name.split('_')

        # --- DOSYA ADI FORMATI AYRIŞTIRMA ---
        if "bip" in fname and len(parts) >= 4:
            version = parts[0]   # "5.1.23" veya "5.2.6"
            app_name = "BiP"
            net_raw = parts[2]   # "4.5g" veya "wifi"
            type_raw = parts[3]  # "hdphoto", "sdphoto" vb.
            grup_adi = f"BiP (V{version})"
        elif "wa" in fname and len(parts) >= 3:
            version = "Güncel"
            app_name = "WhatsApp"
            net_raw = parts[1]   # "4.5g" veya "wifi"
            type_raw = parts[2]  # "hdphoto", "sdphoto" vb.
            grup_adi = "WhatsApp"
        else:
            return None

        # Medya kalitesi ve türü ayrıştırma
        if "hd" in type_raw:
            medya_kalitesi = "HD"
            medya_turu = type_raw.replace("hd", "").capitalize()
        elif "sd" in type_raw:
            medya_kalitesi = "SD"
            medya_turu = type_raw.replace("sd", "").capitalize()
        else:
            medya_kalitesi = "Genel"
            medya_turu = type_raw.capitalize()

        # Şebeke ismini standartlaştır
        if "3g" in net_raw: network = "3G"
        elif "4g" in net_raw or "4.5g" in net_raw: network = "4.5G"
        elif "wifi" in net_raw: network = "Wi-Fi"
        else: network = net_raw.upper()

        # DataFrame sütunlarını doldur
        df['Uygulama'] = app_name
        df['Versiyon'] = version
        df['Şebeke'] = network
        df['Grup'] = grup_adi
        df['Medya Kalitesi'] = medya_kalitesi
        df['Medya Türü'] = medya_turu
        df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'DİĞER')

        return df[['Test Adı', 'Uzantı', 'İndirme Süresi', 'Uygulama', 'Versiyon', 'Şebeke', 'Grup', 'Medya Kalitesi', 'Medya Türü']]

    except Exception as e:
        st.error(f"⚠️ {os.path.basename(file_path)} işlenirken hata oluştu: {e}")
        return None

# --- SÜRÜM GELİŞİM VE RAKİP YORUM MOTORU ---
def performans_yorumu(df, metrik_kolonu):
    if df.empty:
        return "Yorumlanacak veri bulunamadı."

    yorumlar = []
    gruplar = list(df['Grup'].unique())
    sebekeler = sorted(list(df['Şebeke'].unique()))

    # 1. Analiz: BiP Versiyon Karşılaştırması (Eski vs Yeni)
    bip_versions = sorted([g for g in gruplar if "BiP" in g])
    if len(bip_versions) >= 2:
        v_eski = bip_versions[0]
        v_yeni = bip_versions[1]
        
        yorumlar.append(f"### 🔄 {v_eski} Sürümünden {v_yeni} Sürümüne Geçiş Analizi")
        for seb in sebekeler:
            ort_eski = df[(df['Grup'] == v_eski) & (df['Şebeke'] == seb)][metrik_kolonu].mean()
            ort_yeni = df[(df['Grup'] == v_yeni) & (df['Şebeke'] == seb)][metrik_kolonu].mean()
            
            if pd.notna(ort_eski) and pd.notna(ort_yeni):
                if ort_yeni < ort_eski:
                    iyilesme = ((ort_eski - ort_yeni) / ort_eski) * 100
                    yorumlar.append(f"- **{seb} Şebekesinde:** Yeni **{v_yeni}**, eski {v_eski}'e göre indirme süresini **%{iyilesme:.1f} azaltarak (hızlandırarak)** performans artışı kaydetmiştir. ✅")
                else:
                    yavaslama = ((ort_yeni - ort_eski) / ort_eski) * 100
                    yorumlar.append(f"- **{seb} Şebekesinde:** Yeni **{v_yeni}** sürümünde, {v_eski}'e kıyasla **%{yavaslama:.1f} yavaşlama** (süre artışı) görülmüştür. ⚠️")

    # 2. Analiz: En Güncel BiP vs WhatsApp Karşılaştırması
    if "WhatsApp" in gruplar and len(bip_versions) > 0:
        v_guncel_bip = bip_versions[-1]
        
        yorumlar.append(f"\n### 🏁 {v_guncel_bip} Sürümü ile WhatsApp Karşılaştırması")
        for seb in sebekeler:
            ort_bip = df[(df['Grup'] == v_guncel_bip) & (df['Şebeke'] == seb)][metrik_kolonu].mean()
            ort_wa = df[(df['Grup'] == "WhatsApp") & (df['Şebeke'] == seb)][metrik_kolonu].mean()
            
            if pd.notna(ort_bip) and pd.notna(ort_wa):
                if ort_bip < ort_wa:
                    fark = ((ort_wa - ort_bip) / ort_wa) * 100
                    yorumlar.append(f"- **{seb} Şebekesinde:** **{v_guncel_bip}**, WhatsApp'a göre **%{fark:.1f} daha hızlıdır.** 🚀")
                else:
                    fark = ((ort_bip - ort_wa) / ort_wa) * 100
                    yorumlar.append(f"- **{seb} Şebekesinde:** **{v_guncel_bip}**, WhatsApp'tan **%{fark:.1f} daha yavaştır.** 📉")
                    
    return "\n".join(yorumlar)

# --- VERİ TARAMA VE YÜKLEME ---
all_files = glob.glob("*.xlsx") + glob.glob("*.XLSX")
all_files = list(set(all_files))

all_data = []
for f in all_files:
    res = veri_isle(f)
    if res is not None:
        all_data.append(res)

if all_data:
    full_df = pd.concat(all_data, ignore_index=True)

    # --- FİLTRELER (SIDEBAR) ---
    st.sidebar.header("⚙️ Analiz Ayarları")

    kalite_listesi = sorted(full_df['Medya Kalitesi'].unique())
    secilen_kalite = st.sidebar.selectbox("Medya Kalitesi Seçin:", kalite_listesi)

    tur_listesi = sorted(full_df['Medya Türü'].unique())
    secilen_tur = st.sidebar.selectbox("Medya Türü Seçin:", tur_listesi)

    mevcut_gruplar = sorted(full_df['Grup'].unique())
    secilen_gruplar = st.sidebar.multiselect("Grafikte Gösterilecek Uygulamalar/Versiyonlar:", mevcut_gruplar, default=mevcut_gruplar)

    # Temel Filtreleme
    plot_df = full_df[
        (full_df['Medya Kalitesi'] == secilen_kalite) & 
        (full_df['Medya Türü'] == secilen_tur) & 
        (full_df['Grup'].isin(secilen_gruplar))
    ].copy()

    if not plot_df.empty:
        # --- DİNAMİK KOŞUM SAYISI (SIRA NO) ATAMA ---
        plot_df = plot_df.sort_values(by=['Şebeke', 'Grup', 'Test Adı'])
        plot_df['Koşum Sayısı'] = plot_df.groupby(['Şebeke', 'Grup']).cumcount() + 1
        plot_df['Koşum Sayısı'] = plot_df['Koşum Sayısı'].astype(str) + ". Koşum"

        # Renk paleti
        color_map = {
            'WhatsApp': '#25D366'
        }
        bip_groups = [g for g in mevcut_gruplar if "BiP" in g]
        if len(bip_groups) > 0: color_map[bip_groups[0]] = '#3498db'
        if len(bip_groups) > 1: color_map[bip_groups[1]] = '#1f3a60'

        # --- GRAFİK: İNDİRME (DOWNLOAD) ---
        st.subheader(f"📥 {secilen_kalite} {secilen_tur} Dosyaları - İndirme Performansı Kıyaslaması")
        
        fig_down = px.bar(
            plot_df, x='Koşum Sayısı', y='İndirme Süresi', color='Grup',
            facet_col='Şebeke', barmode='group', text_auto=True,
            category_orders={
                "Şebeke": ["4.5G", "Wi-Fi"], 
                "Grup": mevcut_gruplar,
                "Koşum Sayısı": sorted(plot_df['Koşum Sayısı'].unique(), key=lambda x: int(x.split('.')[0]))
            },
            color_discrete_map=color_map,
            labels={'İndirme Süresi': 'Süre (ms)', 'Grup': 'Uygulama / Sürüm', 'Koşum Sayısı': 'Koşum Numarası'}
        )
        st.plotly_chart(fig_down, use_container_width=True)

        st.info(performans_yorumu(plot_df, 'İndirme Süresi'))

        with st.expander("📊 Filtrelenmiş Veri Tablosu"):
            st.dataframe(plot_df.sort_values(['Şebeke', 'Koşum Sayısı', 'Grup']), use_container_width=True)
    else:
        st.warning("Seçilen kriterlere uygun veri bulunamadı. Lütfen sol menüden farklı kombinasyonlar deneyin.")
else:
    st.error("❌ Klasörde geçerli veri içeren BiP veya Wa (WhatsApp) .xlsx dosyası bulunamadı!")
