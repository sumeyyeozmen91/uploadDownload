import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# Sayfa ayarları
st.set_page_config(page_title="BiP Versiyon Karşılaştırma Merkezi", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP Versiyon İndirme Performans Analizi")
st.markdown("""
    Bu panelde BiP uygulamasının versiyon gelişimi analiz edilir:
    * **BiP (V5.1.23) vs BiP (V5.2.6):** İki farklı sürüm arasındaki indirme performans farkları ve iyileşme oranları.
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

        # Sadece Download_Duration sütununu hedef alıyoruz (Duration sütunu yok sayılıyor)
        sutun_haritasi = {
            'Download_Duration': 'İndirme Süresi'
        }
        df.rename(columns=sutun_haritasi, inplace=True)

        gerekli_sutunlar = ['Test Adı', 'İndirme Süresi']
        for col in gerekli_sutunlar:
            if col not in df.columns:
                st.error(f"⚠️ {os.path.basename(file_path)} içinde gerekli sütun yapısı çözülemedi! Mevcut Sütunlar: {list(df.columns)}")
                return None

        # --- GÜVENLİ SAYISAL DÖNÜŞTÜRME (PyArrow String Hatası Çözümü) ---
        # Değerleri tek tek stringe çevirip temizliyoruz (vektörel kilitleri kırmak için)
        df['İndirme Süresi'] = df['İndirme Süresi'].apply(lambda x: ''.join(c for c in str(x) if c.isdigit() or c in ['.', ',']))
        df['İndirme Süresi'] = df['İndirme Süresi'].str.replace(',', '.')
        
        # Önce objeyi sayısal değere zorla, ardından float tipine cast et
        df['İndirme Süresi'] = pd.to_numeric(df['İndirme Süresi'], errors='coerce').astype(float)

        # Grafiklerin bozulmaması için indirme verisi olmayan satırları eliyoruz
        df = df.dropna(subset=['İndirme Süresi'])

        fname = os.path.basename(file_path).lower()

        # --- DOSYA ADI FORMATI AYRIŞTIRMA ---
        if "_" in fname and "bip" in fname:
            clean_name = fname.replace(".xlsx", "").replace(".csv", "")
            parts = clean_name.split('_')
            
            version = parts[0]   # "5.1.23" veya "5.2.6"
            app_name = "BiP"
            net_raw = parts[2]   # "4.5g" veya "wifi"
            
            type_raw = parts[3] 
            if "hd" in type_raw:
                medya_kalitesi = "HD"
                medya_turu = type_raw.replace("hd", "").capitalize()
            elif "sd" in type_raw:
                medya_kalitesi = "SD"
                medya_turu = type_raw.replace("sd", "").capitalize()
            else:
                medya_kalitesi = "Genel"
                medya_turu = type_raw.capitalize()
        else:
            return None

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
        df['Medya Kalitesi'] = medya_kalitesi
        df['Medya Türü'] = medya_turu

        # Dosya uzantısı ve boyut bilgisini 'Test Adı' sütunundan al
        df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'DİĞER')
        df['Boyut'] = df['Test Adı'].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x))

        return df[['Test Adı', 'Uzantı', 'Boyut', 'İndirme Süresi', 'Uygulama', 'Versiyon', 'Şebeke', 'Grup', 'Medya Kalitesi', 'Medya Türü']]
    except Exception as e:
        st.error(f"⚠️ {os.path.basename(file_path)} işlenirken hata oluştu: {e}")
        return None

# --- SÜRÜM GELİŞİM YORUM MOTORU ---
def surum_gelisim_yorumu(df, metrik_kolonu, metrik_adi):
    if df.empty:
        return "Yorumlanacak veri bulunamadı."

    yorumlar = []
    bip_versions = sorted(list(set(df['Versiyon'].dropna().astype(str))))
    
    if len(bip_versions) < 2:
        return "Karşılaştırma yapabilmek için filtrelerde en az iki farklı BiP sürümü seçili olmalıdır."
        
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
    secilen_gruplar = st.sidebar.multiselect("Grafikte Gösterilecek Versiyonlar:", mevcut_gruplar, default=mevcut_gruplar)

    plot_df = full_df[
        (full_df['Medya Kalitesi'] == secilen_kalite) & 
        (full_df['Medya Türü'] == secilen_tur) & 
        (full_df['Grup'].isin(secilen_gruplar))
    ]

    if not plot_df.empty:
        color_map = {}
        if len(mevcut_gruplar) > 0: color_map[mevcut_gruplar[0]] = '#3498db'
        if len(mevcut_gruplar) > 1: color_map[mevcut_gruplar[1]] = '#1f3a60'

        # --- GRAFİK: İNDİRME (DOWNLOAD) ---
        st.subheader(f"📥 {secilen_kalite} {secilen_tur} Dosyaları - İndirme Performansı Kıyaslaması")
        fig_down = px.bar(
            plot_df, x='Boyut', y='İndirme Süresi', color='Grup',
            facet_col='Şebeke', barmode='group', text_auto=True,
            category_orders={"Şebeke": ["4.5G", "Wi-Fi"], "Grup": mevcut_gruplar},
            color_discrete_map=color_map,
            labels={'İndirme Süresi': 'Süre (ms)', 'Grup': 'BiP Sürümü'}
        )
        st.plotly_chart(fig_down, use_container_width=True)
        st.success(surum_gelisim_yorumu(plot_df, 'İndirme Süresi', 'indirme'))

        with st.expander("📊 Filtrelenmiş Veri Tablosu"):
            st.dataframe(plot_df.sort_values(['Şebeke', 'Boyut', 'Grup']), use_container_width=True)
    else:
        st.warning("Seçilen kriterlere uygun veri bulunamadı. Lütfen sol menüden farklı kombinasyonlar deneyin.")
else:
    st.error("❌ Klasörde geçerli veri içeren BiP .xlsx dosyası bulunamadı!")
