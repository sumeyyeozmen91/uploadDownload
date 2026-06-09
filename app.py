import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# Sayfa ayarları
st.set_page_config(page_title="Hız Testi Analiz Merkezi", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP vs WhatsApp Performans Kıyaslama (V5.1 & V5.2)")
st.markdown("""
    Bu panelde dosyalar **Versiyon_Uygulama_Şebeke** formatına göre otomatik analiz edilir. 
    Örn: `5.1_Bip_3G.xlsx` veya `5.2_Wa_4G.xlsx`
""")

def veri_isle(file_path):
    try:
        if not os.path.exists(file_path):
            return None
            
        df = pd.read_excel(file_path)
        
        # Sütun isimlerini temizle
        df.columns = [str(c).split(' (')[0].strip() for c in df.columns]
        
        # Dosya adından bilgi çıkarma (Harf duyarlılığını kaldırmak için lower yapıyoruz)
        fname = os.path.basename(file_path).lower()
        parts = fname.split('_')
        
        if len(parts) < 3:
            return None # Hatalı isimlendirilmiş dosyaları atla
            
        version = parts[0] # "5.1" veya "5.2"
        app_raw = parts[1] # "bip" veya "wa" / "whatsapp"
        net_raw = parts[2].replace(".xlsx", "").replace(".csv", "")
        
        # Uygulama ismini standartlaştır
        app_name = "BiP" if "bip" in app_raw else "WhatsApp"
        
        # Şebeke ismini standartlaştır (4.5g veya 4g gelirse ortak '4G' yap)
        if "3g" in net_raw: network = "3G"
        elif "4g" in net_raw or "4.5g" in net_raw: network = "4G"
        elif "wifi" in net_raw: network = "Wi-Fi"
        else: network = net_raw.upper()
        
        df['Uygulama'] = app_name
        df['Versiyon'] = version
        df['Şebeke'] = network
        df['Grup'] = f"{app_name} (V{version})"
        
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
    
    yorumlar.append(f"📌 **Genel Değerlendirme:** Seçilen filtrelerde en kısa {metrik_adi} süresi **{en_hizli['Boyut']}** dosyasında, **{en_hizli['Grup']}** ile **{en_hizli['Şebeke']}** şebekesinde (**{int(en_hizli[metrik_kolonu]):,} ms**) ölçülmüştür. "
                    f"En uzun süre ise **{en_yavas['Boyut']}** dosyasında, **{en_yavas['Grup']}** ile **{en_yavas['Şebeke']}** şebekesinde (**{int(en_yavas[metrik_kolonu]):,} ms**) görülmüştür.")

    # 2. Şebeke Bazlı WhatsApp vs BiP Kıyaslaması
    sebeke_ort = df.groupby(['Şebeke', 'Uygulama'])[metrik_kolonu].mean().unstack()
    
    sebeke_yorumları = []
    for sebeke in sebeke_ort.index:
        columns_present = sebeke_ort.columns
        if 'BiP' in columns_present and 'WhatsApp' in columns_present:
            bip_hiz = sebeke_ort.loc[sebeke, 'BiP']
            wa_hiz = sebeke_ort.loc[sebeke, 'WhatsApp']
            if pd.notna(bip_hiz) and pd.notna(wa_hiz):
                if bip_hiz < wa_hiz:
                    fark_yuzde = ((wa_hiz - bip_hiz) / wa_hiz) * 100
                    sebeke_yorumları.append(f"**{sebeke}** ağında **BiP**, WhatsApp'a göre ortalamada **%{fark_yuzde:.1f} daha hızlı** sonuç vermiştir.")
                else:
                    fark_yuzde = ((bip_hiz - wa_hiz) / bip_hiz) * 100
                    sebeke_yorumları.append(f"**{sebeke}** ağında **WhatsApp**, BiP'e göre ortalamada **%{fark_yuzde:.1f} daha hızlı** sonuç vermiştir.")
        else:
            # Eğer sadece biri varsa kullanıcıyı uyar
            mevcut_uyg = columns_present[0] if len(columns_present) > 0 else ""
            if mevcut_uyg:
                sebeke_yorumları.append(f"**{sebeke}** ağında karşılaştırma yapılamadı çünkü sadece **{mevcut_uyg}** verisi mevcut.")
                    
    if sebeke_yorumları:
        yorumlar.append(f"📶 **WhatsApp vs BiP Trendleri:**\n" + "\n".join([f"- {s}" for s in sebeke_yorumları]))
        
    # 3. BiP 5.1 vs BiP 5.2 Karşılaştırması
    bip_df = df[df['Uygulama'] == 'BiP']
    if not bip_df.empty:
        bip_ver_ort = bip_df.groupby('Versiyon')[metrik_kolonu].mean()
        if '5.1' in bip_ver_ort.index and '5.2' in bip_ver_ort.index:
            v51_bip = bip_ver_ort['5.1']
            v52_bip = bip_ver_ort['5.2']
            
            if v52_bip < v51_bip:
                iyilesme = ((v51_bip - v52_bip) / v51_bip) * 100
                bip_notu = f"🔄 **BiP Versiyon Gelişimi:** BiP uygulaması **V5.2** sürümünde, V5.1 sürümüne göre ortalama {metrik_adi} süresini **%{iyilesme:.1f} oranında düşürerek (hızlandırarak)** performans artışı yakalamıştır."
            else:
                yavaslama = ((v52_bip - v51_bip) / v51_bip) * 100
                bip_notu = f"🔄 **BiP Versiyon Gelişimi:** BiP uygulaması **V5.2** sürümünde, V5.1 sürümüne göre ortalama {metrik_adi} süresinde **%{yavaslama:.1f} oranında bir artış (yavaşlama)** kaydetmiştir."
            yorumlar.append(bip_notu)

    return "\n\n".join(yorumlar)

# --- VERİ YÜKLEME (DİNAMİK TARAMA OLSUN) ---
# Sabit isim listesi yerine klasördeki tüm xlsx dosyalarını tarıyoruz, böylece harf hatalarından kaçınırız.
all_files = glob.glob("*.xlsx")
all_data = []

for f in all_files:
    res = veri_isle(f)
    if res is not None:
        all_data.append(res)

if all_data:
    full_df = pd.concat(all_data, ignore_index=True)
    
    # --- FİLTRELER (SIDEBAR) ---
    st.sidebar.header("⚙️ Analiz Ayarları")
    
    uzanti_listesi = sorted(full_df['Uzantı'].unique())
    secilen_uzanti = st.sidebar.selectbox("Dosya Formatı Seçin:", uzanti_listesi)
    
    versiyon_listesi = sorted(full_df['Versiyon'].unique())
    secilen_versiyonlar = st.sidebar.multiselect(
        "Versiyonları Kıyasla:", 
        versiyon_listesi, 
        default=versiyon_listesi
    )
    
    # Filtreleme uygula
    mask = (full_df['Uzantı'] == secilen_uzanti) & (full_df['Versiyon'].isin(secilen_versiyonlar))
    plot_df = full_df[mask]

    if not plot_df.empty:
        # Renk paleti
        color_map = {
            'BiP (V5.1)': '#3498db',       
            'BiP (V5.2)': '#2980b9',       
            'WhatsApp (V5.1)': '#2ecc71',  
            'WhatsApp (V5.2)': '#27ae60'   
        }

        # --- GRAFİKLER ---
        # 1. YÜKLEME
        st.subheader(f"📤 {secilen_uzanti} - Yükleme Performansı Analizi")
        fig_up = px.bar(
            plot_df, x='Boyut', y='Yükleme Süresi', color='Grup',
            facet_col='Şebeke', barmode='group', text_auto=True,
            category_orders={"Şebeke": ["3G", "4G", "Wi-Fi"]},
            color_discrete_map=color_map,
            labels={'Yükleme Süresi': 'Süre (ms)', 'Grup': 'Uygulama & Versiyon'}
        )
        st.plotly_chart(fig_up, use_container_width=True)
        st.info(dinamik_yorum_yap(plot_df, 'Yükleme Süresi', 'yükleme'))

        st.divider()

        # 2. İNDİRME
        st.subheader(f"📥 {secilen_uzanti} - İndirme Performansı Analizi")
        fig_down = px.bar(
            plot_df, x='Boyut', y='İndirme Süresi', color='Grup',
            facet_col='Şebeke', barmode='group', text_auto=True,
            category_orders={"Şebeke": ["3G", "4G", "Wi-Fi"]},
            color_discrete_map=color_map,
            labels={'İndirme Süresi': 'Süre (ms)', 'Grup': 'Uygulama & Versiyon'}
        )
        st.plotly_chart(fig_down, use_container_width=True)
        st.success(dinamik_yorum_yap(plot_df, 'İndirme Süresi', 'indirme'))

        # Tablo Görünümü
        with st.expander("📊 Ham Veri Tablosu"):
            st.dataframe(plot_df.sort_values(['Şebeke', 'Boyut', 'Versiyon']), use_container_width=True)
    else:
        st.warning("Seçilen filtrelere uygun veri bulunamadı.")
else:
    st.error("❌ Klasörde hiç .xlsx dosyası bulunamadı!")
