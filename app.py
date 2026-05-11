import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="BiP vs WhatsApp Performans Analizi", layout="wide")

st.title("🚀 BiP & WhatsApp Karşılaştırmalı Performans Raporu")
st.markdown("3G, 4.5G ve Wi-Fi üzerinden yükleme ve indirme sürelerinin analizi.")

# Verileri Hazırlama Fonksiyonu
def veri_hazirla(dosya_adi, uygulama_adi, baglanti_turu):
    df = pd.read_csv(dosya_adi, sep=';')
    # Sütun isimlerini standartlaştıralım (Bazılarında ms yazıyor bazılarında yazmıyor)
    df.columns = [c.replace(' (ms)', '') for c in df.columns]
    
    # Sadece ihtiyacımız olan sütunları alalım
    secili_df = df[['Test Adı', 'Yükleme Süresi', 'İndirme Süresi']].copy()
    secili_df['Uygulama'] = uygulama_adi
    secili_df['Bağlantı'] = baglanti_turu
    return secili_df

# Tüm dosyaları birleştirelim
try:
    dataframes = [
        veri_hazirla('Bip_3G_new.csv', 'BiP', '3G'),
        veri_hazirla('Bip_4.5G_new.csv', 'BiP', '4.5G'),
        veri_hazirla('Bip_Wifi_new.csv', 'BiP', 'Wi-Fi'),
        veri_hazirla('Wa_3G.csv', 'WhatsApp', '3G'),
        veri_hazirla('Wa_4.5G.csv', 'WhatsApp', '4.5G'),
        veri_hazirla('Wa_Wifi.csv', 'WhatsApp', 'Wi-Fi')
    ]
    all_data = pd.concat(dataframes, ignore_index=True)
except Exception as e:
    st.error(f"Veri yüklenirken hata oluştu: {e}")
    all_data = pd.DataFrame()

if not all_data.empty:
    # --- FILTRELER ---
    baglanti_secimi = st.sidebar.multiselect("Bağlantı Türü", all_data['Bağlantı'].unique(), default=['4.5G', 'Wi-Fi'])
    test_secimi = st.sidebar.selectbox("Dosya Boyutu/Tipi Seçin", all_data['Test Adı'].unique())

    filtered_df = all_data[(all_data['Bağlantı'].isin(baglanti_secimi)) & (all_data['Test Adı'] == test_secimi)]

    # --- GRAFİKLER ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"📥 İndirme Süreleri (ms) - {test_secimi}")
        fig_dl = px.bar(filtered_df, x='Bağlantı', y='İndirme Süresi', color='Uygulama', 
                        barmode='group', text_auto=True, color_discrete_map={'BiP': '#00d2ff', 'WhatsApp': '#25D366'})
        st.plotly_chart(fig_dl, use_container_width=True)

    with col2:
        st.subheader(f"📤 Yükleme Süreleri (ms) - {test_secimi}")
        fig_ul = px.bar(filtered_df, x='Bağlantı', y='Yükleme Süresi', color='Uygulama', 
                        barmode='group', text_auto=True, color_discrete_map={'BiP': '#00d2ff', 'WhatsApp': '#25D366'})
        st.plotly_chart(fig_ul, use_container_width=True)

    # --- ÖZET TABLO ---
    st.divider()
    st.subheader("📊 Tüm Test Verileri")
    st.dataframe(all_data, use_container_width=True)
