# 12 haftalık plan — güncel durum

Son güncelleme: 7 Eylül 2026

| Çalışma paketi | Durum | Kanıt / sonraki kapı |
| --- | --- | --- |
| Repo, CI, test ve üretim build'i | Tamamlandı | GitHub Actions, Python ve web testleri |
| 80 görevlik TR-PubBench | Tamamlandı | 24/16/40 dondurulmuş split |
| Phi-4 Unguarded / Guarded ana deney | Tamamlandı | `results/frozen` ham izleri ve kanonik özet |
| İstatistiksel final değerlendirme | Tamamlandı | 40 eşlenmiş test, exact McNemar |
| Gerçek veriye bağlı dashboard | Tamamlandı | Grafikler ve 40 görevlik JSONL replay explorer |
| İnsan yazımı OOD sağlamlık paketi | Altyapı tamamlandı | 24 görev, sızıntı denetimi, çok-seed runner; Kaggle koşusu bekliyor |
| Çok-seed sağlamlık sonucu | Bekliyor | 144 GPU koşusu ve `analyze_robustness.py` |
| ML Guard / Hybrid Guard ablation | Bekliyor | XLM-R artefaktının geri alınması ve dört sistem karşılaştırması |
| İkinci üretici model | Bekliyor | GPU kotasına göre 24 OOD görevde ek model |
| Altı ayrı portal yüzeyi | Kısmi | Backend altı hizmeti kapsıyor; frontend burs demosu ağırlıklı |
| Temiz makine Docker doğrulaması | Bekliyor | Docker Desktop bulunan ayrı ortamda smoke test |
| İngilizce README ve mimari görsel | Bekliyor | Yayın paketi |
| Demo videosu | Bekliyor | 3–5 dakika, dashboard + replay |
| TÜBİTAK 2209-A taslağı | Bekliyor | Amaç, yöntem, iş-zaman, risk ve yaygın etki |
| Resmî v1.0.0 release | Bekliyor | OOD sonucu ve yayın belgelerinden sonra |

## Sıradaki karar kapıları

1. OOD robustness koşularını Kaggle'da tamamla ve ham ZIP'i arşivle.
2. Sonuç makulse dashboard'a ikinci “OOD Sağlamlık” bölümü ekle; başarısızsa hata taksonomisini yayınla.
3. XLM-R artefaktı bulunursa ML/Hybrid ablation'a geç; bulunamazsa veri ve modeli yeniden üret.
4. Yayın belgelerini ve videoyu tamamlayıp `v1.0.0` sürümünü çıkar.
