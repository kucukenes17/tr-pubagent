# Üretici modeller arası doğrulama protokolü v1

> Durum: Ön kayıtlı koşu 7 Eylül 2026'da tamamlandı. Aşağıdaki tasarım sonuçlar görülmeden önce sabitlendi; gerçekleşen sonuç belgenin sonunda ayrı verilir.

## Amaç

Bu doğrulama, Guarded v2.1 kazanımının yalnızca `microsoft/Phi-4-mini-instruct`
modeline özgü olup olmadığını sınar. İkinci üretici model
`Qwen/Qwen2.5-7B-Instruct` olarak deney başlamadan önce sabitlenmiştir.

## Dondurulan tasarım

- Görevler: değiştirilmemiş 24 insan yazımı OOD görevi.
- Sistemler: Unguarded v1 ve kural tabanlı Guarded v2.1.
- Model: `Qwen/Qwen2.5-7B-Instruct`, NF4 4-bit.
- Çıkarım: `do_sample=False`; seed `0` yalnızca çalışma zamanı kaydı içindir.
- Koşu sayısı: 24 görev × 2 sistem = 48 eşlenmiş koşu.
- Birincil metrik: görev başarı oranındaki eşlenmiş mutlak fark.
- Güvenlik metrikleri: ihlal sayısı, geçersiz eylem sayısı ve ortak güvenli-başarı.
- İstatistik: tam McNemar testi ve görev düzeyinde bootstrap güven aralığı.

Tek seed seçimi deterministik çıkarımda aynı koşuyu üç kez tekrar etmemek içindir.
Model, istemler, görevler, oracle, koruma kuralları veya değerlendirici sonuçlar
görüldükten sonra değiştirilmeyecektir.

## İzolasyon ve yeniden üretilebilirlik

Çıktılar `results/cross-model/qwen2_5_7b/` benzeri ayrı bir klasöre yazılır.
`--run-label qwen2_5_7b` zorunlu kullanılır; böylece dondurulmuş Phi-4 JSONL
dosyalarının üzerine yazılamaz. Her satır model kimliğini, model revizyonunu,
Git commit'ini, seed'i ve deney kimliğini taşır. Kesilen Kaggle oturumunda aynı
komut yeniden çalıştırıldığında tamamlanan görevler atlanır.

## Başarı ölçütü

Çapraz-model hipotezi, Guarded v2.1'in başarı oranını artırması ve güvenlik
ihlallerini artırmaması halinde desteklenir. Sonuç ne olursa olsun raporlanır;
Phi-4 üzerinde dondurulmuş ana sonuçların yerine geçmez, harici doğrulama olarak
sunulur.

## Gerçekleşen sonuç

48 model koşusu tamamlandı. Unguarded 8/24 (%33,3), Guarded v2.1 24/24
(%100) başarı verdi. Geçersiz eylemler 4'ten 0'a, gözlenen ihlaller 2'den 0'a
indi. On altı görev yalnız Guarded tarafından, sekiz görev iki sistem tarafından
başarıldı; ters sonuç yoktu. Mutlak fark +66,7 yüzde puan, görev bootstrap %95
aralığı +45,8–+83,3 yüzde puan ve exact McNemar `p=3,0517578125×10⁻⁵`
olarak ölçüldü. Ham artefaktlar
[`results/cross-model/qwen2_5_7b`](../results/cross-model/qwen2_5_7b)
altındadır.
