import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob

# Sayfa ayarları
st.set_page_config(page_title="BiP & WhatsApp Performans Karşılaştırma Merkezi", layout="wide")

# --- BAŞLIK VE AÇIKLAMA ---
st.title("🚀 BiP (V5.1.23 & V5.2.6) vs WhatsApp İndirme Performansı Karşılaştırması")
st.markdown("""
    Bu panelde BiP ve WhatsApp uygulamalarının **Download_Duration (İndirme Süresi)** performansları 3'lü olarak analiz edilir:
    * **BiP (V5.1.23) vs BiP (V5.2.6):** Sürüm gelişim ve optimizasyon başarısı.
    * **BiP Sürümleri vs WhatsApp:** Rakip analizi ve şebeke bazlı en hızlı uygulama tespiti.
""")

def veri_isle(file_path):
    try:
        if not os.path.exists(file_path):
            return None

        # Excel dosyasını oku
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
        except:
            df = pd.read_excel(file_path)

        if df.empty:
            return None

        # Sütun isimlerinin başındaki ve sonundaki boşlukları temizle
        df.columns = [str(c).strip() for c in df.columns]

        # İlk sütunu 'Test Adı' olarak sabitle
        df.rename(columns={df.columns[0]: 'Test Adı'}, inplace=True)

        # --- DOWNLOAD_DURATION ODAKLI KONTROL ---
        duration_col = None
        for col in df.columns:
            if col.lower() == 'download_duration':
                duration_col = col
                break
        
        if duration_col is not None:
            df.rename(columns={duration_col: 'Download_Duration'}, inplace=True)
        else:
            for col in df.columns:
                if 'duration' in col.lower():
                    df.rename(columns={col: 'Download_Duration'}, inplace=True)
                    duration_col = col
                    break
        
        if 'Download_Duration' not in df.columns:
            return None

        # --- GÜVENLİ SAYISAL DÖNÜŞTÜRME ---
        df['Download_Duration'] = df['Download_Duration'].apply(lambda x: ''.join(c for c in str(x) if c.isdigit() or c in ['.', ',']))
        df['Download_Duration'] = df['Download_Duration'].str.replace(',', '.')
        df['Download_Duration'] = pd.to_numeric(df['Download_Duration'], errors='coerce').astype(float)

        # Boş veya hatalı satırları temizle
        df = df.dropna(subset=['Download_Duration'])

        fname = os.path.basename(file_path)
        fname_lower = fname.lower()

        # --- DOSYA ADI FORMATI AYRIŞTIRMA ---
        if "_" in fname:
            clean_name = fname.replace(".xlsx", "").replace(".csv", "")
            parts = clean_name.split('_')
            parts_lower = [p.lower() for p in parts]
            
            if parts_lower[0] == "wa":
                app_name = "WhatsApp"
                version = "Genel"
                net_raw = parts_lower[1]
                type_raw = parts_lower[2]
            elif "bip" in parts_lower:
                version = parts[0]
                app_name = "BiP"
                net_raw = parts_lower[2]
                type_raw = parts_lower[3]
            else:
                return None
                
            if "hd" in type_raw:
                medya_kalitesi = "HD"
                medya_turu = type_raw.replace("hd", "").capitalize()
            elif "sd" in type_raw:
                medya_kalitesi = "SD"
                medya_turu = type_raw.replace("sd", "").capitalize()
            else:
                medya_kalitesi = "Genel"
                medya_turu = type_raw.capitalize()
        else:
            return None

        if "3g" in net_raw: network = "3G"
        elif "4g" in net_raw or "4.5g" in net_raw: network = "4.5G"
        elif "wifi" in net_raw: network = "Wi-Fi"
        else: network = net_raw.upper()

        df['Uygulama'] = app_name
        df['Versiyon'] = version
        df['Şebeke'] = network
        df['Grup'] = f"BiP (V{version})" if app_name == "BiP" else app_name
        df['Medya Kalitesi'] = medya_kalitesi
        df['Medya Türü'] = medya_turu

        return df[['Test Adı', 'Download_Duration', 'Uygulama', 'Versiyon', 'Şebeke', 'Grup', 'Medya Kalitesi', 'Medya Türü']]
    except Exception as e:
        return None

# --- GELİŞMİŞ 3'LÜ KARŞILAŞTIRMA MOTORU ---
def surum_gelisim_yorumu(df, metrik_kolonu):
    try:
        if df.empty:
            return "Yorumlanacak veri bulunamadı."

        yorumlar = []
        stats = df.groupby(['Şebeke', 'Grup'])[metrik_kolonu].mean().unstack(level=-1)
        
        yorumlar.append("### 📊 3'lü Performans Karşılaştırma Analiz Raporu (Download_Duration)")
        
        for seb in sorted(df['Şebeke'].unique()):
            if seb in stats.index:
                yorumlar.append(f"\n**📍 {seb} Şebekesi Altındaki Durum:**")
                row = stats.loc[seb]
                
                bip51 = row.get('BiP (V5.1.23)', None)
                bip52 = row.get('BiP (V5.2.6)', None)
                wa = row.get('WhatsApp', None)
                
                if pd.notna(bip51) and pd.notna(bip52):
                    if bip52 < bip51:
                        degisim = ((bip51 - bip52) / bip51) * 100
                        yorumlar.append(f"- **BiP Gelişimi:** Yeni V5.2.6 sürümü, eski V5.1.23 sürümüne göre **%{degisim:.1f} daha hızlı indiriyor.** ✅")
                    else:
                        degisim = ((bip52 - bip51) / bip51) * 100
                        yorumlar.append(f"- **BiP Gelişimi:** Yeni V5.2.6 sürümünde eski sürüme göre **%{degisim:.1f} oranında bir yavaşlama (süre artışı)** saptanmıştır. ⚠️")
                
                mevcut_ortalamalar = [(k, v) for k, v in row.items() if pd.notna(v)]
                if mevcut_ortalamalar:
                    mevcut_ortalamalar.sort(key=lambda x: x[1])
                    lider_grup, lider_sure = mevcut_ortalamalar[0]
                    yorumlar.append(f"- **3'lü Rekabet:** En kısa indirme süresi **{int(lider_sure)} ms** ile **{lider_grup}** tarafından elde edilmiştir. 🚀")
                    
                    podyum = " > ".join([f"**{g}** ({int(s)} ms)" for g, s in mevcut_ortalamalar])
                    yorumlar.append(f"- **Hız Sıralaması (Hızlıdan Yavaşa):** {podyum}")
                    
        return "\n".join(yorumlar)
    except:
        return "Yorum motorunda teknik bir hata oluştu."

# --- VERİ TARAMA VE YÜKLEME ---
all_files = glob.glob("*.xlsx") + glob.glob("*.XLSX")
all_files = list(set(all_files))

all_data = []
for f in all_files:
    res = veri_isle(f)
    if res is not None:
        all_data.append(res)

if all_data:
    full_df = pd.concat(all_data, ignore_index=True)

    # --- FİLTRELER (SIDEBAR) ---
    st.sidebar.header("⚙️ Analiz Ayarları")

    kalite_listesi = sorted(full_df['Medya Kalitesi'].unique())
    secilen_kalite = st.sidebar.selectbox("Medya Kalitesi Seçin:", kalite_listesi)

    tur_listesi = sorted(full_df['Medya Türü'].unique())
    secilen_tur = st.sidebar.selectbox("Medya Türü Seçin:", tur_listesi)

    hedef_sira = ['BiP (V5.1.23)', 'BiP (V5.2.6)', 'WhatsApp']
    mevcut_gruplar = sorted(full_df['Grup'].unique())
    varsayilan_gruplar = [g for g in hedef_sira if g in mevcut_gruplar]

    secilen_gruplar = st.sidebar.multiselect(
        "Grafikte Gösterilecek Versiyonlar/Uygulamalar:", 
        mevcut_gruplar, 
        default=varsayilan_gruplar
    )

    plot_df = full_df[
        (full_df['Medya Kalitesi'] == secilen_kalite) & 
        (full_df['Medya Türü'] == secilen_tur) & 
        (full_df['Grup'].isin(secilen_gruplar))
    ].copy()

    if not plot_df.empty:
        plot_df = plot_df.sort_values(by=['Şebeke', 'Grup'])
        plot_df['Koşum Sayısı'] = plot_df.groupby(['Şebeke', 'Grup']).cumcount() + 1
        plot_df['Koşum Sayısı'] = plot_df['Koşum Sayısı'].astype(str) + ". Koşum"

        color_map = {
            'BiP (V5.1.23)': '#3498db',
            'BiP (V5.2.6)': '#1f3a60',
            'WhatsApp': '#2ecc71'
        }

        st.subheader(f"📥 {secilen_kalite} {secilen_tur} Dosyaları - 3'lü İndirme Süresi Kıyaslaması")
        
        unique_kosumlar = plot_df['Koşum Sayısı'].unique()
        kosum_sirasi = sorted(list(unique_kosumlar), key=lambda x: int(x.split('.')[0]) if '.' in str(x) else 0)

        fig_down = px.bar(
            plot_df, x='Koşum Sayısı', y='Download_Duration', color='Grup',
            facet_col='Şebeke', barmode='group', text_auto=True,
            category_orders={
                "Şebeke": ["4.5G", "Wi-Fi"], 
                "Grup": [g for g in hedef_sira if g in secilen_gruplar],
                "Koşum Sayısı": kosum_sirasi
            },
            color_discrete_map=color_map,
            labels={'Download_Duration': 'Süre (ms)', 'Grup': 'Uygulama / Sürüm', 'Koşum Sayısı': 'Koşum Numarası'}
        )
        
        fig_down.update_xaxes(type='category')
        st.plotly_chart(fig_down, use_container_width=True)
        st.success(surum_gelisim_yorumu(plot_df, 'Download_Duration'))

        with st.expander("📊 Filtrelenmiş Veri Tablosu"):
            st.dataframe(plot_df.sort_values(['Şebeke', 'Grup']), use_container_width=True)
    else:
        st.warning("⚠️ Seçilen filtrelere (Medya Kalitesi / Türü) uygun veri bulunamadı. Lütfen sol menüdeki filtreleri değiştirin.")
else:
    st.error("❌ Klasördeki .xlsx dosyalarının hiçbirinde 'Download_Duration' sütunu bulunamadı veya isim formatı eşleşmedi!")
