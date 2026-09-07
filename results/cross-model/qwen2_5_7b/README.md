# Qwen2.5-7B çapraz-model doğrulaması

Bu klasör, sonuçlar görülmeden önce `docs/CROSS_MODEL_PROTOCOL.md` içinde
sabitlenen doğrulamanın kanonik artefaktlarını içerir.

- Üretici model: `Qwen/Qwen2.5-7B-Instruct`
- Model revision: `a09a35458c702b33eeacc393d103063234e8bc28`
- Deney commit'i: `4cddcf688adc227ea6f1643d1220e1f39db3a6da`
- Görevler: 24 insan yazımı sentetik OOD görevi
- Seed: 0; çıkarım deterministiktir
- Unguarded: 8/24 (%33,3), 4 geçersiz eylem, 2 gözlenen ihlal
- Guarded v2.1: 24/24 (%100), 0 geçersiz eylem, 0 gözlenen ihlal
- Exact McNemar: `p=3.0517578125e-05`

`raw/` tekrar üretilebilir adım izlerini, `derived/` istatistiksel özeti ve
görev tablosunu, `metadata/` ise SHA-256 bütünlük manifestini içerir. Çalışma
veritabanı yeniden üretilebilir olduğu ve kişisel çalışma durumu taşıdığı için
arşivlenmemiştir.
