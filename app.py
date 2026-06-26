import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# Sayfa ayarları
st.set_page_config(page_title="Hız Testi Analiz Merkezi", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP Sürüm Gelişimi ve Performans Analizi")
st.markdown("""
    Bu panelde dosyalar **Versiyon_Uygulama_Şebeke_Senaryo** formatına göre otomatik analiz edilir. 
    Grafiklerin altında, seçilen her **Dosya Formatı** ve **Yük Senaryosuna (HDPhoto / SDPhoto)** özel otomatik analitik karşılaştırma yorumları üretilmektedir.
""")

def veri_isle(file_path):
    try:
        if not os.path.exists(file_path):
            return None
            
        # Uzantıya göre esnek okuma (CSV veya Excel)
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
            
        # Sütun isimlerini temizle ve (ms) eklerini kaldır
        df.columns = [str(c).split(' (')[0].strip() for c in df.columns]
        
        # Olası farklı sütun isimlerini standart hale getir
        rename_dict = {}
        for col in df.columns:
            if "İndirme" in col: rename_dict[col] = "İndirme Süresi"
            elif "Yükleme" in col: rename_dict[col] = "Yükleme Süresi"
            elif "Test Adı" in col: rename_dict[col] = "Test Adı"
        df = df.rename(columns=rename_dict)
        
        # Süreleri sayısal tipe zorla
        df["İndirme Süresi"] = pd.to_numeric(df["İndirme Süresi"], errors='coerce')
        df["Yükleme Süresi"] = pd.to_numeric(df["Yükleme Süresi"], errors='coerce')
        
        fname = os.path.basename(file_path).lower()
        
        # --- DİNAMİK DOSYA ADI FORMATI AYRIŞTIRMA ---
        # Örnek: 5.1.23_bip_4.5g_hdphoto.csv
        if "_" in fname:
            parts = fname.split('_')
            version = parts[0].upper()       # "5.1.23" veya "5.2.6"
            app_name = "BiP"
            net_raw = parts[2]               # "4.5g" veya "wifi"
            
            # Senaryo ismini ayıkla (Uzantıyı temizle)
            scenario = parts[3].split('.')[0].upper() # "HDPHOTO" veya "SDPHOTO"
        else:
            return None # Formata uymayan dosyaları es geç
            
        # Şebeke ismini standartlaştır
        if "3g" in net_raw: network = "3G"
        elif "4g" in net_raw or "4.5g" in net_raw: network = "4.5G"
        elif "wifi" in net_raw: network = "Wi-Fi"
        else: network = net_raw.upper()
        
        # DataFrame meta verilerini doldur
        df['Uygulama'] = app_name
        df['Versiyon'] = version
        df['Şebeke'] = network
        df['Senaryo'] = scenario
        df['Grup'] = f"BiP (V{version})"
        
        # "Test Adı" sütunundan Dosya Uzantısını ve Boyut Etiketini Ayıkla
        df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'DİĞER')
        df['Boyut'] = df['Test Adı'].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x))
        
        return df[['Test Adı', 'Uzantı', 'Boyut', 'Yükleme Süresi', 'İndirme Süresi', 'Uygulama', 'Versiyon', 'Şebeke', 'Senaryo', 'Grup']]
    except Exception as e:
        st.error(f"⚠️ {file_path} işlenirken hata oluştu: {e}")
        return None

# --- ÖZEL İKİLİ SÜRÜM GELİŞİM YORUM MOTORU ---
def ozel_glisim_yorumu(df, metrik_kolonu, metrik_adi):
    if df.empty:
        return "Yorumlanacak veri bulunamadı."
        
    yorumlar = []
    
    # Mevcut filtredeki versiyonları bul
    versiyonlar = sorted(df['Versiyon'].unique())
    
    if len(versiyonlar) >= 2:
        v_eski = versiyonlar[0]
        v_yeni = versiyonlar[1]
        
        eski_df = df[df['Versiyon'] == v_eski]
        yeni_df = df[df['Versiyon'] == v_yeni]
        
        sebekeler = sorted(list(set(eski_df['Şebeke']).intersection(set(yeni_df['Şebeke']))))
        
        for seb in sebekeler:
            eski_ort = eski_df[eski_df['Şebeke'] == seb][metrik_kolonu].mean()
            yeni_ort = yeni_df[yeni_df['Şebeke'] == seb][metrik_kolonu].mean()
            
            if pd.notna(eski_ort) and pd.notna(yeni_ort):
                if yeni_ort < eski_ort:
                    iyilesme = ((eski_ort - yeni_ort) / eski_ort) * 100
                    yorumlar.append(f"- **{seb} Altyapısında:** Yeni **V{v_yeni}** sürümü, eski V{v_eski} sürümüne göre ortalama {metrik_adi} süresini **%{iyilesme:.1f} azaltarak (hızlandırarak)** başarılı bir optimizasyon sergilemiştir. ✅")
                else:
                    yavaslama = ((yeni_ort - eski_ort) / eski_ort) * 100
                    yorumlar.append(f"- **{seb} Altyapısında:** Yeni **V{v_yeni}** sürümünde, eski V{v_eski} sürümüne kıyasla ortalama {metrik_adi} süresinde **%{yavaslama:.1f} oranında bir yavaşlama (regresyon)** saptanmıştır. ⚠️")
    else:
        yorumlar.append("- Karşılaştırmalı gelişim analizi için sol menüden en az iki farklı BiP versiyonu seçili olmalıdır.")
        
    return "\n".join(yorumlar)

# --- VERİ TARAMA VE YÜKLEME ---
# Hem .xlsx hem de dönüştürülmüş .csv dosyalarını otomatik tara
dosya_havuzu = glob.glob("*.xlsx") + glob.glob("*.csv")
all_data = []

for f in dosya_havuzu:
    # Dashboard scriptinin kendisini okumaya çalışmasını engelle
    if "streamlit" in f.lower() or f.endswith('.py'):
        continue
    res = veri_isle(f)
    if res is not None:
        all_data.append(res)

if all_data:
    full_df = pd.concat(all_data, ignore_index=True).dropna(subset=['Yükleme Süresi', 'İndirme Süresi'])
    
    # --- YAN MENÜ FİLTRELERİ (SIDEBAR) ---
    st.sidebar.header("⚙️ Analiz ve Filtre Ayarları")
    
    # 1. Yük Senaryosu Filtresi (HDPHOTO / SDPHOTO)
    senaryo_listesi = sorted(full_df['Senaryo'].unique())
    secilen_senaryo = st.sidebar.selectbox("Yük Senaryosu Seçin:", senaryo_listesi)
    
    # 2. Dosya Formatı Filtresi (PNG, JPEG, vb.)
    uzanti_listesi = sorted(full_df[full_df['Senaryo'] == secilen_senaryo]['Uzantı'].unique())
    secilen_uzanti = st.sidebar.selectbox("Dosya Formatı Seçin:", uzanti_listesi)
    
    # 3. Sürüm Filtresi
    mevcut_gruplar = sorted(full_df['Grup'].unique())
    secilen_gruplar = st.sidebar.multiselect("Grafikte Gösterilecek Sürümler:", mevcut_gruplar, default=mevcut_gruplar)
    
    # Ana filtreleme maskesi
    mask = (full_df['Senaryo'] == secilen_senaryo) & \
           (full_df['Uzantı'] == secilen_uzanti) & \
           (full_df['Grup'].isin(secilen_gruplar))
           
    plot_df = full_df[mask]

    if not plot_df.empty:
        # Kurumsal Sürüm Renk Paleti (Açık Mavi -> Koyu Mavi Sürüm Tonlaması)
        color_map = {
            'BiP (V5.1.23)': '#3498db',     # Canlı Açık Mavi
            'BiP (V5.2.6)': '#1f3a60'       # Derin Koyu Lacivert
        }

        # --- GRAFİKLER VE DİNAMİK ANALİZ ALANLARI ---
        st.markdown(f"### 📍 Seçili İnceleme Modu: **{secilen_senaryo}** Senaryosu > **{secilen_uzanti}** Formatı")
        
        # 1. YÜKLEME (UPLOAD) GRAFİĞİ VE YORUMU
        st.subheader("📤 Yükleme Performansı ve Sürümler Arası Kıyaslama")
        fig_up = px.bar(
            plot_df, x='Boyut', y='Yükleme Süresi', color='Grup',
            facet_col='Şebeke', barmode='group', text_auto=True,
            category_orders={"Şebeke": ["3G", "4.5G", "Wi-Fi"], "Grup": ["BiP (V5.1.23)", "BiP (V5.2.6)"]},
            color_discrete_map=color_map,
            labels={'Yükleme Süresi': 'Süre (ms)', 'Grup': 'Uygulama Sürümü'}
        )
        st.plotly_chart(fig_up, use_container_width=True)
        
        # Her yüke özel dinamik yükleme yorum motoru
        st.info(f"💬 **{secilen_senaryo} Yükü İçin Otomatik Yükleme Performans Yorumu:**\n" + 
                ozel_glisim_yorumu(plot_df, 'Yükleme Süresi', 'yükleme'))

        st.divider()

        # 2. İNDİRME (DOWNLOAD) GRAFİĞİ VE YORUMU
        st.subheader("📥 İndirme Performansı ve Sürümler Arası Kıyaslama")
        fig_down = px.bar(
            plot_df, x='Boyut', y='İndirme Süresi', color='Grup',
            facet_col='Şebeke', barmode='group', text_auto=True,
            category_orders={"Şebeke": ["3G", "4.5G", "Wi-Fi"], "Grup": ["BiP (V5.1.23)", "BiP (V5.2.6)"]},
            color_discrete_map=color_map,
            labels={'İndirme Süresi': 'Süre (ms)', 'Grup': 'Uygulama Sürümü'}
        )
        st.plotly_chart(fig_down, use_container_width=True)
        
        # Her yüke özel dinamik indirme yorumu
        st.success(f"💬 **{secilen_senaryo} Yükü İçin Otomatik İndirme Performans Yorumu:**\n" + 
                   ozel_glisim_yorumu(plot_df, 'İndirme Süresi', 'indirme'))

        # Ham Veri İnceleme Matrisi
        with st.expander("📊 Filtrelenmiş Detaylı Ham Veri Matrisi"):
            st.dataframe(plot_df.sort_values(['Şebeke', 'Boyut', 'Grup']), use_container_width=True)
    else:
        st.warning("Seçilen kombinasyona (Senaryo + Uzantı + Sürüm) uygun eşleşen test verisi üretilemedi.")
else:
    st.error("❌ Klasörde tanımlanan isimlendirme formatına uygun veri dosyası saptanamadı!")
    st.info("""
    **Dosyalarınızın şu örnek formatta isimlendirildiğinden emin olun:**
    - `5.1.23_Bip_4.5G_HDPhoto.csv`
    - `5.2.6_Bip_Wifi_SDPhoto.xlsx`
    """)
