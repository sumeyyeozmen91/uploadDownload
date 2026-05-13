import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Sayfa ayarları
st.set_page_config(page_title="Hız Testi Analiz Merkezi", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP vs WhatsApp Hız Analiz Raporu")
st.markdown("""
    Bu panel, kayıtlı olan en son test sonuçlarını gösterir. 
    **Yeni bir test yaptıysanız**, sol taraftan Excel dosyalarını yükleyerek raporu güncelleyebilirsiniz.
""")

# --- AYARLAR ---
# GitHub'daki dosya isimlerinle buradakilerin karakteri karakterine aynı olması gerekir.
# Eğer GitHub'da isimler "Bip_3G.xlsx.xlsx" şeklindeyse burayı da öyle düzeltmelisin.
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
    """Hem yüklenen dosyaları hem de GitHub'daki yolları okuyan fonksiyon"""
    try:
        df = pd.read_excel(file)
        # Sütun başlıklarını temizle
        df.columns = [str(c).split(' (')[0].strip() for c in df.columns]
        
        # Dosya adını belirle ve şebeke tespiti için temizle
        fname = file if is_path else file.name
        fname = fname.lower()
        
        # Uygulama Tespiti
        app_name = "BiP" if "bip" in fname else "WhatsApp"
        
        # Şebeke Tespiti (Sağa kaymayı önlemek için isimleri standartlaştırıyoruz)
        if "3g" in fname:
            network = "3G"
        elif "4.5g" in fname:
            network = "4.5G"
        elif "wifi" in fname or "wi-fi" in fname:
            network = "Wi-Fi"
        else:
            network = "Diğer"
        
        df['Uygulama'] = app_name
        df['Şebeke'] = network
        
        # Uzantı ve Boyut ayırma
        df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'DİĞER')
        df['Boyut'] = df['Test Adı'].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x))
        
        return df[['Test Adı', 'Uzantı', 'Boyut', 'Yükleme Süresi', 'İndirme Süresi', 'Uygulama', 'Şebeke']]
    except Exception as e:
        st.error(f"Hata: {file} okunamadı. Bilgi: {e}")
        return None

# --- VERİ KAYNAĞI SEÇİMİ ---
final_df_list = []

if uploaded_files:
    # 1. Senaryo: Yeni dosya yüklendiyse
    st.sidebar.warning("⚠️ Yeni yüklenen dosyalar gösteriliyor.")
    for f in uploaded_files:
        processed = veri_isle(f)
        if processed is not None:
            final_df_list.append(processed)
else:
    # 2. Senaryo: GitHub'daki dosyaları kullan
    st.sidebar.info("✅ GitHub'daki güncel sonuçlar gösteriliyor.")
    for f_name in VARSAYILAN_DOSYALAR:
        # GitHub'daki çift .xlsx hatasını toleransla karşılamak için kontrol
        if os.path.exists(f_name):
            target = f_name
        elif os.path.exists(f_name + ".xlsx"):
            target = f_name + ".xlsx"
        else:
            target = None
            
        if target:
            processed = veri_isle(target, is_path=True)
            if processed is not None:
                final_df_list.append(processed)

# --- GÖRSELLEŞTİRME ---
if final_df_list:
    full_df = pd.concat(final_df_list, ignore_index=True)
    
    # Filtre
    uzantilar = sorted(full_df['Uzantı'].unique())
    secilen_uzanti = st.selectbox("Analiz edilecek dosya türünü seçin:", uzantilar)
    
    plot_df = full_df[full_df['Uzantı'] == secilen_uzanti]

    # Grafik
    st.subheader(f"📊 {secilen_uzanti} Dosyaları İçin Tüm Şebekelerdeki Performans")
    
    fig = px.bar(plot_df, x='Boyut', y='İndirme Süresi', color='Uygulama',
                 facet_col='Şebeke', barmode='group', text_auto=True,
                 # Şebeke sırasını sabitliyoruz
                 category_orders={"Şebeke": ["3G", "4.5G", "Wi-Fi"]},
                 color_discrete_map={'BiP': '#1E90FF', 'WhatsApp': '#25D366'},
                 labels={'İndirme Süresi': 'Süre (ms)', 'Boyut': 'Dosya Boyutu'})
    
    # Görsel iyileştirme
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
    
    # Detaylı Tablo
    with st.expander("Sayısal Verileri İncele"):
        st.dataframe(plot_df.sort_values(['Şebeke', 'Boyut']), use_container_width=True)
else:
    st.error("❌ Veri bulunamadı! Lütfen GitHub'daki dosya isimlerini veya yüklediğiniz dosyaları kontrol edin.")
