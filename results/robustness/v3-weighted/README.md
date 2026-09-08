# Sınıf-ağırlıklı XLM-R v3 OOD ablation

Bu klasör, XLM-R v3 risk sınıflandırıcısının insan yazımı OOD görevlerdeki sürüm ayrımlı takip deneyini içerir.

- Üretici model: `microsoft/Phi-4-mini-instruct`
- Değerlendirme commit'i: `bc4e102cd4d67eaeeac4ab99dd2546559d771ac8`
- Görev × seed: 24 × 3
- ML eşiği: `0.80` (OOD sonucuna göre ayarlanmadı)
- Rule Guard: 66/72 başarı, 0 ihlal
- ML-only v3: 57/72 başarı, 3 ihlal
- Hybrid v3: 57/72 başarı, 0 ihlal
- H3: desteklenmedi

`package_manifest.json`, dışarı aktarılan paketteki dosyaların SHA-256 değerlerini ve deney kökenini kaydeder. Unguarded ve Rule ham izleri kanonik olarak üst klasörde tutulur; manifestteki hash'leri bu dosyalarla eşleşir. Model ağırlıkları boyut nedeniyle depoya dahil değildir; eğitim metadata'sı ve test raporu [`../../ml/xlmr-risk-v3-weighted`](../../ml/xlmr-risk-v3-weighted) altındadır.
