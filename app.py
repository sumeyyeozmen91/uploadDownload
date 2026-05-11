import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="BiP vs WA Karşılaştırma", layout="wide")

st.title("📶 Bağlantı Bazlı Performans Kıyası: BiP vs WhatsApp")
st.markdown("Sol taraftan 6 dosyanın tamamını yükleyin. Sistem otomatik olarak 3G, 4.5G ve Wifi ayrımı yapacaktır.")

# 1. DOSYA YÜKLEME
st.sidebar.header("📂 Veri Yükleme")
uploaded_files = st.sidebar.file_uploader("CSV Dosyalarını Seçin", type="csv", accept_multiple_files=True)

def preprocess_data(file):
    df = pd.read_csv(file, sep=';')
    # Başlıkları temizle (ms ekini kaldır)
    df.columns = [c.split(' (')[0].strip() for c in df.columns]
    
    fname = file.name.lower()
    df['Uygulama'] = "BiP" if "bip" in fname else "WhatsApp"
    
    if "3g" in fname: df['Bağlantı'] = "3G"
    elif "4.5g" in fname: df['Bağlantı'] = "4.5G"
    else: df['Bağlantı'] = "Wi-Fi"
    
    return df[['Test Adı', 'Yükleme Süresi', 'İndirme Süresi', 'Uygulama', 'Bağlantı']]

if uploaded_files:
    combined_df = pd.concat([preprocess_data(f) for f in uploaded_files])
    
    # --- TEST ADI SEÇİMİ (Filtre) ---
    st.subheader("🎯 Test Bazlı İnceleme")
    selected_test = st.selectbox("Bir Test Seçin (Örn: 10MB.avi):", combined_df['Test Adı'].unique())
    filtered_df = combined_df[combined_df['Test Adı'] == selected_test]

    # --- AYRI AYRI BAĞLANTI KIYASLARI ---
    # Yan yana 3 sütun: 3G | 4.5G | Wi-Fi
    col1, col2, col3 = st.columns(3)
    
    baglantilar = ["3G", "4.5G", "Wi-Fi"]
    column_list = [col1, col2, col3]

    for i, baglanti in enumerate(baglantilar):
        with column_list[i]:
            st.info(f"### {baglanti} Performansı")
            temp_df = filtered_df[filtered_df['Bağlantı'] == baglanti]
            
            if not temp_df.empty:
                # İndirme vs Yükleme kıyaslaması için veriyi eritiyoruz (melt)
                melted_df = temp_df.melt(id_vars=['Uygulama'], value_vars=['İndirme Süresi', 'Yükleme Süresi'], 
                                        var_name='İşlem Türü', value_name='Süre (ms)')
                
                fig = px.bar(melted_df, x='İşlem Türü', y='Süre (ms)', color='Uygulama',
                             barmode='group', text_auto=True,
                             color_discrete_map={'BiP': '#1E90FF', 'WhatsApp': '#25D366'},
                             title=f"{baglanti} - {selected_test}")
                
                fig.update_layout(showlegend=(i==0)) # Sadece ilk grafikte lejant göster
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"{baglanti} için veri bulunamadı.")

    # --- ÖZET ANALİZ NOTU ---
    st.success("💡 **Analiz İpucu:** Sütun boyu ne kadar kısaysa uygulama o kadar hızlı demektir.")

else:
    st.warning("Lütfen sol menüden CSV dosyalarını yükleyin.")
