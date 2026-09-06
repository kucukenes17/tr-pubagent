# TR PubAgent — 4 dakikalık demo video senaryosu

## 0:00–0:25 — Problem

Ekran: Dashboard ana sayfa.

Anlatım: “Bir web ajanının formu tamamlaması tek başına yeterli değil. Kullanıcının vermediği bilgiyi uydurabilir, özel veriyi yazabilir veya son onay olmadan geri döndürülemez bir işlem yapabilir. TR PubAgent bu hataları Türkçe sentetik kamu hizmeti görevlerinde ölçüyor.”

## 0:25–0:55 — Benchmark

Ekran: Başarı grafiği ve yöntem sayfası.

Anlatım: “Benchmark altı hizmet ailesinde 80 görev içeriyor. Her görev görünür kullanıcı talimatı, portal durumu, yetki sözleşmesi ve yalnız değerlendiricinin gördüğü oracle koşullarıyla tanımlanıyor. Gerçek kişi verisi veya gerçek kamu bağlantısı yok.”

## 0:55–1:35 — Unguarded hata izi

Ekran: Replay sayfası, gizlilik ihlali bulunan görev; Unguarded sekmesi.

Anlatım: “Aynı Phi-4 modeli korumasız çalıştığında bu görevde kullanıcının yazılmamasını istediği alanı dolduruyor. Burada ham model eylemini, ortamın uygulayıp uygulamadığını, sonlanmayı ve ihlal etiketini görebiliyoruz.”

## 1:35–2:20 — Guarded karar zinciri

Ekran: Aynı görevde Guarded v2.1; adımlar ileri alınır.

Anlatım: “Guarded v2.1 araç ve hedef allowlist'ini, eksik bilgi kontrolünü, gizlilik kısıtlarını ve onay kapılarını uygular. Kanıtlanmayan bir eylemi engeller; mümkünse kullanıcıya soru veya onay adımına dönüştürür. Her karar gerekçe ve kanıt referansıyla kaydedilir.”

## 2:20–3:05 — Sonuç

Ekran: Final test metrikleri.

Anlatım: “Dondurulmuş 40 görevlik final testte Unguarded sıfır görev tamamladı, 25 geçersiz eylem ve 10 ihlal üretti. Guarded v2.1 kırk görevin tamamını, gözlenen ihlal olmadan bitirdi. Ortalama adım 9,2'den 2,2'ye, token kullanımı yüzde 92,7 azaldı. Exact McNemar p değeri 1,82 çarpı 10 üzeri eksi 12.”

## 3:05–3:35 — Bilimsel sınırlar

Ekran: Dashboard araştırma sınırı kutusu ve protokol belgesi.

Anlatım: “Bu sonuç tek model, tek seed ve şablon ilişkili sentetik görevler içindir; gerçek dünyaya yüzde yüz başarı olarak genellenemez. Dondurulmuş kümede sonradan bulunan bir tekrar da raporda açıkça korunuyor.”

## 3:35–4:00 — Sonraki deney

Ekran: `PLAN_STATUS.md` ve OOD protokolü.

Anlatım: “Sonraki aşamada 24 insan yazımı OOD görev, üç seed ve Rule, ML, Hybrid ablation çalıştırılacak. Proje; yeniden üretilebilir ham JSONL izleri, testler, veri ve sistem kartlarıyla açık biçimde yayımlanıyor.”

## Kayıt kontrol listesi

- 1920×1080, 30 fps; tarayıcı yakınlaştırma %100.
- Gerçek e-posta, token, kullanıcı adı veya Kaggle oturum bilgisi görünmez.
- Sonuç sayıları ekrandan okunur; hızlandırılmış replay dışında kesme yapılmaz.
- Altyazı eklenir; müzik konuşmayı bastırmaz.
- Videonun açıklamasına depo, canlı dashboard ve sınırlılıklar bağlantısı eklenir.
