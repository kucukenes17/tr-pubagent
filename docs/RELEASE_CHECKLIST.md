# v1.0.0 yayın kontrol listesi

Bu liste, proje sahibinin açık onayıyla yayımlanan `v1.0.0` sürümünün kapanış
kaydını tutar.

## Tamamlanan teknik kapılar

- [x] Kaynak kod için tam Apache-2.0 metni ve NOTICE
- [x] Sentetik görev/veri/araştırma artefaktları için CC BY 4.0 kapsamı
- [x] Üçüncü taraf model ve bağımlılık istisnaları
- [x] Makinece okunabilir `CITATION.cff`
- [x] Dondurulmuş ana test, OOD, ikinci model ve Chromium sonuçları
- [x] Ham izler ve SHA-256 manifestleri
- [x] Dashboard üretim derlemesi ve temiz GitHub CI
- [x] Bilimsel sınırlamalar ve post-hoc ayrımı
- [x] Demo videosunun yayın ön koşulu olmaktan çıkarılması

## Bilinçli kapsam kararları

- İlk taslaktaki “3 sistem × 80 görev” tek bir deney olarak uygulanmadı.
  Bunun yerine ana 80 görevlik benchmark iki sistemle; dört sistemli ablation
  ise daha zor, insan yazımı 24 OOD görev × üç seed üzerinde yürütüldü. Bu
  sapma açıkça raporlanır ve 240 koşu yapılmış gibi sunulmaz.
- Gerçek tarayıcı aktarımı Playwright/Chromium üzerinde tamamlandı; sayfalar
  yerel ve sentetik olduğu için canlı kamu portalı kanıtı sayılmaz.
- Model ağırlıkları depoya konmaz; yeniden üretme kodu ve metadata yayımlanır.
- TÜBİTAK başvurusu ve demo videosu kullanıcı kararıyla sürüm kapsamı dışıdır.

## Yayından hemen önce

- [x] Proje sahibi public release için açık onay verir.
- [x] `package.json` ve `CITATION.cff` sürümü `1.0.0` yapılır.
- [x] Son `main` CI koşusu başarıyla tamamlanır.
- [x] Açıklamalı `v1.0.0` tag'i oluşturulur.
- [x] GitHub Release notunda sentetik ortam sınırı ilk ekranda belirtilir.
- [x] GitHub'ın kaynak ZIP/TAR paketleri release sayfasında yayımlanır.

## Önerilen release başlığı

`TR PubAgent v1.0.0 — Turkish authorization-aware web-agent benchmark`

## Önerilen kısa açıklama

İlk araştırma sürümü; 80 görevlik Türkçe sentetik benchmarkı, Rule/ML/Hybrid
guard ablation'ını, Phi-4 ve Qwen doğrulamalarını, BYOA protokolünü ve gerçek
Chromium üzerinde yerel sentetik portal aktarımını içerir. Sonuçlar canlı kamu
sitelerine veya gerçek kişilere genellenmez.
