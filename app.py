import pandas as pd
import glob
import re

# 1. Dosya Listesi ve Tanımlamalar
# Yeni dosya formatları: "Bip_3G_new.xlsx - Sıralı Veriler.csv", "Bip_4.5G_new.xlsx - Test Verileri.csv", vb.
file_pattern = "*.csv"
all_files = glob.glob(file_pattern)

data_list = []

for file_name in all_files:
    # Dosya isminden Uygulama ve Şebeke türünü çıkarma
    # Örn: "Bip_3G_new.xlsx - Sıralı Veriler.csv" -> App: Bip, Net: 3G
    match = re.search(r'(BiP|Wa)_(3G|4\.5G|Wifi)', file_name, re.IGNORECASE)
    
    if match:
        app_raw = match.group(1).lower()
        net_raw = match.group(2).lower()
        
        # Standart isimlendirme
        app = "BiP" if app_raw == "bip" else "WhatsApp"
        
        if net_raw == "3g":
            network = "3G"
        elif net_raw == "4.5g":
            network = "4.5G"
        else:
            network = "Wi-Fi"
            
        # CSV Dosyasını Okuma
        try:
            df = pd.read_csv(file_name)
            
            # Sütun isimlerindeki boşlukları temizleme
            df.columns = df.columns.str.strip()
            
            # Şebeke ve Uygulama bilgilerini yeni sütun olarak ekleme
            df['Application'] = app
            df['Network'] = network
            
            # Dosya adını referans için tutma
            df['Source_File'] = file_name
            
            data_list.append(df)
            print(f"Başarıyla yüklendi: {file_name} ({app} - {network})")
        except Exception as e:
            print(f"Hata oluştu ({file_name}): {e}")

# tüm verileri tek bir DataFrame'de birleştirme
if data_list:
    final_df = pd.concat(data_list, ignore_index=True)
    print(f"\nToplam {len(final_df)} satır veri birleştirildi.")
else:
    print("Eşleşen veya okunabilen dosya bulunamadı.")
