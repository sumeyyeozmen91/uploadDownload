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

# Formata göre dosya listesi oluşturma: "5.1_Bip_3G.xlsx"
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
        elif "4g" in net_raw: network = "4G"
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

# --- OTOMATİK YORUM FONKSİYONU ---
def otomatik_yorum_yap(df_sub):
    """Her dosya tipi için verileri inceleyip otomatik performans yorumu üretir."""
    try:
        yorumlar = []
        
        # En hızlı indirme ve yükleme senaryolarını bulma
        en_hizli_indirme = df_sub.loc[df_sub['İndirme Süresi'].idxmin()]
        en_hizli_yukleme = df_sub.loc[df_sub['Yükleme Süresi'].idxmin()]
        
        # Uygulama bazlı genel ortalamalar
        ortalamalar = df_sub.groupby('Uygulama')[['İndirme Süresi', 'Yükleme Süresi']].mean()
        
        yorumlar.append(f"**⏱️ Genel Özet:**")
        if len(ortalamalar) > 1:
            bip_indirme = ortalamalar.loc['BiP', 'İndirme Süresi'] if 'BiP' in ortalamalar.index else 999999
            wa_indirme = ortalamalar.loc['WhatsApp', 'İndirme Süresi'] if 'WhatsApp' in ortalamalar.index else 999999
            
            if bip_indirme < wa_indirme:
                oran = (wa_indirme - bip_indirme) / wa_indirme * 100
                yorumlar.append(f"- Bu dosya tipinde **BiP**, WhatsApp'a kıyasla ortalamada **%{oran:.1f} daha hızlı** indirme performansı gösteriyor.")
            else:
                oran = (bip_indirme - wa_indirme) / bip_indirme * 100
                yorumlar.append(f"- Bu dosya tipinde **WhatsApp**, BiP'e kıyasla ortalamada **%{oran:.1f} daha hızlı** indirme performansı gösteriyor.")
        
        yorumlar.append(f"**⚡ Rekor Performanslar:**")
        yorumlar.append(f"- **En Kısa İndirme Süresi:** {en_hizli_indirme['İndirme Süresi']} ms ile **{en_hizli_indirme['Grup']}** tarafından **{en_hizli_indirme['Şebeke']}** ağında ({en_hizli_indirme['Boyut']} dosyası için) elde edilmiştir.")
        yorumlar.append(f"- **En Kısa Yükleme Süresi:** {en_hizli_yukleme['Yükleme Süresi']} ms ile **{en_hizli_yukleme['Grup']}** tarafından **{en_hizli_yukleme['Şebeke']}** ağında ({en_hizli_yukleme['Boyut']} dosyası için) elde edilmiştir.")
        
        # Versiyon kıyaslaması (5.1 vs 5.2)
        v_ortalamalar = df_sub.groupby('Versiyon')[['İndirme Süresi', 'Yükleme Süresi']].mean()
        if '5.1' in v_ortalamalar.index and '5.2' in v_ortalamalar.index:
            yorumlar.append(f"**🔄 Versiyon Gelişimi:**")
            v51_dl = v_ortalamalar.loc['5.1', 'İndirme Süresi']
            v52_dl = v_ortalamalar.loc['5.2', 'İndirme Süresi']
            if v52_dl < v51_dl:
                gelişim = (v51_dl - v52_dl) / v51_dl * 100
                yorumlar.append(f"- **V5.2 versiyonu**, V5.1'e göre indirme sürelerini genel olarak **%{gelişim:.1f} oranında iyileştirmiş** görünüyor.")
            else:
                yorumlar.append(f"- V5.2 versiyonunda bu dosya tipi için indirme sürelerinde belirgin bir optimizasyon artışı gözlemlenmedi.")

        return "\n".join(yorumlar)
    except:
        return "Bu dosya tipi için otomatik yorum üretilemedi."

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
    
    secilen_versiyonlar = st.sidebar.multiselect(
        "Versiyonları Kıyasla:", 
        VERSİYONLAR, 
        default=VERSİYONLAR
    )
    
    # Renk paleti (Versiyon bazlı tonlama)
    color_map = {
        'BiP (V5.1)': '#3498db',       # Açık Mavi
        'BiP (V5.2)': '#2980b9',       # Koyu Mavi
        'WhatsApp (V5.1)': '#2ecc71',  # Açık Yeşil
        'WhatsApp (V5.2)': '#27ae60'   # Koyu Yeşil
    }

    # Benzersiz dosya uzantılarını alıp sekmeler (tabs) oluşturma
    uzanti_listesi = sorted(full_df['Uzantı'].unique())
    
    if uzanti_listesi:
        st.info(f"📊 Toplam {len(uzanti_listesi)} farklı dosya tipi tespit edildi. Sekmelerden inceleyebilirsiniz.")
        
        # Her dosya tipi için bir sekme oluştur
        sekmeler = st.tabs([f"📄 {uz} Formatı" for uz in uzanti_listesi])
        
        for i, uzanti in enumerate(uzanti_listesi):
            with sekmeler[i]:
                # Sadece bu sekmeye ait dosya uzantısını ve seçilen versiyonları filtrele
                mask = (full_df['Uzantı'] == uzanti) & (full_df['Versiyon'].isin(secilen_versiyonlar))
                plot_df = full_df[mask]
                
                if not plot_df.empty:
                    st.header(f"🎯 {uzanti} Formatı Performans Raporu")
                    
                    # --- OTOMATİK ANALİZ VE YORUM ALANI ---
                    st.subheader("💡 Yapay Zeka / Otomatik Veri Yorumu")
                    yorum_metni = otomatik_yorum_yap(plot_df)
                    st.info(yorum_metni)
                    
                    # Grafik düzeni için iki kolon oluşturma
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("📤 Yükleme Performansı")
                        fig_up = px.bar(
                            plot_df, x='Boyut', y='Yükleme Süresi', color='Grup',
                            facet_col='Şebeke', barmode='group', text_auto=True,
                            category_orders={"Şebeke": ["3G", "4G", "Wi-Fi"]},
                            color_discrete_map=color_map,
                            labels={'Yükleme Süresi': 'Süre (ms)', 'Grup': 'Uygulama & Versiyon'}
                        )
                        fig_up.update_layout(margin=dict(l=20, r=20, t=40, b=20))
                        st.plotly_chart(fig_up, use_container_width=True)
                        
                    with col2:
                        st.subheader("📥 İndirme Performansı")
                        fig_down = px.bar(
                            plot_df, x='Boyut', y='İndirme Süresi', color='Grup',
                            facet_col='Şebeke', barmode='group', text_auto=True,
                            category_orders={"Şebeke": ["3G", "4G", "Wi-Fi"]},
                            color_discrete_map=color_map,
                            labels={'İndirme Süresi': 'Süre (ms)', 'Grup': 'Uygulama & Versiyon'}
                        )
                        fig_down.update_layout(margin=dict(l=20, r=20, t=40, b=20))
                        st.plotly_chart(fig_down, use_container_width=True)
                    
                    st.divider()
                    
                    # Tablo Görünümü
                    with st.expander(f"📊 {uzanti} Formatı Ham Veri Tablosu"):
                        st.dataframe(plot_df.sort_values(['Şebeke', 'Boyut', 'Versiyon']), use_container_width=True)
                else:
                    st.warning("Seçilen filtrelere uygun veri bulunamadı.")
    else:
        st.warning("Dosyalardan hiçbir uzantı bilgisi çıkarılamadı.")
else:
    st.error("❌ Veri dosyaları bulunamadı!")
    st.info("""
    Lütfen Excel dosyalarınızın script ile aynı klasörde ve şu isimlerde olduğundan emin olun:
    - **5.1_Bip_3G.xlsx**, **5.2_Bip_4G.xlsx**, **5.1_Wa_Wifi.xlsx** vb.
    """)
