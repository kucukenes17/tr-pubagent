# Üretici modeller arası doğrulama protokolü v1

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
