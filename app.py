import streamlit as st
import pandas as pd
import plotly.express as px

# Sayfa Genişliği ve Başlık
st.set_page_config(page_title="Hız Testi Karşılaştırma", layout="wide")

st.title("🚀 BiP vs WhatsApp Performans Analizi")
st.markdown("Aşağıdaki alana CSV dosyalarını yükleyerek karşılaştırmalı raporu oluşturabilirsiniz.")

# 1. DOSYA YÜKLEME ALANI
st.sidebar.header("📂 Dosyaları Yükle")
uploaded_files = st.sidebar.file_uploader(
    "CSV dosyalarını buraya sürükleyin (Çoklu seçim yapabilirsiniz)", 
    type="csv", 
    accept_multiple_files=True
)

def veri_temizle(df, dosya_adi):
    # Sütun isimlerini standartlaştıralım (ms ifadelerini ve boşlukları temizler)
    df.columns = [c.split(' (')[0].strip() for c in df.columns]
    
    # Dosya adından Uygulama ve Bağlantı türünü çıkaralım
    adi_dusuk = dosya_adi.lower()
    uygulama = "BiP" if "bip" in adi_dusuk else "WhatsApp"
    baglanti = "3G" if "3g" in adi_dusuk else ("4.5G" if "4.5g" in adi_dusuk else "Wi-Fi")
    
    # Sadece gerekli sütunları alalım
    df = df[['Test Adı', 'Yükleme Süresi', 'İndirme Süresi']].copy()
    df['Uygulama'] = uygulama
    df['Bağlantı'] = baglanti
    return df

# Veri işleme süreci
if uploaded_files:
    all_data_list = []
    for uploaded_file in uploaded_files:
        # Senin dosyaların ';' ile ayrılmış olduğu için sep=';' ekledik
        df_raw = pd.read_csv(uploaded_file, sep=';')
        df_clean = veri_temizle(df_raw, uploaded_file.name)
        all_data_list.append(df_clean)
    
    full_df = pd.concat(all_data_list, ignore_index=True)

    # --- Üst Metrikler (KPI) ---
    st.subheader("📌 Genel Özet")
    c1, c2, c3 = st.columns(3)
    avg_dl = full_df.groupby('Uygulama')['İndirme Süresi'].mean().reset_index()
    
    with c1:
        st.metric("Toplam Test Sayısı", len(full_df))
    with c2:
        bip_avg = avg_dl[avg_dl['Uygulama'] == 'BiP']['İndirme Süresi'].values[0]
        st.metric("BiP Ort. İndirme", f"{int(bip_avg)} ms")
    with c3:
        wa_avg = avg_dl[avg_dl['Uygulama'] == 'WhatsApp']['İndirme Süresi'].values[0]
        st.metric("WhatsApp Ort. İndirme", f"{int(wa_avg)} ms")

    st.divider()

    # --- Görsel Karşılaştırma ---
    # Kullanıcı belirli bir testi (örn: 10MB.avi) seçebilsin
    test_listesi = full_df['Test Adı'].unique()
    secilen_test = st.selectbox("Analiz etmek istediğiniz Testi seçin:", test_listesi)
    
    plot_df = full_df[full_df['Test Adı'] == secilen_test]

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📥 İndirme Süreleri (ms)")
        fig_dl = px.bar(plot_df, x='Bağlantı', y='İndirme Süresi', color='Uygulama',
                        barmode='group', text_auto=True,
                        color_discrete_map={'BiP': '#00d2ff', 'WhatsApp': '#25D366'})
        st.plotly_chart(fig_dl, use_container_width=True)

    with col_right:
        st.subheader("📤 Yükleme Süreleri (ms)")
        fig_ul = px.bar(plot_df, x='Bağlantı', y='Yükleme Süresi', color='Uygulama',
                        barmode='group', text_auto=True,
                        color_discrete_map={'BiP': '#00d2ff', 'WhatsApp': '#25D366'})
        st.plotly_chart(fig_ul, use_container_width=True)

    # Veri Tablosu
    with st.expander("Tüm Verileri Tablo Olarak Gör"):
        st.write(full_df)

else:
    st.info("💡 Devam etmek için lütfen sol taraftaki menüden CSV dosyalarınızı seçin.")
