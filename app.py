import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# Sayfa ayarları
st.set_page_config(page_title="Hız Testi Analiz Merkezi", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP (V5.1 & V5.2) vs WhatsApp Performans Analizi")
st.markdown("""
    Bu panelde iki özel senaryo analiz edilir:
    1. **WhatsApp vs BiP (V5.1):** İki farklı uygulamanın karşılaştırması.
    2. **BiP (V5.1) vs BiP (V5.2):** BiP uygulamasının versiyon gelişimi.
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
            
        # Senaryo 2: 5.1_Bip_3G.xlsx formatı (BiP)
        elif "_" in fname and (fname.startswith('5.1') or fname.startswith('5.2')):
            parts = fname.split('_')
            version = parts[0] # "5.1" veya "5.2"
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
    
    # 1. WHATSAPP vs BIP V5.1 KIYASLAMASI
    wa_df = df[df['Grup'] == 'WhatsApp']
    bip51_df = df[df['Grup'] == 'BiP (V5.1)']
    
    yorumlar.append("### 📊 1. WhatsApp vs BiP (V5.1) Karşılaştırması")
    if not wa_df.empty and not bip51_df.empty:
        # Şebeke bazlı genel ortalamalar
        sebekeler = sorted(list(set(wa_df['Şebeke']).intersection(set(bip51_df['Şebeke']))))
        for seb in sebekeler:
            wa_ort = wa_df[wa_df['Şebeke'] == seb][metrik_kolonu].mean()
            bip_ort = bip51_df[bip51_df['Şebeke'] == seb][metrik_kolonu].mean()
            
            if pd.notna(wa_ort) and pd.notna(bip_ort):
                if bip_ort < wa_ort:
                    fark = ((wa_ort - bip_ort) / wa_ort) * 100
                    yorumlar.append(f"- **{seb} Şebekesinde:** **BiP (V5.1)**, WhatsApp'a göre ortalama {metrik_adi} süresinde **%{fark:.1f} daha hızlıdır**.")
                else:
                    fark = ((bip_ort - wa_ort) / bip_ort) * 100
                    yorumlar.append(f"- **{seb} Şebekesinde:** **WhatsApp**, BiP (V5.1)'e göre ortalama {metrik_adi} süresinde **%{fark:.1f} daha hızlıdır**.")
    else:
        yorumlar.append("- Kıyaslama yapılamadı. Klasörde WhatsApp veya BiP V5.1 dosyalarından biri eksik.")
        
    # 2. BIP V5.1 vs BIP V5.2 GELİŞİM KIYASLAMASI
    bip52_df = df[df['Grup'] == 'BiP (V5.2)']
    
    yorumlar.append("\n### 🔄 2. BiP V5.1 Sürümünden V5.2 Sürümüne Geçiş Analizi")
    if not bip51_df.empty and not bip52_df.empty:
        sebekeler = sorted(list(set(bip51_df['Şebeke']).intersection(set(bip52_df['Şebeke']))))
        for seb in sebekeler:
            v51_ort = bip51_df[bip51_df['Şebeke'] == seb][metrik_kolonu].mean()
            v52_ort = bip52_df[bip52_df['Şebeke'] == seb][metrik_kolonu].mean()
            
            if pd.notna(v51_ort) and pd.notna(v52_ort):
                if v52_ort < v51_ort:
                    iyilesme = ((v51_ort - v52_ort) / v51_ort) * 100
                    yorumlar.append(f"- **{seb} Şebekesinde:** Yeni **V5.2 sürümü**, eski V5.1'e göre {metrik_adi} süresini **%{iyilesme:.1f} azaltarak (hızlandırarak)** performans artışı kaydetmiştir. ✅")
                else:
                    yavaslama = ((v52_ort - v51_ort) / v51_ort) * 100
                    yorumlar.append(f"- **{seb} Şebekesinde:** Yeni **V5.2 sürümünde**, V5.1'e kıyasla %{yavaslama:.1f} oranında bir **yavaşlama (süre artışı)** görülmüştür. ⚠️")
    else:
        yorumlar.append("- Klasörde BiP V5.1 veya V5.2 dosyalarından biri eksik olduğu için sürüm gelişim analizi yapılamadı.")

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
    
    # Ekranda hangi gruplar gösterilsin (Hepsini seçili başlatıyoruz)
    mevcut_gruplar = sorted(full_df['Grup'].unique())
    secilen_gruplar = st.sidebar.multiselect("Grafikte Gösterilecek Gruplar:", mevcut_gruplar, default=mevcut_gruplar)
    
    # Veriyi filtrele
    plot_df = full_df[(full_df['Uzantı'] == secilen_uzanti) & (full_df['Grup'].isin(secilen_gruplar))]

    if not plot_df.empty:
        # Renk Düzeni (WhatsApp Yeşil, BiP Tonları Mavi)
        color_map = {
            'WhatsApp': '#2ecc71',      # Parlak Yeşil
            'BiP (V5.1)': '#3498db',     # Açık Mavi
            'BiP (V5.2)': '#1f3a60'      # Koyu Lacivert
        }

        # --- GRAFİKLER VE DETAYLI YORUMLAR ---
        
        # 1. YÜKLEME (UPLOAD)
        st.subheader(f"📤 {secilen_uzanti} Dosyaları - Yükleme Performansı Kıyaslaması")
        fig_up = px.bar(
            plot_df, x='Boyut', y='Yükleme Süresi', color='Grup',
            facet_col='Şebeke', barmode='group', text_auto=True,
            category_orders={"Şebeke": ["3G", "4G", "Wi-Fi"], "Grup": ["WhatsApp", "BiP (V5.1)", "BiP (V5.2)"]},
            color_discrete_map=color_map,
            labels={'Yükleme Süresi': 'Süre (ms)', 'Grup': 'Uygulama & Sürüm'}
        )
        st.plotly_chart(fig_up, use_container_width=True)
        
        # Yükleme Yorum Alanı
        st.info(ozel_karsilastirma_yorumu(plot_df, 'Yükleme Süresi', 'yükleme'))

        st.divider()

        # 2. İNDİRME (DOWNLOAD)
        st.subheader(f"📥 {secilen_uzanti} Dosyaları - İndirme Performansı Kıyaslaması")
        fig_down = px.bar(
            plot_df, x='Boyut', y='İndirme Süresi', color='Grup',
            facet_col='Şebeke', barmode='group', text_auto=True,
            category_orders={"Şebeke": ["3G", "4G", "Wi-Fi"], "Grup": ["WhatsApp", "BiP (V5.1)", "BiP (V5.2)"]},
            color_discrete_map=color_map,
            labels={'İndirme Süresi': 'Süre (ms)', 'Grup': 'Uygulama & Sürüm'}
        )
        st.plotly_chart(fig_down, use_container_width=True)
        
        # İndirme Yorum Alanı
        st.success(ozel_karsilastirma_yorumu(plot_df, 'İndirme Süresi', 'indirme'))

        # Ham Veri Tablosu
        with st.expander("📊 Filtrelenmiş Veri Tablosu"):
            st.dataframe(plot_df.sort_values(['Şebeke', 'Boyut', 'Grup']), use_container_width=True)
    else:
        st.warning("Seçilen kriterlere uygun veri bulunamadı.")
else:
    st.error("❌ Klasörde eşleşen formatta .xlsx dosyası bulunamadı!")
    st.info("""
    **Beklenen örnek dosya isimleri:**
    - WhatsApp için: `Wa_3G.xlsx`, `Wa_4G.xlsx`, `Wa_Wifi.xlsx`
    - BiP için: `5.1_Bip_3G.xlsx`, `5.2_Bip_4G.xlsx`, `5.2_Bip_Wifi.xlsx`
    """)
