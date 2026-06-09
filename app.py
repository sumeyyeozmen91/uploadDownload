import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Sayfa ayarları
st.set_page_config(page_title="Hız Testi Analiz Merkezi", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP vs WhatsApp Performans Kıyaslama (V5.1 & V5.2)")
st.markdown("""
    Bu panelde dosyalar **Versiyon_Uygulama_Şebeke** formatına göre otomatik analiz edilir. 
    Örn: `5.1_Bip_3G.xlsx` veya `5.2_Wa_Wifi.xlsx`
""")

# --- YAPILANDIRMA ---
VERSİYONLAR = ["5.1", "5.2"]
UYGULAMALAR = ["Bip", "Wa"]
ŞEBEKELER = ["3G", "4G", "Wifi"]

# Yeni formata göre dosya listesi oluşturma: "5.1_Bip_3G.xlsx"
VARSAYILAN_DOSYALAR = [
    f"{ver}_{app}_{net}.xlsx" 
    for ver in VERSİYONLAR 
    for app in UYGULAMALAR 
    for net in ŞEBEKELER
]

def veri_isle(file_path):
    try:
        if not os.path.exists(file_path):
            return None
            
        df = pd.read_excel(file_path)
        
        # Sütun isimlerini temizle (Örn: "Yükleme Süresi (ms)" -> "Yükleme Süresi")
        df.columns = [str(c).split(' (')[0].strip() for c in df.columns]
        
        # Dosya adından bilgi çıkarma (Örn: 5.1_Bip_3G.xlsx)
        fname = os.path.basename(file_path).lower()
        parts = fname.split('_')
        
        version = parts[0] # "5.1" veya "5.2"
        app_raw = parts[1] # "bip" veya "wa"
        net_raw = parts[2].replace(".xlsx", "") # "3g", "4g" veya "wifi"
        
        # Etiketleri düzenle
        app_name = "BiP" if "bip" in app_raw else "WhatsApp"
        
        if "3g" in net_raw: network = "3G"
        elif "4g" in net_raw or "4g" in net_raw: network = "4G"
        elif "wifi" in net_raw: network = "Wi-Fi"
        else: network = net_raw.upper()
        
        # Veri setine ekle
        df['Uygulama'] = app_name
        df['Versiyon'] = version
        df['Şebeke'] = network
        df['Grup'] = f"{app_name} (V{version})"
        
        # Dosya uzantısı ve boyutu çıkarma (Test Adı sütunundan)
        df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'DİĞER')
        df['Boyut'] = df['Test Adı'].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x))
        
        return df[['Test Adı', 'Uzantı', 'Boyut', 'Yükleme Süresi', 'İndirme Süresi', 'Uygulama', 'Versiyon', 'Şebeke', 'Grup']]
    except Exception as e:
        st.error(f"⚠️ {file_path} işlenirken hata oluştu: {e}")
        return None

# --- VERİ YÜKLEME ---
all_data = []
for f in VARSAYILAN_DOSYALAR:
    res = veri_isle(f)
    if res is not None:
        all_data.append(res)

if all_data:
    full_df = pd.concat(all_data, ignore_index=True)
    
    # --- FİLTRELER (SIDEBAR) ---
    st.sidebar.header("⚙️ Analiz Ayarları")
    
    uzanti_listesi = sorted(full_df['Uzantı'].unique())
    secilen_uzanti = st.sidebar.selectbox("Dosya Formatı Seçin:", uzanti_listesi)
    
    secilen_versiyonlar = st.sidebar.multiselect(
        "Versiyonları Kıyasla:", 
        VERSİYONLAR, 
        default=VERSİYONLAR
    )
    
    # Filtreleme uygula
    mask = (full_df['Uzantı'] == secilen_uzanti) & (full_df['Versiyon'].isin(secilen_versiyonlar))
    plot_df = full_df[mask]

    if not plot_df.empty:
        # Renk paleti (Versiyon bazlı tonlama)
        color_map = {
            'BiP (V5.1)': '#3498db',       # Açık Mavi
            'BiP (V5.2)': '#2980b9',       # Koyu Mavi
            'WhatsApp (V5.1)': '#2ecc71',  # Açık Yeşil
            'WhatsApp (V5.2)': '#27ae60'   # Koyu Yeşil
        }

        # --- GRAFİKLER ---
        
        # 1. YÜKLEME
        st.subheader(f"📤 {secilen_uzanti} - Yükleme Performansı")
        fig_up = px.bar(
            plot_df, x='Boyut', y='Yükleme Süresi', color='Grup',
            facet_col='Şebeke', barmode='group', text_auto=True,
            category_orders={"Şebeke": ["3G", "4G", "Wi-Fi"]},
            color_discrete_map=color_map,
            labels={'Yükleme Süresi': 'Süre (ms)', 'Grup': 'Uygulama & Versiyon'}
        )
        st.plotly_chart(fig_up, use_container_width=True)

        st.divider()

        # 2. İNDİRME
        st.subheader(f"📥 {secilen_uzanti} - İndirme Performansı")
        fig_down = px.bar(
            plot_df, x='Boyut', y='İndirme Süresi', color='Grup',
            facet_col='Şebeke', barmode='group', text_auto=True,
            category_orders={"Şebeke": ["3G", "4G", "Wi-Fi"]},
            color_discrete_map=color_map,
            labels={'İndirme Süresi': 'Süre (ms)', 'Grup': 'Uygulama & Versiyon'}
        )
        st.plotly_chart(fig_down, use_container_width=True)

        # Tablo Görünümü
        with st.expander("📊 Ham Veri Tablosu"):
            st.dataframe(plot_df.sort_values(['Şebeke', 'Boyut', 'Versiyon']), use_container_width=True)
    else:
        st.warning("Seçilen filtrelere uygun veri bulunamadı.")
else:
    st.error("❌ Veri dosyaları bulunamadı!")
    st.info("""
    Lütfen Excel dosyalarınızın script ile aynı klasörde ve şu isimlerde olduğundan emin olun:
    - **5.1_Bip_3G.xlsx**, **5.2_Bip_4G.xlsx**, **5.1_Wa_Wifi.xlsx** vb.
    """)
