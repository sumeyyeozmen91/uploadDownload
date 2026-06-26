import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# Sayfa ayarları
st.set_page_config(page_title="Hız Testi Analiz Merkezi", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP Versiyon Performans Analizi (Fotoğraf Modları)")
st.markdown("""
    Bu panelde, yeni test formatına göre fotoğraf yükleme ve indirme performansları analiz edilir.
    - **Sürümler:** V5.1.23 vs V5.2.6
    - **Şebekeler:** 4.5G ve Wi-Fi
    - **Fotoğraf Modları:** HDPhoto ve SDPhoto
""")

def veri_isle(file_path):
    try:
        if not os.path.exists(file_path):
            return None
            
        df = pd.read_excel(file_path)
        
        # Sütun isimlerini temizle
        df.columns = [str(c).split(' (')[0].strip() for c in df.columns]
        
        fname = os.path.basename(file_path).lower()
        
        # --- YENİ DOSYA ADI FORMATI AYRIŞTIRMA ---
        # Örn: 5.1.23_bip_4.5g_hdphoto.xlsx veya .csv
        if "_" in fname and ('5.1.23' in fname or '5.2.6' in fname):
            parts = fname.split('_')
            version = parts[0]              # "5.1.23" veya "5.2.6"
            app_name = "BiP"
            net_raw = parts[2]              # "4.5g" veya "wifi"
            mode_raw = parts[3].replace(".xlsx", "").replace(".csv", "").upper() # "HDPHOTO" veya "SDPHOTO"
        else:
            return None # Tanımlanamayan formatları es geç
        
        # Şebeke ismini standartlaştır (Sadece 4.5G ve Wi-Fi)
        if "4.5g" in net_raw or "4g" in net_raw: 
            network = "4.5G"
        elif "wifi" in net_raw: 
            network = "Wi-Fi"
        else:
            return None # 3G vb. varsa dahil etme
        
        # DataFrame sütunlarını doldur
        df['Uygulama'] = app_name
        df['Versiyon'] = version
        df['Şebeke'] = network
        df['Foto Modu'] = "HD Fotoğraf" if "HDPHOTO" in mode_raw else "SD Fotoğraf"
        df['Grup'] = f"BiP (V{version})"
        
        # Dosya uzantısı ve boyutu çıkarma (Test Adı sütunundan)
        df['Uzantı'] = df['Test Adı'].apply(lambda x: str(x).split('.')[-1].upper() if '.' in str(x) else 'DİĞER')
        df['Boyut'] = df['Test Adı'].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x))
        
        return df[['Test Adı', 'Uzantı', 'Boyut', 'Yükleme Süresi', 'İndirme Süresi', 'Uygulama', 'Versiyon', 'Şebeke', 'Foto Modu', 'Grup']]
    except Exception as e:
        st.error(f"⚠️ {file_path} işlenirken hata oluştu: {e}")
        return None

# --- SÜRÜM GELİŞİM YORUM MOTORU ---
def surum_gelisim_yorumu(df, metrik_kolonu, metrik_adi):
    if df.empty:
        return "Yorumlanacak veri bulunamadı."
    
    yorumlar = []
    bip51_df = df[df['Versiyon'] == '5.1.23']
    bip52_df = df[df['Versiyon'] == '5.2.6']
    
    yorumlar.append("### 🔄 Sürümler Arası Geçiş ve Optimizasyon Analizi (V5.1.23 ➡️ V5.2.6)")
    
    if not bip51_df.empty and not bip52_df.empty:
        sebekeler = sorted(list(set(bip51_df['Şebeke']).intersection(set(bip52_df['Şebeke']))))
        modlar = sorted(list(set(bip51_df['Foto Modu']).intersection(set(bip52_df['Foto Modu']))))
        
        for seb in sebekeler:
            for mod in modlar:
                v51_ort = bip51_df[(bip51_df['Şebeke'] == seb) & (bip51_df['Foto Modu'] == mod)][metrik_kolonu].mean()
                v52_ort = bip52_df[(bip52_df['Şebeke'] == seb) & (bip52_df['Foto Modu'] == mod)][metrik_kolonu].mean()
                
                if pd.notna(v51_ort) and pd.notna(v52_ort):
                    if v52_ort < v51_ort:
                        iyilesme = ((v51_ort - v52_ort) / v51_ort) * 100
                        yorumlar.append(f"- **{seb} - {mod} Modunda:** Yeni **V5.2.6 sürümü**, eski sürüme göre {metrik_adi} süresini **%{iyilesme:.1f} azaltarak (hızlandırarak)** performans artışı kaydetmiştir. ✅")
                    else:
                        yavaslama = ((v52_ort - v51_ort) / v51_ort) * 100
                        yorumlar.append(f"- **{seb} - {mod} Modunda:** Yeni **V5.2.6 sürümünde**, V5.1.23'e kıyasla %{yavaslama:.1f} oranında bir **yavaşlama (süre artışı)** görülmüştür. ⚠️")
    else:
        yorumlar.append("- Klasörde kıyaslama yapmak için BiP V5.1.23 veya V5.2.6 dosyalarından biri eksik.")

    return "\n".join(yorumlar)

# --- VERİ TARAMA VE YÜKLEME ---
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
    
    # Fotoğraf Modu Filtresi (HD / SD)
    mevcut_modlar = sorted(full_df['Foto Modu'].unique())
    secilen_mod = st.sidebar.radio("Fotoğraf Kalitesi Seçin:", mevcut_modlar)
    
    # Sürüm Grupları Filtresi
    mevcut_gruplar = sorted(full_df['Grup'].unique())
    secilen_gruplar = st.sidebar.multiselect("Grafikte Gösterilecek Sürümler:", mevcut_gruplar, default=mevcut_gruplar)
    
    # Şebeke Filtresi
    mevcut_sebekeler = sorted(full_df['Şebeke'].unique())
    secilen_sebekeler = st.sidebar.multiselect("Şebeke Seçimi:", mevcut_sebekeler, default=mevcut_sebekeler)
    
    # Veriyi filtrele
    plot_df = full_df[
        (full_df['Uzantı'] == secilen_uzanti) & 
        (full_df['Foto Modu'] == secilen_mod) & 
        (full_df['Grup'].isin(secilen_gruplar)) &
        (full_df['Şebeke'].isin(secilen_sebekeler))
    ]

    if not plot_df.empty:
        # Renk Düzeni (Versiyon tonlaması)
        color_map = {
            'BiP (VV5.1.23)': '#3498db',     # Açık Mavi
            'BiP (VV5.2.6)': '#1f3a60'       # Koyu Lacivert
        }

        # --- GRAFİKLER VE DETAYLI YORUMLAR ---
        
        # 1. YÜKLEME (UPLOAD)
        st.subheader(f"📤 {secilen_uzanti} - {secilen_mod} Yükleme Performansı Kıyaslaması")
        fig_up = px.bar(
            plot_df, x='Boyut', y='Yükleme Süresi', color='Grup',
            facet_col='Şebeke', barmode='group', text_auto=True,
            category_orders={"Şebeke": ["4.5G", "Wi-Fi"], "Grup": ["BiP (V5.1.23)", "BiP (V5.2.6)"]},
            color_discrete_map=color_map,
            labels={'Yükleme Süresi': 'Süre (ms)', 'Grup': 'Sürüm'}
        )
        st.plotly_chart(fig_up, use_container_width=True)
        
        # Yükleme Yorum Alanı
        st.info(surum_gelisim_yorumu(plot_df, 'Yükleme Süresi', 'yükleme'))

        st.divider()

        # 2. İNDİRME (DOWNLOAD)
        st.subheader(f"📥 {secilen_uzanti} - {secilen_mod} İndirme Performansı Kıyaslaması")
        fig_down = px.bar(
            plot_df, x='Boyut', y='İndirme Süresi', color='Grup',
            facet_col='Şebeke', barmode='group', text_auto=True,
            category_orders={"Şebeke": ["4.5G", "Wi-Fi"], "Grup": ["BiP (V5.1.23)", "BiP (V5.2.6)"]},
            color_discrete_map=color_map,
            labels={'İndirme Süresi': 'Süre (ms)', 'Grup': 'Sürüm'}
        )
        st.plotly_chart(fig_down, use_container_width=True)
        
        # İndirme Yorum Alanı
        st.success(surum_gelisim_yorumu(plot_df, 'İndirme Süresi', 'indirme'))

        # Ham Veri Tablosu
        with st.expander("📊 Filtrelenmiş Detaylı Veri Tablosu"):
            st.dataframe(plot_df.sort_values(['Şebeke', 'Boyut', 'Grup']), use_container_width=True)
    else:
        st.warning("Seçilen kriterlere uygun veri bulunamadı.")
else:
    st.error("❌ Klasörde yeni formata uygun .xlsx dosyası bulunamadı!")
    st.info("""
    **Beklenen örnek dosya isimleri:**
    - `5.1.23_Bip_4.5G_HDPhoto.xlsx`
    - `5.1.23_Bip_Wifi_SDPhoto.xlsx`
    - `5.2.6_Bip_4.5G_HDPhoto.xlsx`
    - `5.2.6_Bip_Wifi_SDPhoto.xlsx`
    """)
