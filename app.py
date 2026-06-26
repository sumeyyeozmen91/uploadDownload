import pandas as pd
import numpy as np

# 1. Dosya Yolları ve İsimlerinin Tanımlanması (Yeni Dosya Yapısına Göre)
files = {
    'BiP_4.5G': 'Bip_4.5G_new.xlsx - Test Verileri.csv',
    'BiP_WiFi': 'Bip_Wifi_new.xlsx - Test Verileri.csv',
    'WhatsApp_4.5G': 'Wa_4.5G.xlsx - Sıralı Test Verileri.csv',
    'WhatsApp_WiFi': 'Wa_Wifi.xlsx - Veri Listesi.csv'
}

def clean_and_load(file_path, app_name, network_type):
    try:
        df = pd.read_csv(file_path)
        
        # Sütun isimlerindeki boşlukları temizleme
        df.columns = [c.strip() for c in df.columns]
        
        # İlgili sütunları seçme ve isimlendirme
        # Not: Sütun isimleri dosyalara göre farklılık gösterebilir (örn: 'Yükleme Süresi' veya 'Yükleme Süresi (ms)')
        upload_col = [c for c in df.columns if 'Yükleme Süresi' in c][0]
        download_col = [c for c in df.columns if 'İndirme Süresi' in c][0]
        
        df = df.rename(columns={
            'Test Adı': 'Test_Adi',
            upload_col: 'Upload_ms',
            download_col: 'Download_ms'
        })
        
        # Sayısal değerleri temizleme ve dönüştürme
        df['Upload_ms'] = pd.to_numeric(df['Upload_ms'], errors='coerce')
        df['Download_ms'] = pd.to_numeric(df['Download_ms'], errors='coerce')
        
        # Uygulama ve Şebeke etiketlerini ekleme
        df['Uygulama'] = app_name
        df['Sebeke'] = network_type
        
        return df[['Test_Adi', 'Upload_ms', 'Download_ms', 'Uygulama', 'Sebeke']]
    except Exception as e:
        print(f"Hata ({file_path}): {e}")
        return pd.DataFrame()

# 2. Tüm Verilerin Yüklenmesi ve Birleştirilmesi
all_data = []
for key, file_name in files.items():
    app, network = key.split('_')
    # Şebeke ismini daha okunabilir yapalım
    network_label = '4.5G' if network == '4.5G' else 'Wi-Fi'
    df_cleaned = clean_and_load(file_name, app, network_label)
    if not df_cleaned.empty:
        all_data.append(df_cleaned)

combined_df = pd.concat(all_data, ignore_index=True)

# 3. 4.5G ve Wi-Fi Karşılaştırmalı Performans Analizi (Özet Tablo)
print("=== 4.5G ve Wi-Fi Genel Performans Karşılaştırması (Ortalama ms) ===")
summary = combined_df.groupby(['Uygulama', 'Sebeke'])[['Download_ms', 'Upload_ms']].mean().round(2)
print(summary)
print("\n")

# 4. Dosya Boyutlarına Göre Detaylı Karşılaştırma (Opsiyonel)
# Test adından dosya boyutunu (örn: 10MB, 40MB) çıkarma
combined_df['Dosya_Boyutu'] = combined_df['Test_Adi'].str.extract(r'(\d+MB)')

print("=== Dosya Boyutlarına Göre Detaylı Karşılaştırma (Ortalama ms) ===")
detailed_summary = combined_df.groupby(['Dosya_Boyutu', 'Uygulama', 'Sebeke'])[['Download_ms', 'Upload_ms']].mean().round(2)
print(detailed_summary)
