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
            
        # Eğer gerçek dosyalarınız CSV ise pd.read_csv(file_path) olarak güncelleyebilirsiniz.
        df = pd.read_excel(file_path)
        
        # Sütun isimlerini temizle (Örn: "Yükleme Süresi (ms)" -> "Yükleme Süresi")
        df.columns = [str(c).split(' (')[0].strip() for c in df.columns]
        
        # Dosya adından bilgi çıkarma (Örn: 5.1_Bip_3G.xlsx)
        fname = os.path.basename(file_path).lower()
        parts = fname.split('_')
        
        version = parts[0] # "5.1" veya "5.2"
        app_raw = parts[1] # "bip" veya "wa"
        net_raw = parts[2].replace(".xlsx", "").replace(".csv", "") # Uzantı temizleme
        
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

# --- OTOMATİK YORUM GENERATORÜ ---
def dinamik_yorum_yap(df, metrik_kolonu, metrik_adi):
    if df.empty:
        return "Yorumlanacak veri bulunamadı."
    
    yorumlar = []
    
    # 1. Genel En İyi ve En Kötü Performans
    en_hizli = df.loc[df[metrik_kolonu].idxmin()]
    en_yavas = df.loc[df[metrik_kolonu].idxmax()]
    
    yorumlar.append(f"• **Genel Değerlendirme:** Seçilen filtrelerde en kısa {metrik_adi} süresi **{en_hizli['Boyut']}** dosyasında, **{en_hizli['Grup']}** ile **{en_hizli['Şebeke']}** şebekesinde (**{int(en_hizli[metrik_kolonu]):,} ms**) ölçülmüştür. "
                    f"En uzun süre ise **{en_yavas['Boyut']}** dosyasında, **{en_yavas['Grup']}** ile **{en_yavas['Şebeke']}** şebekesinde (**{int(en_yavas[metrik_kolonu]):,} ms**) görülmüştür.")

    # 2. Şebeke Bazlı Kıyaslama (Ortalamalar)
    sebeke_ort = df.groupby(['Şebeke', 'Uygulama'])[metrik_kolonu].mean().unstack()
    
    sebeke_yorumları = []
    for sebeke in sebeke_ort.index:
        if 'BiP' in sebeke_ort.columns and 'WhatsApp' in sebeke_ort.columns:
            bip_hiz = sebeke_ort.loc[sebeke, 'BiP']
            wa_hiz = sebeke_ort.loc[sebeke, 'WhatsApp']
            if pd.notna(bip_hiz) and pd.notna(wa_hiz):
                if bip_hiz < wa_hiz:
                    fark_yuzde = ((wa_hiz - bip_hiz) / wa_hiz) * 100
                    sebeke_yorumları.append(f"**{sebeke}** şebekesinde **BiP**, WhatsApp'tan ortalama olarak daha hızlıdır.")
                else:
                    fark_yuzde = ((bip_hiz - wa_hiz) / bip_hiz) * 100
                    sebeke_yorumları.append(f"**{sebeke}** şebekesinde **WhatsApp**, BiP'ten ortalama olarak daha hızlıdır.")
                    
    if sebeke_yorumları:
        yorumlar.append(f"• **Şebeke Trendleri:** " + " ".join(sebeke_yorumları))
        
    # 3. Versiyon Gelişimi (V5.1 vs V5.2 Karşılaştırması)
    ver_ort = df.groupby(['Uygulama', 'Versiyon'])[metrik_kolonu].mean().unstack()
    if '5.1' in ver_ort.columns and '5.2' in ver_ort.columns:
        ver_yorumlar = []
        for uyg in ver_ort.index:
            v1 = ver_ort.loc[uyg, '5.1']
            v2 = ver_ort.loc[uyg, '5.2']
            if pd.notna(v1) and pd.notna(v2):
                if v2 < v1:
                    iyilesme = ((v1 - v2) / v1) * 100
                    ver_yorumlar.append(f"**{uyg}** uygulaması V5.2 sürümünde ortalama performansını iyileştirmiştir.")
                else:
                    ver_yorumlar.append(f"**{uyg}** uygulaması V5.2 sürümünde ortalama gecikme süresinde artış yaşamıştır.")
        if ver_yorumlar:
            yorumlar.append(f"• **Sürüm Gelişimleri:** " + " ".join(ver_yorumlar))

    return "\n\n".join(yorumlar)

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
        
        # 1. YÜKLEME SIRA
        st.subheader(f"📤 {secilen_uzanti} - Yükleme Performansı Analizi")
        fig_up = px.bar(
            plot_df, x='Boyut', y='Yükleme Süresi', color='Grup',
            facet_col='Şebeke', barmode='group', text_auto=True,
            category_orders={"Şebeke": ["3G", "4G", "Wi-Fi"]},
            color_discrete_map=color_map,
            labels={'Yükleme Süresi': 'Süre (ms)', 'Grup': 'Uygulama & Versiyon'}
        )
        st.plotly_chart(fig_up, use_container_width=True)
        
        # Yükleme için otomatik yorum alanı
        st.info(dinamik_yorum_yap(plot_df, 'Yükleme Süresi', 'yükleme'))

        st.divider()

        # 2. İNDİRME SIRA
        st.subheader(f"📥 {secilen_uzanti} - İndirme Performansı Analizi")
        fig_down = px.bar(
            plot_df, x='Boyut', y='İndirme Süresi', color='Grup',
            facet_col='Şebeke', barmode='group', text_auto=True,
            category_orders={"Şebeke": ["3G", "4G", "Wi-Fi"]},
            color_discrete_map=color_map,
            labels={'İndirme Süresi': 'Süre (ms)', 'Grup': 'Uygulama & Versiyon'}
        )
        st.plotly_chart(fig_down, use_container_width=True)
        
        # İndirme için otomatik yorum alanı
        st.success(dinamik_yorum_yap(plot_df, 'İndirme Süresi', 'indirme'))

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
