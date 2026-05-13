import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Performans Analiz Merkezi", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP vs WhatsApp Hız Analiz Raporu")
st.markdown("""
    Bu panel, kayıtlı olan en son test sonuçlarını gösterir. 
    **Yeni bir test yaptıysanız**, sol taraftan Excel dosyalarını yükleyerek raporu güncelleyebilirsiniz.
""")

# --- AYARLAR ---
VARSAYILAN_DOSYALAR = [
    "Bip_3G.xlsx", "Bip_4.5G.xlsx", "Bip_Wifi.xlsx",
    "Wa_3G.xlsx", "Wa_4.5G.xlsx", "Wa_Wifi.xlsx"
]

st.sidebar.header("📂 Veri Kontrolü")
uploaded_files = st.sidebar.file_uploader(
    "Yeni Excel dosyalarını buraya sürükleyin", 
    type="xlsx", 
    accept_multiple_files=True
)

def veri_isle(file, is_path=False):
    """Hem yüklenen dosyaları hem de yerel yolları okuyan fonksiyon"""
    try:
        df = pd.read_excel(file)
        # Sütun başlıklarını temizle
        df.columns = [str(c).split(' (')[0].strip() for c in df.columns]
        
        # Dosya adını belirle
        fname = file if is_path else file.name
        fname = fname.lower()
        
        # Uygulama ve Şebeke tespiti
        app_name = "BiP" if "bip" in fname else "WhatsApp"
        network = "3G" if "3g" in fname else ("4.5G" if "4.5g" in fname else "Wi-Fi")
        
        df['Uygulama'] = app_name
        df['Şebeke'] = network
        df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'DİĞER')
        df['Boyut'] = df['Test Adı'].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x))
        
        return df[['Test Adı', 'Uzantı', 'Boyut', 'Yükleme Süresi', 'İndirme Süresi', 'Uygulama', 'Şebeke']]
    except Exception as e:
        st.error(f"Hata: {file} okunamadı. {e}")
        return None

# --- VERİ KAYNAĞI SEÇİMİ ---
final_df_list = []

if uploaded_files:
    # EĞER YENİ DOSYA YÜKLENDİYSE
    st.sidebar.warning("⚠️ Yeni yüklenen dosyalar gösteriliyor.")
    for f in uploaded_files:
        processed = veri_isle(f)
        if processed is not None:
            final_list.append(processed)
else:
    # EĞER DOSYA YÜKLENMEDİYSE (REFRESH DURUMU)
    st.sidebar.info("✅ GitHub'daki güncel sonuçlar gösteriliyor.")
    for f_name in VARSAYILAN_DOSYALAR:
        if os.path.exists(f_name):
            processed = veri_isle(f_name, is_path=True)
            if processed is not None:
                final_df_list.append(processed)

# --- GÖRSELLEŞTİRME ---
if final_df_list:
    full_df = pd.concat(final_df_list, ignore_index=True)
    
    # Uzantı seçimi
    uzantilar = sorted(full_df['Uzantı'].unique())
    secilen_uzanti = st.selectbox("Analiz edilecek dosya türünü seçin:", uzantilar)
    
    plot_df = full_df[full_df['Uzantı'] == secilen_uzanti]

    # Panel Grafiği (3G, 4.5G, Wi-Fi yan yana)
    st.subheader(f"📊 {secilen_uzanti} Dosyaları İçin Tüm Şebekelerdeki Performans")
    
    fig = px.bar(plot_df, x='Boyut', y='İndirme Süresi', color='Uygulama',
                 facet_col='Şebeke', barmode='group', text_auto=True,
                 category_orders={"Şebeke": ["3G", "4.5G", "Wi-Fi"]},
                 color_discrete_map={'BiP': '#1E90FF', 'WhatsApp': '#25D366'},
                 labels={'İndirme Süresi': 'Süre (ms)', 'Boyut': 'Dosya Boyutu'})
    
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
    
    # Detaylı Tablo
    with st.expander("Sayısal Verileri İncele"):
        st.dataframe(plot_df.sort_values(['Şebeke', 'Boyut']), use_container_width=True)
else:
    st.warning("Henüz veri kaynağı bulunamadı. Lütfen GitHub'a Excel dosyalarını ekleyin veya buradan yükleyin.")
