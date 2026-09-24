import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# Sayfa ayarları
st.set_page_config(page_title="BiP (V5.5.15) & WhatsApp Performans Karşılaştırması", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP (V5.5.15) vs WhatsApp İndirme & Yükleme Performansı Analiz Paneli")
st.markdown("""
    Bu panelde **BiP (Sürüm: V5.5.15)** ve WhatsApp uygulamalarının 4.5G (LTE) ve Wi-Fi şebekeleri üzerindeki 
    Fotoğraf, 2dk Video ve 5dk Video indirme/yükleme performansları, ortalama süreleri ve dosya boyutları analiz edilir.
""")

def veri_isle(file_path):
    try:
        if not os.path.exists(file_path):
            return None

        df = pd.read_excel(file_path)

        if df.empty:
            return None

        # --- SÜTUN İSİMLERİNİ TEMİZLEME VE DÜZENLEME ---
        df.rename(columns={df.columns[0]: 'Test Adı'}, inplace=True)
        df.columns = [str(c).strip() for c in df.columns]

        fname = os.path.basename(file_path)
        clean_name = fname.replace(".xlsx", "").replace(".XLSX", "").replace(".csv", "")
        parts = clean_name.split('_')

        # Varsayılan Değerler
        medya_kalitesi = "SD"
        medya_turu = "Fotoğraf"
        islem_turu = "Download"
        network = "Wi-Fi"
        app_name = "BiP"
        version = "V5.5.15"  # Varsayılan BiP Sürümü
        grup_adi = f"BiP ({version})"

        # Dosya ismi parçalarını analiz etme (Örn: SD_2dkVideo_Download_Lte_2.xlsx)
        for part in parts:
            p_lower = part.lower()
            
            # Sonda kalan duplike dosya numaralarını (_2, _3 vb.) es geç
            if p_lower.isdigit() and len(p_lower) <= 2:
                continue

            if p_lower in ["sd", "hd"]:
                medya_kalitesi = part.upper()
            elif "2dkvideo" in p_lower:
                medya_turu = "2dkVideo"
            elif "5dkvideo" in p_lower:
                medya_turu = "5dkVideo"
            elif "photo" in p_lower or "fotograf" in p_lower or "foto" in p_lower:
                medya_turu = "Photo"
            elif "video" in p_lower:
                medya_turu = "Video"
            elif "download" in p_lower or "indirme" in p_lower:
                islem_turu = "Download"
            elif "upload" in p_lower or "yukleme" in p_lower:
                islem_turu = "Upload"
            elif p_lower in ["lte", "4g", "4.5g"]:
                network = "4.5G"
            elif p_lower in ["wifi", "wi-fi", "w"]:
                network = "Wi-Fi"
            elif "wa" in p_lower or "whatsapp" in p_lower:
                app_name = "WhatsApp"
                version = "Güncel"
                grup_adi = "WhatsApp"
            elif p_lower.replace('.', '').isdigit():
                version = f"V{part}"
                app_name = "BiP"
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

        # Başlıkla eşleşmezse varsayılan olarak 2. sütunu al
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

        # Ham veri çıktısı CompressDuration içeriyorsa topla
        if compress_col and compress_col in df.columns:
            df['Süre'] = df[duration_col] + df[compress_col]
        else:
            df['Süre'] = df[duration_col]

        # Dosya boyutu sütununu çekme ve MB birimine dönüştürme
        if size_col and size_col in df.columns:
            df['Boyut (Bytes)'] = df[size_col]
            df['Boyut (MB)'] = (df[size_col] / (1024 * 1024)).round(2)
        else:
            df['Boyut (Bytes)'] = 0
            df['Boyut (MB)'] = 0.0

        df = df.dropna(subset=['Süre'])

        # Tabloya Metadata Sütunlarını Ekle
        df['Uygulama'] = app_name
        df['Versiyon'] = version
        df['Şebeke'] = network
        df['Grup'] = grup_adi
        df['Medya Kalitesi'] = medya_kalitesi
        df['Medya Türü'] = medya_turu
        df['İşlem Türü'] = islem_turu
        df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'DİĞER')

        return df[['Test Adı', 'Uzantı', 'Süre', 'Boyut (MB)', 'Boyut (Bytes)', 'Uygulama', 'Versiyon', 'Şebeke', 'Grup', 'Medya Kalitesi', 'Medya Türü', 'İşlem Türü']]

    except Exception as e:
        st.error(f"⚠️ {os.path.basename(file_path)} işlenirken hata oluştu: {e}")
        return None

# --- PERFORMANS VE LTE/WIFI YORUM MOTORU ---
def performans_yorumu(df, metrik_kolonu, islem_turu):
    if df.empty:
        return "Yorumlanacak veri bulunamadı."

    yorumlar = []
    gruplar = list(df['Grup'].unique())
    sebekeler = sorted(list(df['Şebeke'].unique()))
    islem_str = "indirme" if islem_turu == "Download" else "yükleme"

    # Ortalamalama dosya boyutunu belirleme
    ort_boyut = df['Boyut (MB)'].mean()
    if ort_boyut > 0:
        yorumlar.append(f"📦 **Ortalama Dosya Büyüklüğü:** `{ort_boyut:.2f} MB` ({int(df['Boyut (Bytes)'].mean()):,} Bytes)")

    # 1. Analiz: LTE (4.5G) vs Wi-Fi Performans Karşılaştırması
    if len(sebekeler) >= 2:
        yorumlar.append(f"\n### 📶 LTE (4.5G) vs Wi-Fi Şebeke Karşılaştırması ({islem_turu})")
        for g in gruplar:
            ort_lte = df[(df['Grup'] == g) & (df['Şebeke'] == "4.5G")][metrik_kolonu].mean()
            ort_wifi = df[(df['Grup'] == g) & (df['Şebeke'] == "Wi-Fi")][metrik_kolonu].mean()

            if pd.notna(ort_lte) and pd.notna(ort_wifi) and ort_lte > 0 and ort_wifi > 0:
                if ort_wifi < ort_lte:
                    fark = ((ort_lte - ort_wifi) / ort_lte) * 100
                    yorumlar.append(f"- **{g}:** **Wi-Fi** şebekesi (Ort: `{ort_wifi:.1f} ms`), 4.5G (LTE) şebekesine (Ort: `{ort_lte:.1f} ms`) göre {islem_str} işlemini **%{fark:.1f} daha hızlı** tamamlamıştır. ⚡")
                else:
                    fark = ((ort_wifi - ort_lte) / ort_wifi) * 100
                    yorumlar.append(f"- **{g}:** **4.5G (LTE)** şebekesi (Ort: `{ort_lte:.1f} ms`), Wi-Fi şebekesine (Ort: `{ort_wifi:.1f} ms`) göre {islem_str} işlemini **%{fark:.1f} daha hızlı** tamamlamıştır. 📱")

    # 2. Analiz: BiP Sürüm / Rakip Karşılaştırması
    bip_versions = sorted([g for g in gruplar if "BiP" in g])
    if len(bip_versions) >= 2:
        v_eski = bip_versions[0]
        v_yeni = bip_versions[1]
        
        yorumlar.append(f"\n### 🔄 {v_eski} vs {v_yeni} Sürüm Analizi")
        for seb in sebekeler:
            ort_eski = df[(df['Grup'] == v_eski) & (df['Şebeke'] == seb)][metrik_kolonu].mean()
            ort_yeni = df[(df['Grup'] == v_yeni) & (df['Şebeke'] == seb)][metrik_kolonu].mean()
            
            if pd.notna(ort_eski) and pd.notna(ort_yeni) and ort_eski > 0:
                if ort_yeni < ort_eski:
                    iyilesme = ((ort_eski - ort_yeni) / ort_eski) * 100
                    yorumlar.append(f"- **{seb} Şebekesinde:** Yeni **{v_yeni}** (Ort: `{ort_yeni:.1f} ms`), {v_eski}'e (Ort: `{ort_eski:.1f} ms`) göre {islem_str} süresini **%{iyilesme:.1f} iyileştirmiştir.** ✅")
                else:
                    yavaslama = ((ort_yeni - ort_eski) / ort_eski) * 100
                    yorumlar.append(f"- **{seb} Şebekesinde:** Yeni **{v_yeni}** sürümünde **%{yavaslama:.1f} yavaşlama** görülmüştür. ⚠️")

    if "WhatsApp" in gruplar and len(bip_versions) > 0:
        v_guncel_bip = bip_versions[-1]
        yorumlar.append(f"\n### 🏁 {v_guncel_bip} vs WhatsApp Karşılaştırması")
        for seb in sebekeler:
            ort_bip = df[(df['Grup'] == v_guncel_bip) & (df['Şebeke'] == seb)][metrik_kolonu].mean()
            ort_wa = df[(df['Grup'] == "WhatsApp") & (df['Şebeke'] == seb)][metrik_kolonu].mean()
            
            if pd.notna(ort_bip) and pd.notna(ort_wa) and ort_wa > 0:
                if ort_bip < ort_wa:
                    fark = ((ort_wa - ort_bip) / ort_wa) * 100
                    yorumlar.append(f"- **{seb} Şebekesinde:** **{v_guncel_bip}** (Ort: `{ort_bip:.1f} ms`), WhatsApp'a (Ort: `{ort_wa:.1f} ms`) kıyasla **%{fark:.1f} daha hızlıdır.** 🚀")
                else:
                    fark = ((ort_bip - ort_wa) / ort_wa) * 100
                    yorumlar.append(f"- **{seb} Şebekesinde:** **{v_guncel_bip}** (Ort: `{ort_bip:.1f} ms`), WhatsApp'tan (Ort: `{ort_wa:.1f} ms`) **%{fark:.1f} daha yavaştır.** 📉")
                    
    return "\n".join(yorumlar) if yorumlar else "Kıyaslama için yeterli veri bulunmuyor."

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

    islem_listesi = sorted(full_df['İşlem Türü'].unique())
    secilen_islem = st.sidebar.selectbox("İşlem Türü Seçin:", islem_listesi)

    kalite_listesi = sorted(full_df['Medya Kalitesi'].unique())
    secilen_kalite = st.sidebar.selectbox("Medya Kalitesi Seçin:", kalite_listesi)

    tur_listesi = sorted(full_df['Medya Türü'].unique())
    secilen_tur = st.sidebar.selectbox("Medya Türü Seçin:", tur_listesi)

    mevcut_gruplar = sorted(full_df['Grup'].unique())
    secilen_gruplar = st.sidebar.multiselect("Grafikte Gösterilecek Uygulamalar/Versiyonlar:", mevcut_gruplar, default=mevcut_gruplar)

    # Temel Filtreleme
    plot_df = full_df[
        (full_df['İşlem Türü'] == secilen_islem) &
        (full_df['Medya Kalitesi'] == secilen_kalite) & 
        (full_df['Medya Türü'] == secilen_tur) & 
        (full_df['Grup'].isin(secilen_gruplar))
    ].copy()

    if not plot_df.empty:
        # --- DİNAMİK KOŞUM SAYISI (SIRA NO) ATAMA ---
        plot_df = plot_df.sort_values(by=['Şebeke', 'Grup', 'Test Adı'])
        plot_df['Koşum Sayısı'] = plot_df.groupby(['Şebeke', 'Grup']).cumcount() + 1
        plot_df['Koşum Sayısı'] = plot_df['Koşum Sayısı'].astype(str) + ". Koşum"

        # --- ORTALAMA SÜRE METRİK KARTLARI ---
        st.subheader("⏱️ Ortalama Süreler Özeti")
        col1, col2, col3 = st.columns(3)

        genel_ort = plot_df['Süre'].mean()
        col1.metric(f"Genel Ortalama {secilen_islem} Süresi", f"{genel_ort:.1f} ms", f"{genel_ort/1000:.2f} sn")

        lte_df = plot_df[plot_df['Şebeke'] == '4.5G']
        if not lte_df.empty:
            lte_ort = lte_df['Süre'].mean()
            col2.metric(f"4.5G (LTE) Ortalama Süre", f"{lte_ort:.1f} ms", f"{lte_ort/1000:.2f} sn")

        wifi_df = plot_df[plot_df['Şebeke'] == 'Wi-Fi']
        if not wifi_df.empty:
            wifi_ort = wifi_df['Süre'].mean()
            col3.metric(f"Wi-Fi Ortalama Süre", f"{wifi_ort:.1f} ms", f"{wifi_ort/1000:.2f} sn")

        st.markdown("---")

        # Renk Paleti
        color_map = {
            'WhatsApp': '#25D366',
            'BiP (V5.5.15)': '#3498db'
        }
        bip_groups = [g for g in mevcut_gruplar if "BiP" in g]
        if len(bip_groups) > 0: color_map[bip_groups[0]] = '#3498db'
        if len(bip_groups) > 1: color_map[bip_groups[1]] = '#1f3a60'

        # --- GRAFİK GÖSTERİMİ ---
        islem_baslik = "İndirme (Download)" if secilen_islem == "Download" else "Yükleme (Upload)"
        st.subheader(f"📊 {secilen_kalite} {secilen_tur} Dosyaları - {islem_baslik} Performansı Kıyaslaması")
        
        fig = px.bar(
            plot_df, x='Koşum Sayısı', y='Süre', color='Grup',
            facet_col='Şebeke', barmode='group', text_auto=True,
            hover_data=['Boyut (MB)', 'Boyut (Bytes)'],
            category_orders={
                "Şebeke": ["4.5G", "Wi-Fi"], 
                "Grup": mevcut_gruplar,
                "Koşum Sayısı": sorted(plot_df['Koşum Sayısı'].unique(), key=lambda x: int(x.split('.')[0]))
            },
            color_discrete_map=color_map,
            labels={'Süre': 'Süre (ms)', 'Grup': 'Uygulama / Sürüm', 'Koşum Sayısı': 'Koşum Numarası'}
        )
        st.plotly_chart(fig, use_container_width=True)

        st.info(performans_yorumu(plot_df, 'Süre', secilen_islem))

        # --- ORTALAMALAR TABLOSU VE VERİ TABLOSU ---
        with st.expander("📌 Grup ve Şebeke Bazlı Ortalama Süreler Tablosu"):
            summary_df = plot_df.groupby(['Grup', 'Şebeke']).agg(
                Ortalama_Süre_ms=('Süre', 'mean'),
                Ortalama_Süre_sn=('Süre', lambda x: x.mean() / 1000),
                Ortalama_Boyut_MB=('Boyut (MB)', 'mean'),
                Koşum_Sayısı=('Süre', 'count')
            ).reset_index()

            summary_df['Ortalama_Süre_ms'] = summary_df['Ortalama_Süre_ms'].round(1)
            summary_df['Ortalama_Süre_sn'] = summary_df['Ortalama_Süre_sn'].round(2)
            summary_df['Ortalama_Boyut_MB'] = summary_df['Ortalama_Boyut_MB'].round(2)

            summary_df.columns = ['Uygulama/Grup', 'Şebeke', 'Ortalama Süre (ms)', 'Ortalama Süre (sn)', 'Ortalama Boyut (MB)', 'Toplam Koşum']
            st.dataframe(summary_df, use_container_width=True)

        with st.expander("📊 Filtrelenmiş Tüm Veri Tablosu (Dosya Büyüklükleri Dahil)"):
            gosterilecek_sutunlar = ['Test Adı', 'Süre', 'Boyut (MB)', 'Boyut (Bytes)', 'Grup', 'Şebeke', 'İşlem Türü', 'Koşum Sayısı']
            mevcut_sutunlar = [col for col in gosterilecek_sutunlar if col in plot_df.columns]
            
            siralama_sutunlari = [col for col in ['Şebeke', 'Koşum Sayısı', 'Grup'] if col in plot_df.columns]
            
            if siralama_sutunlari:
                st.dataframe(plot_df[mevcut_sutunlar].sort_values(siralama_sutunlari), use_container_width=True)
            else:
                st.dataframe(plot_df[mevcut_sutunlar], use_container_width=True)
    else:
        st.warning("Seçilen kriterlere uygun veri bulunamadı. Lütfen sol menüden farklı kombinasyonlar deneyin.")
else:
    st.error("❌ Klasörde geçerli Excel (.xlsx) dosyası bulunamadı!")
