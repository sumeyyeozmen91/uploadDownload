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
    Bu panelde BiP ve WhatsApp uygulamalarının indirme performansları 3'lü olarak analiz edilir:
    * **BiP (V5.1.23) vs BiP (V5.2.6):** Sürüm optimizasyon başarısı.
    * **BiP Sürümleri vs WhatsApp:** Rakip analizi ve şebeke bazlı en hızlı uygulama tespiti.
""")

def veri_isle(file_path):
    try:
        if not os.path.exists(file_path):
            return None

        # Excel okuma motorunu açıkça belirliyoruz
        df = pd.read_excel(file_path, engine='openpyxl')

        if df.empty:
            return None

        # İlk sütunu test adı olarak işaretle ve temizle
        df.rename(columns={df.columns[0]: 'Test Adı'}, inplace=True)
        df.columns = [str(c).strip() for c in df.columns]

        # --- AKILLI SÜTUN BULUCU (Hata Almayı Önleyen Kritik Kısım) ---
        target_col = None
        for col in df.columns:
            col_lower = col.lower()
            # Sütun adında indirme, download, duration, süre veya time geçen ilk sütunu hedef al
            if any(k in col_lower for k in ['duration', 'süre', 'sure', 'download', 'time', 'indirme']):
                target_col = col
                break
        
        if target_col is not None:
            df.rename(columns={target_col: 'İndirme Süresi'}, inplace=True)
        else:
            # Eğer eşleşen bulunamazsa, 2. sütunu indirme süresi kabul et (Vailsafe)
            if len(df.columns) >= 2:
                df.rename(columns={df.columns[1]: 'İndirme Süresi'}, inplace=True)
            else:
                return None

        # --- GÜVENLİ SAYISAL DÖNÜŞTÜRME ---
        df['İndirme Süresi'] = df['İndirme Süresi'].apply(lambda x: ''.join(c for c in str(x) if c.isdigit() or c in ['.', ',']))
        df['İndirme Süresi'] = df['İndirme Süresi'].str.replace(',', '.')
        df['İndirme Süresi'] = pd.to_numeric(df['İndirme Süresi'], errors='coerce').astype(float)

        # Boş satırları temizle
        df = df.dropna(subset=['İndirme Süresi'])

        fname = os.path.basename(file_path).lower()

        # --- DOSYA ADI FORMATI AYRIŞTIRMA (Büyük/Küçük Harf Korumalı) ---
        if "_" in fname:
            clean_name = fname.replace(".xlsx", "").replace(".csv", "")
            parts = clean_name.split('_')
            
            # WhatsApp formatı kontrolü (wa_... veya wa_...)
            if parts[0] == "wa":
                app_name = "WhatsApp"
                version = "Genel"
                net_raw = parts[1]
                type_raw = parts[2]
            # BiP formatı kontrolü (5.1.23_bip_...)
            elif "bip" in parts:
                version = parts[0]   # "5.1.23" veya "5.2.6"
                app_name = "BiP"
                net_raw = parts[2]   # "4.5g" veya "wifi"
                type_raw = parts[3] 
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

        # Şebeke ismini standartlaştır
        if "3g" in net_raw: network = "3G"
        elif "4g" in net_raw or "4.5g" in net_raw: network = "4.5G"
        elif "wifi" in net_raw: network = "Wi-Fi"
        else: network = net_raw.upper()

        # DataFrame sütunlarını doldur
        df['Uygulama'] = app_name
        df['Versiyon'] = version
        df['Şebeke'] = network
        df['Grup'] = f"BiP (V{version})" if app_name == "BiP" else app_name
        df['Medya Kalitesi'] = medya_kalitesi
        df['Medya Türü'] = medya_turu

        return df[['Test Adı', 'İndirme Süresi', 'Uygulama', 'Versiyon', 'Şebeke', 'Grup', 'Medya Kalitesi', 'Medya Türü']]
    except Exception as e:
        return None

# --- GELİŞMİŞ 3'LÜ KARŞILAŞTIRMA MOTORU ---
def surum_gelisim_yorumu(df, metrik_kolonu):
    if df.empty:
        return "Yorumlanacak veri bulunamadı."

    yorumlar = []
    stats = df.groupby(['Şebeke', 'Grup'])[metrik_kolonu].mean().unstack(level=-1)
    
    yorumlar.append("### 📊 3'lü Performans Karşılaştırma Analiz Raporu")
    
    for seb in sorted(df['Şebeke'].unique()):
        if seb in stats.index:
            yorumlar.append(f"\n**📍 {seb} Şebekesi Altındaki Durum:**")
            row = stats.loc[seb]
            
            bip51 = row.get('BiP (V5.1.23)', None)
            bip52 = row.get('BiP (V5.2.6)', None)
            wa = row.get('WhatsApp', None)
            
            # 1. BiP Sürüm Gelişimi Kıyası
            if pd.notna(bip51) and pd.notna(bip52):
                if bip52 < bip51:
                    degisim = ((bip51 - bip52) / bip51) * 100
                    yorumlar.append(f"- **BiP Gelişimi:** Yeni V5.2.6 sürümü, eski V5.1.23 sürümüne göre **%{degisim:.1f} daha hızlıdır.** ✅")
                else:
                    degisim = ((bip52 - bip51) / bip51) * 100
                    yorumlar.append(f"- **BiP Gelişimi:** Yeni V5.2.6 sürümünde eski sürüme göre **%{degisim:.1f} oranında bir yavaşlama** saptanmıştır. ⚠️")
            
            # 2. WhatsApp ile 3'lü Liderlik Yarışı
            mevcut_ortalamalar = [(k, v) for k, v in row.items() if pd.notna(v)]
            if mevcut_ortalamalar:
                mevcut_ortalamalar.sort(key=lambda x: x[1])
                lider_grup, lider_sure = mevcut_ortalamalar[0]
                yorumlar.append(f"- **3'lü Rekabet:** En efektif indirme süresi **{int(lider_sure)} ms** ile **{lider_grup}** tarafından elde edilmiştir. 🚀")
                
                podyum = " > ".join([f"**{g}** ({int(s)} ms)" for g, s in mevcut_ortalamalar])
                yorumlar.append(f"- **Hız Sıralaması (Hızlıdan Yavaşa):** {podyum}")
                
    return "\n".join(yorumlar)

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

        st.subheader(f"📥 {secilen_kalite} {secilen_tur} Dosyaları - 3'lü İndirme Performansı Kıyaslaması")
        
        unique_kosumlar = plot_df['Koşum Sayısı'].unique()
        kosum_sirasi = sorted(list(unique_kosumlar), key=lambda x: int(x.split('.')[0]) if '.' in str(x) else 0)

        fig_down = px.bar(
            plot_df, x='Koşum Sayısı', y='İndirme Süresi', color='Grup',
            facet_col='Şebeke', barmode='group', text_auto=True,
            category_orders={
                "Şebeke": ["4.5G", "Wi-Fi"], 
                "Grup": [g for g in hedef_sira if g in secilen_gruplar],
                "Koşum Sayısı": kosum_sirasi
            },
            color_discrete_map=color_map,
            labels={'İndirme Süresi': 'Süre (ms)', 'Grup': 'Uygulama / Sürüm', 'Koşum Sayısı': 'Koşum Numarası'}
        )
        
        fig_down.update_xaxes(type='category')
        st.plotly_chart(fig_down, use_container_width=
