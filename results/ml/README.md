# XLM-R risk classifier artifacts

Bu klasör, Rule/ML/Hybrid OOD ablation için kullanılan 3.000 örnekli deterministik sentetik veri kümesini ve eğitim metadata'sını içerir.

- Temel model: `FacebookAI/xlm-roberta-base`
- Özellik şeması: `xlmr-risk-v2-json`
- Test örneği: 398
- Test macro-F1: `1.0`
- Runtime eşiği: `0.80`

Test örnekleri sınıf başına tekrar eden sentetik kalıplardan gelir; macro-F1 dış geçerlilik veya gerçek dünya başarısı değildir. Uçtan uca OOD sonucu [`../robustness/guard_ablation_summary.json`](../robustness/guard_ablation_summary.json) dosyasında raporlanır.

Model ağırlıkları boyut nedeniyle bu depoya dahil edilmez. Ağırlıklar `ml/train_risk_classifier.py` ile veri kümesinden yeniden üretilebilir; burada config, tokenizer metadata, test raporu ve eğitim kökeni saklanır.

## Sınıf-ağırlıklı v3 takip sürümü

`xlmr-risk-v3-weighted` klasörü, aynı veri snapshot'ıyla dengeli sınıf ağırlıklı çapraz entropi kullanılarak yeniden eğitilen takip sürümünün metadata ve test raporunu içerir. Sentetik test macro-F1 değeri `1,0` olsa da insan yazımı OOD ablation'da ML-only ve Hybrid 57/72 başarı verdi; Rule Guard 66/72'de kaldı. Bu fark, sentetik sınıflandırma metriğinin uçtan uca OOD ajan sonucu olmadığını gösterir. Ham izler [`../robustness/v3-weighted`](../robustness/v3-weighted) altındadır.
