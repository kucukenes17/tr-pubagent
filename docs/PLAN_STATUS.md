# 12 haftalık plan — güncel durum

Son güncelleme: 7 Eylül 2026

| Çalışma paketi | Durum | Kanıt / sonraki kapı |
| --- | --- | --- |
| Repo, CI, test ve üretim build'i | Tamamlandı | GitHub Actions, Python ve web testleri |
| 80 görevlik TR-PubBench | Tamamlandı | 24/16/40 dondurulmuş split |
| Phi-4 Unguarded / Guarded ana deney | Tamamlandı | `results/frozen` ham izleri ve kanonik özet |
| İstatistiksel final değerlendirme | Tamamlandı | 40 eşlenmiş test, exact McNemar |
| Gerçek veriye bağlı dashboard | Tamamlandı | Grafikler ve 40 görevlik JSONL replay explorer |
| İnsan yazımı OOD sağlamlık paketi | Tamamlandı | 24 görev, sızıntı denetimi ve dondurulmuş protokol |
| Çok-seed sağlamlık sonucu | Tamamlandı | 144 GPU koşusu: Guarded %91,7, Unguarded %8,3; exact McNemar p=1,73×10⁻¹⁸ |
| ML Guard / Hybrid Guard ablation | Tamamlandı | Üç guarded sistem 66/72; H3 desteklenmedi. XLM-R metadata ve ham izler arşivlendi |
| Kullanıcı ajan adaptörü / BYOA | Tamamlandı | `tr-pubagent.agent.v1` HTTP sözleşmesi, doğrudan/kural korumalı CLI, örnek ajan ve güvenlik kontrolleri |
| İkinci üretici model | Tamamlandı | Qwen2.5-7B: 8/24 → 24/24; 4 geçersiz eylem ve 2 ihlal → 0; p=3,05×10⁻⁵ |
| Guard v2.2 post-hoc düzeltme | Tamamlandı | 66/72 → 72/72; 6 yalnız-v2.2 başarısı, 0 regresyon, 0 ihlal; exact McNemar p=0,03125 |
| Altı ayrı portal yüzeyi | Tamamlandı | Burs, ders kaydı, randevu, belediye, sosyal yardım ve belge teslimi; tek guard motoruna bağlı erişilebilir sekmeler |
| Temiz makine Docker doğrulaması | Bekliyor | Docker Desktop bulunan ayrı ortamda smoke test |
| İngilizce README ve mimari görsel | Tamamlandı | İngilizce özet ve Mermaid mimarisi repoda |
| Demo videosu | Senaryo tamamlandı | 4 dakikalık çekim metni hazır; ekran kaydı bekliyor |
| TÜBİTAK 2209-A taslağı | Taslak tamamlandı | Kimlik, danışman, bütçe, tarih ve güncel kaynakça alanları başvuru öncesi doldurulacak |
| Resmî v1.0.0 release | Bekliyor | OOD sonucu ve yayın belgelerinden sonra |

## Sıradaki karar kapıları

1. Temiz Docker ortamında web ve API servisleri için smoke test yap.
2. Yayın belgelerini ve videoyu tamamlayıp `v1.0.0` sürümünü çıkar.
