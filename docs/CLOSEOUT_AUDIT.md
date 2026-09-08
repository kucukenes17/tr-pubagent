# İlk plana göre kapanış denetimi

8 Eylül 2026 — yerel kod ve arşiv belgeleri incelendi. Bu belge bir release
ilanı veya yeni GPU deneyi değildir. Dondurulmuş sonuçlar değiştirilmedi.

## Bu turda kapatılan teknik eksik

İlk plan Scripted Oracle'ın bütün görevlerde başarılı olmasını istiyordu.
Yeni 80 görevlik regresyon kontrolü başlangıçta 66/80 geçti: seçim alanlarına
`fill` gönderilmesi 14 görevi bozuyordu. `benchmark/run_scripted.py` artık
alan türüne göre `select` kullanır, zaten doğru olan alanları yeniden yazmaz
ve reddedilen işlemleri sessizce yutmaz. Test, başarı yanında ihlal ve
`invalid_action` olaylarının yokluğunu da denetler.

Bu, gizli beklenen değerleri gören altyapı doğrulayıcısıdır; model performansı
veya yeni bilimsel baseline olarak raporlanamaz. Önceki scripted arşivleri
silinmez ya da bu yeni sonuçlarla üzerine yazılmaz.

## İlk planla farklar ve açık kabul ölçütleri

| Madde | Mevcut kanıt / durum | Kapanış için gereken |
| --- | --- | --- |
| Gerçek tarayıcı üzerinden ajan yürütme | Tamamlandı: 80/80 gold-aware altyapı testine ek olarak frozen Browser v2 protokolünde 40 Unguarded + 40 Rule Guard Phi-4 koşusu yapıldı. Başarı 0/40→25/40, ihlal 11→0; ham iz ve manifest yayımlandı | Canlı kamu sitesi veya insan katılımcı sonucu değildir; yerel sentetik HTML kapsamını koru. [Protokol](BROWSER_MODEL_PROTOCOL_V2.md), [sonuçlar](../results/browser/phi4-v2) |
| En az 3 sistem × 80 ana görev | Ana 80 görev iki sistemle; dört sistemli ablation daha zor, insan yazımı 24 OOD görev × üç seed ile yürütüldü | Bilinçli kapsam sapması: 240 koşu yapılmış sayılmaz. v1.0.0 önerisi mevcut OOD ablation'ını esas alır; yeni 240 koşu release kapısı değildir |
| Şablon ayrışmış frozen split | Şablon ilişkisi/tekrar sınırlılığı raporlanmış; ayrı OOD paketi mevcut | İlk sızıntısız split beklentisinden sapmayı koru; eski test kümesini değiştirme |
| Ek metrikler | Soru P/R/F1 ve tekrar ölçümü iki frozen sistemde raporlandı. Ayrı, gold görmeyen şeffaf kural çıkarıcısı 80 şablonlu görevde sözleşme exact-match 80/80 ve alan-micro F1 1,0 verdi | Şablon sonucu doğal dil/OOD çıkarım kanıtı değildir; daha güçlü iddia için görülmemiş insan yazımı sözleşme seti gerekir. [Tanımlar ve sonuçlar](SUPPLEMENTARY_METRICS.md) |
| SQLAlchemy/Alembic, koşu başına ayrı DB | Bilinçli kapsam değişikliği: stdlib `sqlite3`, ortak DB ve run_id izolasyonu korunuyor. Adım tahsisi atomik, `(run_id, step)` benzersiz; ayrı ve aynı koşuya paralel yazım testleri var | Kabul edildi; üretim ölçeği iddiası yok |
| OpenAPI'den üretilmiş TS istemcisi | FastAPI OpenAPI şemasından bağımlılıksız tipli istemci üretiliyor; gömülü şema SHA-256'sı ve birebir üretim testi CI'da eskimeyi yakalıyor | Tamamlandı; hosted dashboard şu anda statik frozen veri kullanır, canlı API istemcisi yalnız entegrasyon yüzeyidir |
| JSONL + Parquet | Kayıpsız JSON-kayıt sütunlu Parquet dışa aktarımı, geri okuma eşdeğerlik testi ve SHA-256 manifest eklendi; 80 frozen test kaydı aktarıldı | Tamamlandı; iç içe alanlar JSON metni olarak korunur, eski arşivlere yazılmaz |
| ML eğitim ayrıntıları | Erken durdurma, ayrı test raporu ve varsayılan dengeli sınıf-ağırlıklı çapraz entropi kodu mevcut | Yeni kodla yeniden eğitim ayrı sürüm/artefakt ister; mevcut XLM-R v2 sonucu ağırlıklı eğitim diye yeniden etiketlenmez |
| Yayın yeri / paketleme | npm/Vinext ve Sites; ilk planda pnpm/Next.js/HF Static Space vardı | Uygulanan mimariyi esas alan açık kapsam kaydı; erişimsiz oturumda demo görünürlüğü doğrulaması |
| Veri / ağırlık dağıtımı | Tam Apache-2.0, NOTICE, CC BY 4.0 veri kapsamı, üçüncü taraf istisnaları ve `CITATION.cff` eklendi. Model ağırlıkları depoya dahil değil | Tamamlandı; upstream model koşulları yeniden lisanslanmaz |
| Demo videosu | Kullanıcı tarafından iptal | Açık iş değildir; yayın engeli olmaktan çıkarıldı |
| v1.0.0 | Paket/CFF sürümü, changelog, sürüm notu, tag ve GitHub Release tamamlandı | Tamamlandı; yeni yöntemler ayrı sürüm ve protokolle yürütülür |

## Sürüm sonrası isteğe bağlı sıra

1. İstenirse sözleşme çıkarımını insan yazımı, görülmemiş bir kümede doğrula; programatik baseline ölçümü tamamlandı.
2. Yeni model aileleri ve kötü niyetli DOM/prompt-injection senaryoları ekle.

Soru metrikleri, Parquet, OpenAPI/TypeScript sözleşmesi ve eşzamanlı koşu
izolasyonu teknik olarak kapatıldı. Dengeli sınıf-ağırlıklı eğitim yolu hazır,
ancak eski XLM-R artefaktını geriye dönük değiştirmez; yeniden eğitim yeni bir
sürüm olarak kaydedilmelidir. TÜBİTAK başvurusu kullanıcı kararıyla kapsam dışıdır.

Yeni mimari veya deneyler, mevcut frozen model sonuçlarını geriye dönük
değiştirmeden ayrı sürüm ve protokolle yürütülmelidir.
