import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Veri Tipi Analiz Paneli", layout="wide")

st.title("📊 Veri Tipi & Boyut Bazlı Şebeke Analizi")
st.markdown("Bir uzantı seçin (AVI, MP4 vb.); tüm boyutları ve şebekeleri tek ekranda kıyaslayın.")

# 1. DOSYA YÜKLEME
st.sidebar.header("📂 Verileri Yükle")
uploaded_files = st.sidebar.file_uploader("CSV dosyalarını seçin", type="csv", accept_multiple_files=True)

def preprocess_data(file):
    df = pd.read_csv(file, sep=';')
    # Sütun temizliği
    df.columns = [c.split(' (')[0].strip() for c in df.columns]
    
    fname = file.name.lower()
    df['Uygulama'] = "BiP" if "bip" in fname else "WhatsApp"
    
    if "3g" in fname: df['Şebeke'] = "3G"
    elif "4.5g" in fname: df['Şebeke'] = "4.5G"
    else: df['Şebeke'] = "Wi-Fi"
    
    # "10MB.avi" -> "AVI" ve "10MB" olarak ayır
    df['Uzantı'] = df['Test Adı'].apply(lambda x: x.split('.')[-1].upper() if '.' in x else 'Diger')
    df['Boyut'] = df['Test Adı'].apply(lambda x: x.split('.')[0] if '.' in x else x)
    
    return df[['Test Adı', 'Uzantı', 'Boyut', 'Yükleme Süresi', 'İndirme Süresi', 'Uygulama', 'Şebeke']]

if uploaded_files:
    combined_df = pd.concat([preprocess_data(f) for f in uploaded_files])
    
    # --- FİLTRE: SADECE UZANTI SEÇİMİ ---
    uzantilar = sorted(combined_df['Uzantı'].unique())
    secilen_uzanti = st.selectbox("Analiz edilecek Veri Tipini Seçin:", uzantilar)
    
    # Seçilen uzantıya ait tüm veriler
    final_df = combined_df[combined_df['Uzantı'] == secilen_uzanti]

    # --- GÖRSELLEŞTİRME (FACET PLOT) ---
    st.divider()
    
    # İNDİRME GRAFİĞİ
    st.subheader(f"📥 {secilen_uzanti} Dosyaları İçin İndirme Süreleri (Şebeke & Boyut Kıyası)")
    fig_dl = px.bar(final_df, 
                    x='Boyut', 
                    y='İndirme Süresi', 
                    color='Uygulama',
                    facet_col='Şebeke', # Şebekeleri yan yana panellere ayırır
                    barmode='group',
                    text_auto=True,
                    category_orders={"Şebeke": ["3G", "4.5G", "Wi-Fi"], "Boyut": sorted(final_df['Boyut'].unique())},
                    color_discrete_map={'BiP': '#1E90FF', 'WhatsApp': '#25D366'},
                    height=500)
    
    fig_dl.update_layout(margin=dict(t=50, b=50))
    st.plotly_chart(fig_dl, use_container_width=True)

    # YÜKLEME GRAFİĞİ
    st.subheader(f"📤 {secilen_uzanti} Dosyaları İçin Yükleme Süreleri (Şebeke & Boyut Kıyası)")
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

    # --- ÖZET MATRİS TABLOSU ---
    st.subheader("📋 Özet Performans Matrisi")
    # Satırlarda Boyut, sütunlarda Şebeke ve Uygulama olacak şekilde pivot
    matrix_df = final_df.pivot_table(
        index=['Boyut'], 
        columns=['Şebeke', 'Uygulama'], 
        values='İndirme Süresi'
    )
    st.write("Veriler milisaniye (ms) cinsinden 'İndirme Süresi'ni göstermektedir:")
    st.dataframe(matrix_df, use_container_width=True)

else:
    st.info("Lütfen sol taraftan 6 adet CSV dosyasını (Bip/Wa + 3G/4.5G/Wifi) yükleyin.")
