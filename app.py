import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Excel Performans Analizi", layout="wide")

st.title("📊 Veri Tipi & Boyut Bazlı Şebeke Analizi (Excel)")
st.markdown("Excel (.xlsx) dosyalarınızı yükleyin; tüm boyutları ve şebekeleri tek ekranda kıyaslayın.")

# 1. DOSYA YÜKLEME (Excel formatında)
st.sidebar.header("📂 Excel Dosyalarını Yükle")
uploaded_files = st.sidebar.file_uploader("Excel dosyalarını seçin (.xlsx)", type="xlsx", accept_multiple_files=True)

def preprocess_data(file):
    # CSV yerine artık Excel okuyoruz
    df = pd.read_excel(file)
    
    # Sütun temizliği (ms eklerini ve boşlukları kaldırır)
    df.columns = [str(c).split(' (')[0].strip() for c in df.columns]
    
    fname = file.name.lower()
    df['Uygulama'] = "BiP" if "bip" in fname else "WhatsApp"
    
    # Şebeke tespiti
    if "3g" in fname: df['Şebeke'] = "3G"
    elif "4.5g" in fname: df['Şebeke'] = "4.5G"
    else: df['Şebeke'] = "Wi-Fi"
    
    # "10MB.avi" -> Uzantı: "AVI", Boyut: "10MB"
    df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'Diger')
    df['Boyut'] = df['Test Adı'].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x))
    
    return df[['Test Adı', 'Uzantı', 'Boyut', 'Yükleme Süresi', 'İndirme Süresi', 'Uygulama', 'Şebeke']]

if uploaded_files:
    try:
        combined_df = pd.concat([preprocess_data(f) for f in uploaded_files])
        
        # --- FİLTRE: UZANTI SEÇİMİ ---
        uzantilar = sorted(combined_df['Uzantı'].unique())
        secilen_uzanti = st.selectbox("Analiz edilecek Veri Tipini Seçin (Örn: AVI):", uzantilar)
        
        # Seçilen uzantıya ait tüm veriler
        final_df = combined_df[combined_df['Uzantı'] == secilen_uzanti]

        # --- GÖRSELLEŞTİRME (FACET PLOT) ---
        st.divider()
        
        # İNDİRME GRAFİĞİ (Tüm Boyutlar ve Şebekeler)
        st.subheader(f"📥 {secilen_uzanti} Dosyaları: Şebeke & Boyut Bazlı İndirme Süreleri")
        fig_dl = px.bar(final_df, 
                        x='Boyut', 
                        y='İndirme Süresi', 
                        color='Uygulama',
                        facet_col='Şebeke', 
                        barmode='group',
                        text_auto=True,
                        category_orders={"Şebeke": ["3G", "4.5G", "Wi-Fi"], "Boyut": sorted(final_df['Boyut'].unique())},
                        color_discrete_map={'BiP': '#1E90FF', 'WhatsApp': '#25D366'},
                        height=500)
        
        st.plotly_chart(fig_dl, use_container_width=True)

        # YÜKLEME GRAFİĞİ
        st.subheader(f"📤 {secilen_uzanti} Dosyaları: Şebeke & Boyut Bazlı Yükleme Süreleri")
        fig_ul = px.bar(final_df, 
                        x='Boyut', 
                        y='Yükleme Süresi', 
                        color='Uygulama',
                        facet_col='Şebeke',
                        barmode='group',
                        text_auto=True,
                        category_orders={"Şebeke": ["3G", "4.5G", "Wi-Fi"], "Boyut": sorted(final_df['Boyut'].unique())},
                        color_discrete_map={'BiP': '#1E90FF', 'WhatsApp': '#25D366'},
                        height=500)
        
        st.plotly_chart(fig_ul, use_container_width=True)

        # --- SAYISAL MATRİS ---
        with st.expander("Detaylı Veri Tablosunu Görüntüle"):
            st.dataframe(final_df.sort_values(['Şebeke', 'Boyut']), use_container_width=True)

    except Exception as e:
        st.error(f"Dosya işlenirken bir hata oluştu: {e}")
        st.info("İpucu: Excel dosyanızdaki sütun isimlerinin 'Test Adı', 'Yükleme Süresi' ve 'İndirme Süresi' olduğundan emin olun.")

else:
    st.info("Lütfen sol taraftan Excel (.xlsx) dosyalarınızı yükleyin.")
