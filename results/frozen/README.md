# Dondurulmuş sonuç paketi

Bu dizin, TR-PubAgent'ın 5–7 Eylül 2026 Kaggle T4 deneylerinden doğrulanan ham ve türetilmiş çıktıları içerir.

## Dizinler

- `raw/`: görev kataloğu, scripted kontrol ve Phi-4 koşularının satır bazlı JSONL izleri.
- `derived/`: kanonik özetler ve görev düzeyindeki eşleştirilmiş CSV tabloları.
- `metadata/`: çalışma ortamı ve SHA-256 bütünlük manifestleri.

Kanonik sayısal kaynak `derived/frozen_summary.json`, kanonik bütünlük kaynağı `metadata/canonical_sha256_manifest.json` dosyasıdır.

## Yeniden üretme

Repo kökünde:

```bash
python benchmark/generate_frozen_report.py
```

Komut yedi dondurulmuş ajan dosyasındaki görev sayılarını ve benzersiz kimlikleri doğrular; development, validation ve test karşılaştırmalarını yeniden hesaplar; tüm görevleri tek CSV'de birleştirir ve manifesti yeniler.

## Kapsam

Ham veriler sentetiktir ve gerçek kişisel veri içermez. Test sonucu gerçek kamu portallarına, farklı modellere veya serbest biçimli insan taleplerine doğrudan genellenemez. Ayrıntılı yorum ve protokol sapmaları için [`docs/EXPERIMENT_RESULTS.md`](../../docs/EXPERIMENT_RESULTS.md) belgesine bakın.
