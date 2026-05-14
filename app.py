import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Sayfa ayarları
st.set_page_config(page_title="Hız Testi Analiz Merkezi", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP vs WhatsApp Performans Dashboard")
st.markdown("""
    Bu panelde **Yükleme (Upload)** ve **İndirme (Download)** sürelerini alt alta analiz edebilirsiniz. 
    Yeni dosya yüklendiğinde grafikler otomatik olarak güncellenir.
""")

# --- AYARLAR ---
VARSAYILAN_DOSYALAR = [
    "Bip_3G.xlsx", "Bip_4.5G.xlsx", "Bip_Wifi.xlsx",
    "Wa_3G.xlsx", "Wa_4.5G.xlsx", "Wa_Wifi.xlsx"
]

st.sidebar.header("📂 Veri Yönetimi")
uploaded_files = st.sidebar.file_uploader(
    "Yeni Excel dosyalarını buraya sürükleyin", 
    type="xlsx", 
    accept_multiple_files=True
)

def veri_isle(file, is_path=False):
    try:
        df = pd.read_excel(file)
        # Sütun isimlerini temizle
        df.columns = [str(c).split(' (')[0].strip() for c in df.columns]
        
        fname = file if is_path else file.name
        fname = fname.lower()
        
        app_name = "BiP" if "bip" in fname else "WhatsApp"
        
        if "3g" in fname: network = "3G"
        elif "4.5g" in fname: network = "4.5G"
        elif "wifi" in fname or "wi-fi" in fname: network = "Wi-Fi"
        else: network = "Diğer"
        
        df['Uygulama'] = app_name
        df['Şebeke'] = network
        df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'DİĞER')
        df['Boyut'] = df['Test Adı'].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x))
        
        return df[['Test Adı', 'Uzantı', 'Boyut', 'Yükleme Süresi', 'İndirme Süresi', 'Uygulama', 'Şebeke']]
    except Exception as e:
        st.error(f"Hata: {file} okunamadı. Detay: {e}")
        return None

# --- VERİ TOPLAMA ---
final_df_list = []

if uploaded_files:
    st.sidebar.warning("⚠️ Yeni yüklenen dosyalar gösteriliyor.")
    for f in uploaded_files:
        processed = veri_isle(f)
        if processed is not None:
            final_df_list.append(processed)
else:
    st.sidebar.info("✅ Kayıtlı veriler gösteriliyor.")
    for f_name in VARSAYILAN_DOSYALAR:
        target = f_name if os.path.exists(f_name) else (f_name + ".xlsx" if os.path.exists(f_name + ".xlsx") else None)
        if target:
            processed = veri_isle(target, is_path=True)
            if processed is not None:
                final_df_list.append(processed)

# --- GÖRSELLEŞTİRME ---
if final_df_list:
    full_df = pd.concat(final_df_list, ignore_index=True)
    
    uzantilar = sorted(full_df['Uzantı'].unique())
    secilen_uzanti = st.selectbox("Analiz edilecek dosya türünü seçin:", uzantilar)
    
    plot_df = full_df[full_df['Uzantı'] == secilen_uzanti]

    # --- ÜST GRAFİK: YÜKLEME (UPLOAD) ---
    st.subheader(f"📤 {secilen_uzanti} Dosyaları - Yükleme Süreleri (ms)")
    fig_ul = px.bar(plot_df, x='Boyut', y='Yükleme Süresi', color='Uygulama',
                 facet_col='Şebeke', barmode='group', text_auto=True,
                 category_orders={"Şebeke": ["3G", "4.5G", "Wi-Fi"]},
                 color_discrete_map={'BiP': '#1E90FF', 'WhatsApp': '#25D366'},
                 labels={'Yükleme Süresi': 'Süre (ms)', 'Boyut': 'Dosya Boyutu'})
    st.plotly_chart(fig_ul, use_container_width=True)

    st.divider() # Araya bir çizgi ekleyelim

    # --- ALT GRAFİK: İNDİRME (DOWNLOAD) ---
    st.subheader(f"📥 {secilen_uzanti} Dosyaları - İndirme Süreleri (ms)")
    fig_dl = px.bar(plot_df, x='Boyut', y='İndirme Süresi', color='Uygulama',
                 facet_col='Şebeke', barmode='group', text_auto=True,
                 category_orders={"Şebeke": ["3G", "4.5G", "Wi-Fi"]},
                 color_discrete_map={'BiP': '#1E90FF', 'WhatsApp': '#25D366'},
                 labels={'İndirme Süresi': 'Süre (ms)', 'Boyut': 'Dosya Boyutu'})
    st.plotly_chart(fig_dl, use_container_width=True)
    
    # Detaylı Veri Tablosu
    with st.expander("Sayısal Tabloyu Görüntüle"):
        st.dataframe(plot_df.sort_values(['Şebeke', 'Boyut']), use_container_width=True)
else:
    st.error("❌ Veri kaynağı bulunamadı!")
