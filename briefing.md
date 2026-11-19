bu klasörde json dosyaları, png dosyaları, bir adet xlsx dosyası mevcut.

json dosyalarında bip uygulamasına ait bütün upload-download süreleri mevcut. o json dosyalarından Duration değerini ve EĞER CompressDuration değeri SIFIRDAN FARKLIYSA Duration'a EKLEYEREK her bir json dosyası için ayrı ayrı (Upload ve Download'lar da ayrı ayrı olacak şekilde) Dosya İsmi, İndirme/Yükleme Süresi ve Dosya Boyutu olacak şekilde üç sütunlu tablolar oluşturmanı istiyorum.

Bunların isim formatı da şunlar gibi olmalı:

SD_Photo_Upload_Lte
SD_2DkVideo_Upload_Wifi

gibi türe göre uydur ama format buna benzemek zorunda.

png dosyalarına gelince onlar da whatsapp a ait veriler.
her bir png deki sağdaki 2 sayıdan soldaki Upload_Duration ve Download_Duration'ı sırayla temsil etmekteler.
Bu PNG dosyalarındaki Upload ve Download sütunları ayırarak sana vereceğim boyut bilgileriyle tabloları aynı şekil oluştur:

Photo ve Video lar hariç geri kalan dosyaların boyutu tamamen biptekilerle AYNIDIR.


Bunların isim formatı da şunlar gibi :

SD_Photo_Wa_Upload_Lte
SD_2DkVideo_Wa_Upload_Wifi

gibi türe de uydur ama format buna benzemek zorunda.

XLSX dosyası ise her bir test setini çalıştırmadan önce yapılan speedtest sonuçlarını içeriyor.
yalnız upload hızı olarak MDX cihazı, download hızı olarak HXC cihazını baz alman gerek, MDX nin downloadı ve HXC nin uploadını göz ardı etmeliyiz dashboarda yansıtırken.
onların da dashboardumuzda görünmesini istiyorum.

bunları da uygun bir yere yerleştirmek gerekiyor.
bu briefing i iyi anla ve tek seferde güzel bir sonuç çıkar bana.



