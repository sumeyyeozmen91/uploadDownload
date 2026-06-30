# --- GELİŞMİŞ VE DETAYLANDIRILMIŞ 3'LÜ KARŞILAŞTIRMA MOTORU (GÜNCELLENDİ) ---
def surum_gelisim_yorumu(df, metrik_kolonu):
    try:
        if df.empty:
            return "Yorumlanacak veri bulunamadı."

        yorumlar = []
        stats = df.groupby(['Şebeke', 'Grup'])[metrik_kolonu].mean().unstack(level=-1)
        
        yorumlar.append("### 📊 3'lü Performans Karşılaştırma Analiz Raporu (Download_Duration)")
        
        for seb in sorted(df['Şebeke'].unique()):
            if seb in stats.index:
                yorumlar.append(f"\n**📍 {seb} Şebekesi Detaylı Analiz Çıktıları:**")
                row = stats.loc[seb]
                
                bip51 = row.get('BiP (V5.1.23)', None)
                bip52 = row.get('BiP (V5.2.6)', None)
                wa = row.get('WhatsApp', None)
                
                # 1. BiP Kendi İçi Sürüm Gelişimi
                if pd.notna(bip51) and pd.notna(bip52):
                    if bip52 < bip51:
                        degisim = ((bip51 - bip52) / bip51) * 100
                        yorumlar.append(f"- **BiP İçi Evrim:** Yeni V5.2.6 sürümü, eski V5.1.23 sürümüne göre indirme süresini **{int(bip51 - bip52)} ms kısaltmış** ve **%{degisim:.1f} daha hızlı** bir performansa ulaşmıştır. ✅")
                    else:
                        degisim = ((bip52 - bip51) / bip51) * 100
                        yorumlar.append(f"- **BiP İçi Evrim:** Yeni V5.2.6 sürümünde eski sürüme kıyasla indirme süresi **{int(bip52 - bip51)} ms uzamış (%{degisim:.1f} yavaşlama)** saptanmıştır. ⚠️")
                
                # 2. Detaylandırılmış 3'lü Sıralama ve Performans Makası
                mevcut_ortalamalar = [(k, v) for k, v in row.items() if pd.notna(v)]
                if mevcut_ortalamalar:
                    mevcut_ortalamalar.sort(key=lambda x: x[1])  # En kısa süreden (en hızlıdan) en uzuna sıralar
                    
                    lider_grup, lider_sure = mevcut_ortalamalar[0]
                    yorumlar.append(f"- **Kulvar Lideri:** Bu şebekede en az sürede indiren (en hızlı) platform **{int(lider_sure)} ms** ortalamayla **{lider_grup}** olmuştur. 🚀")
                    
                    # Karmaşayı Önleyen Yeni Podyum Metni
                    podyum_elemanlari = []
                    for sira, (grup_adi, sure_degeri) in enumerate(mevcut_ortalamalar, start=1):
                        if sira == 1:
                            podyum_elemanlari.append(f"🥇 **{grup_adi}** ({int(sure_degeri)} ms - En Hızlı)")
                        elif sira == 2:
                            podyum_elemanlari.append(f"🥈 **{grup_adi}** ({int(sure_degeri)} ms - Orta)")
                        else:
                            podyum_elemanlari.append(f"🥉 **{grup_adi}** ({int(sure_degeri)} ms - En Yavaş)")
                    
                    yorumlar.append(f"- **Performans Sıralaması (En Kısa Sürede İndirenden En Uzuna):** " + "  >  ".join(podyum_elemanlari))
                    
                    if len(mevcut_ortalamalar) >= 2:
                        en_yavas_grup, en_yavas_sure = mevcut_ortalamalar[-1]
                        makas_yuzde = ((en_yavas_sure - lider_sure) / en_yavas_sure) * 100
                        yorumlar.append(f"- **Performans Makası:** Lider platform ({lider_grup}), en yavaş kalan platforma ({en_yavas_grup}) kıyasla süreyi **%{makas_yuzde:.1f} oranında azaltarak** daha efektif bir indirme sağlamıştır.")
                        
        return "\n".join(yorumlar)
    except:
        return "Yorum motorunda teknik bir hata oluştu."
