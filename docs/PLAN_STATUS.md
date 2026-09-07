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
| İkinci üretici model | Bekliyor | GPU kotasına göre 24 OOD görevde ek model |
| Altı ayrı portal yüzeyi | Kısmi | Backend altı hizmeti kapsıyor; frontend burs demosu ağırlıklı |
| Temiz makine Docker doğrulaması | Bekliyor | Docker Desktop bulunan ayrı ortamda smoke test |
| İngilizce README ve mimari görsel | Tamamlandı | İngilizce özet ve Mermaid mimarisi repoda |
| Demo videosu | Senaryo tamamlandı | 4 dakikalık çekim metni hazır; ekran kaydı bekliyor |
| TÜBİTAK 2209-A taslağı | Taslak tamamlandı | Kimlik, danışman, bütçe, tarih ve güncel kaynakça alanları başvuru öncesi doldurulacak |
| Resmî v1.0.0 release | Bekliyor | OOD sonucu ve yayın belgelerinden sonra |

## Sıradaki karar kapıları

1. OOD'de bulunan iki sistematik sınırı v2.2 post-hoc deneyinde ayrı etiketle ve yeniden değerlendir.
2. İkinci üretici model ile 24 OOD görevi çalıştır.
3. Altı hizmet için frontend portal yüzeylerini genişlet ve temiz Docker ortamında smoke test yap.
4. Yayın belgelerini ve videoyu tamamlayıp `v1.0.0` sürümünü çıkar.
