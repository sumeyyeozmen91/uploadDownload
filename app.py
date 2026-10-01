import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob
import re

# Sayfa ayarları
st.set_page_config(page_title="BiP (V5.5.15) & WhatsApp Performans Karşılaştırması", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP (V5.5.15) vs WhatsApp İndirme & Yükleme Performansı Analiz Paneli")
st.markdown("""
    Bu panelde **BiP (Sürüm: V5.5.15)** ve **WhatsApp** uygulamalarının LTE şebekesi üzerindeki 
    Fotoğraf ve 2dk Video indirme/yükleme performansları, ortalama süreleri ve dosya boyutları ritmik koşum sırasına göre analiz edilir.
""")

# İzin verilen tam dosya isimleri (Büyük/küçük harf duyarsız kontrol edilir)
ALLOWED_FILES = {
    "sd_2dkvideo_download_lte",
    "sd_2dkvideo_upload_lte",
    "sd_2dkvideo_wa_download_lte",
    "sd_2dkvideo_wa_upload_lte",
    "sd_photo_download_lte",
    "sd_photo_upload_lte",
    "sd_photo_wa_download_lte",
    "sd_photo_wa_upload_lte"
}

def veri_isle(file_path):
    try:
        if not os.path.exists(file_path):
            return None

        fname = os.path.basename(file_path)
        base_name = fname.split('.')[0].lower().strip()

        # Sadece izin verilen 8 dosyayı filtrele
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

        # 8 Özel Dosya Mimarisine Göre Metadata Belirleme
        is_wa = "_wa_" in base_name
        is_video = "2dkvideo" in base_name
        is_upload = "_upload_" in base_name

        medya_kalitesi = "SD"
        medya_turu = "2dkVideo" if is_video else "Photo"
        islem_turu = "Upload" if is_upload else "Download"
        network = "4.5G"

        if is_wa:
            app_name = "WhatsApp"
            version = "Güncel"
            grup_adi = "WhatsApp"
        else:
            app_name = "BiP"
            version = "V5.5.15"
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
def performans_yorumu(df, metrik_kolonu, islem_turu):
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
                hiz_farki = ((ort_wa - ort_bip) / ort_wa) * 100
                saniye_farki = (ort_wa - ort_bip) / 1000
                yorumlar.append(
                    f"- **4.5G (LTE) Şebekesinde:** **BiP** ({ort_bip:.1f} ms / {bip_sec:.2f} sn), "
                    f"WhatsApp'a ({ort_wa:.1f} ms / {wa_sec:.2f} sn) göre **{saniye_farki:.2f} saniye (%{hiz_farki:.1f}) daha hızlıdır.** 🚀"
                )
            elif ort_wa < ort_bip:
                hiz_farki = ((ort_bip - ort_wa) / ort_wa) * 100
                saniye_farki = (ort_bip - ort_wa) / 1000
                yorumlar.append(
                    f"- **4.5G (LTE) Şebekesinde:** **WhatsApp** ({ort_wa:.1f} ms / {wa_sec:.2f} sn), "
                    f"BiP'e ({ort_bip:.1f} ms / {bip_sec:.2f} sn) göre **{saniye_farki:.2f} saniye (%{hiz_farki:.1f}) daha hızlıdır.** 📉"
                )
            else:
                yorumlar.append(f"- **4.5G (LTE) Şebekesinde:** BiP ve WhatsApp eşit süre kaydetmiştir ({bip_sec:.2f} sn). ⚖️")

    return "\n".join(yorumlar) if yorumlar else "Kıyaslama için yeterli veri bulunmuyor."

# --- VERİ TARAMA VE YÜKLEME ---
found_files = glob.glob("*.xlsx") + glob.glob("*.XLSX") + glob.glob("*.csv") + glob.glob("*.CSV")
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

    islem_listesi = sorted(full_df['İşlem Türü'].unique())
    secilen_islem = st.sidebar.selectbox("İşlem Türü Seçin:", islem_listesi)

    tur_listesi = sorted(full_df['Medya Türü'].unique())
    secilen_tur = st.sidebar.selectbox("Medya Türü Seçin:", tur_listesi)

    mevcut_gruplar = sorted(full_df['Grup'].unique())
    secilen_gruplar = st.sidebar.multiselect("Grafikte Gösterilecek Uygulamalar/Versiyonlar:", mevcut_gruplar, default=mevcut_gruplar)

    # Temel Filtreleme
    plot_df = full_df[
        (full_df['İşlem Türü'] == secilen_islem) &
        (full_df['Medya Türü'] == secilen_tur) & 
        (full_df['Grup'].isin(secilen_gruplar))
    ].copy()

    if not plot_df.empty:
        # --- BİREBİR RİTMİK KOŞUM SAYISI ATAMA ---
        plot_df = plot_df.sort_values(by=['Koşum Sırası', 'Grup'])
        plot_df['Koşum Numarası'] = plot_df['Koşum Sırası'].astype(str) + ". Koşum"

        # Ritmik Sıralama Düzeni
        sirali_kosumlar = [f"{i}. Koşum" for i in sorted(plot_df['Koşum Sırası'].unique())]

        # --- ORTALAMA SÜRE METRİK KARTLARI ---
        st.subheader("⏱️ Ortalama Süreler Özeti")
        col1, col2 = st.columns(2)

        genel_ort = plot_df['Süre'].mean()
        col1.metric(f"Genel Ortalama {secilen_islem} Süresi", f"{genel_ort:.1f} ms", f"{genel_ort/1000:.2f} sn")

        bip_df = plot_df[plot_df['Uygulama'] == 'BiP']
        if not bip_df.empty:
            bip_ort = bip_df['Süre'].mean()
            col2.metric(f"BiP (V5.5.15) Ortalama Süre", f"{bip_ort:.1f} ms", f"{bip_ort/1000:.2f} sn")

        st.markdown("---")

        # Renk Paleti
        color_map = {
            'WhatsApp': '#25D366',
            'BiP (V5.5.15)': '#3498db'
        }

        # --- GRAFİK GÖSTERİMİ ---
        islem_baslik = "İndirme (Download)" if secilen_islem == "Download" else "Yükleme (Upload)"
        st.subheader(f"📊 SD {secilen_tur} Dosyaları (LTE/4.5G) - {islem_baslik} Performansı Kıyaslaması")
        
        fig = px.bar(
            plot_df, x='Koşum Numarası', y='Süre', color='Grup',
            barmode='group', text_auto=True,
            hover_data=['Boyut (MB)', 'Boyut (Bytes)'],
            category_orders={
                "Grup": mevcut_gruplar,
                "Koşum Numarası": sirali_kosumlar
            },
            color_discrete_map=color_map,
            labels={'Süre': 'Süre (ms)', 'Grup': 'Uygulama / Sürüm', 'Koşum Numarası': 'Koşum Numarası'}
        )
        st.plotly_chart(fig, use_container_width=True)

        st.info(performans_yorumu(plot_df, 'Süre', secilen_islem))

        # --- ORTALAMALAR TABLOSU VE VERİ TABLOSU ---
        with st.expander("📌 Uygulama Bazlı Ortalama Süreler Tablosu"):
            summary_df = plot_df.groupby(['Grup']).agg(
                Ortalama_Süre_ms=('Süre', 'mean'),
                Ortalama_Süre_sn=('Süre', lambda x: x.mean() / 1000),
                Ortalama_Boyut_MB=('Boyut (MB)', 'mean'),
                Koşum_Sayısı=('Süre', 'count')
            ).reset_index()

            summary_df['Ortalama_Süre_ms'] = summary_df['Ortalama_Süre_ms'].round(1)
            summary_df['Ortalama_Süre_sn'] = summary_df['Ortalama_Süre_sn'].round(2)
            summary_df['Ortalama_Boyut_MB'] = summary_df['Ortalama_Boyut_MB'].round(2)

            summary_df.columns = ['Uygulama/Grup', 'Ortalama Süre (ms)', 'Ortalama Süre (sn)', 'Ortalama Boyut (MB)', 'Toplam Koşum']
            st.dataframe(summary_df, use_container_width=True)

        with st.expander("📊 Filtrelenmiş Tüm Veri Tablosu (Dosya Büyüklükleri Dahil)"):
            gosterilecek_sutunlar = ['Test Adı', 'Koşum Numarası', 'Süre', 'Boyut (MB)', 'Boyut (Bytes)', 'Grup', 'İşlem Türü']
            mevcut_sutunlar = [col for col in gosterilecek_sutunlar if col in plot_df.columns]
            
            siralama_sutunlari = [col for col in ['Koşum Sırası', 'Grup'] if col in plot_df.columns]
            
            if siralama_sutunlari:
                st.dataframe(plot_df.sort_values(siralama_sutunlari)[mevcut_sutunlar], use_container_width=True)
            else:
                st.dataframe(plot_df[mevcut_sutunlar], use_container_width=True)
    else:
        st.warning("Seçilen kriterlere uygun veri bulunamadı. Lütfen sol menüden farklı kombinasyonlar deneyin.")
else:
    st.error("❌ Klasörde belirtilen 8 adet geçerli Excel (.xlsx) veya CSV dosyası bulunamadı!")
