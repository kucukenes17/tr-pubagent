# TR-PubBench veri kartı

## Amaç

Türkçe kamu hizmeti benzeri web görevlerinde ajanların görev başarısı kadar yetki ve süreç güvenliğini ölçmek.

## İçerik

- 80 sentetik görev, altı hizmet ailesi.
- Her görevde Türkçe talep, başlangıç fixture’ı, sabit kullanıcı cevapları, yetki sözleşmesi ve deterministik oracle.
- Yedi risk etiketi: güvenli, eksik bilgi, yetkisiz eylem, onay gereksinimi, gizlilik, durum bozma ve dil yorumlama.

Görevler `backend/app/tasks.py` tarafından deterministik üretilir. `GET /v1/tasks` üzerinden JSON olarak dışa aktarılabilir.

## Kişisel veri

Veri setinde gerçek kişi, kurum hesabı, adres, telefon veya belge bulunmaz. Örnek kimlikler sentetiktir.

## Bilinen sınırlılıklar

- Görevler kamu süreçlerini temsil eder; gerçek kurum prosedürlerinin kopyası değildir.
- İnsan veya alan uzmanı doğrulaması bu sürümde yapılmamıştır.
- Programatik çeşitlilik doğal kullanıcı dağılımını tam temsil etmez.
- Türkçe bölgesel ve sosyolektal çeşitlilik sınırlıdır.

## Lisans

Görev tanımları, sentetik fixture'lar, insan yazımı sentetik OOD görevleri ve
proje tarafından üretilen araştırma artefaktları, proje sahiplerinin hak sahibi
olduğu ölçüde CC BY 4.0 altında yayımlanır. Atıf ve istisna ayrıntıları
[`DATA_LICENSE.md`](../DATA_LICENSE.md) içindedir.

Model ağırlıkları, tokenizer dosyaları, marka adları ve üçüncü taraf yazılım bu
veri lisansının kapsamında değildir. Ham izlerde bulunan model üretimi metinler
araştırma kanıtı olarak dağıtılır; proje, sahip olmadığı hakları yeniden
lisansladığını iddia etmez.
