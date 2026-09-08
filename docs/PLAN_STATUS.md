# 12 haftalık plan — güncel durum

Son güncelleme: 8 Eylül 2026

Bu tablo mevcut araştırma prototipini özetler; ilk plandaki bütün kabul
ölçütlerinin tamamlandığı anlamına gelmez. İlk planla farklar ve yayın
kapıları [kapanış denetiminde](CLOSEOUT_AUDIT.md) ayrı izlenir.

| Çalışma paketi | Durum | Kanıt / sonraki kapı |
| --- | --- | --- |
| Repo, CI, test ve üretim build'i | Tamamlandı | GitHub Actions, Python ve web testleri |
| 80 görevlik TR-PubBench | Tamamlandı | 24/16/40 dondurulmuş split |
| Phi-4 Unguarded / Guarded ana deney | Tamamlandı | `results/frozen` ham izleri ve kanonik özet |
| İstatistiksel final değerlendirme | Tamamlandı | 40 eşlenmiş test, exact McNemar |
| Ek soru metrikleri ve Parquet | Tamamlandı | 80 frozen test kaydında post-hoc P/R/F1, tekrar sayısı, kayıpsız Parquet ve manifest; `docs/SUPPLEMENTARY_METRICS.md` |
| Sözleşme çıkarımı alan-F1 | Programatik baseline tamamlandı | Gold kabul etmeyen Türkçe kural çıkarıcısı: 80/80 exact-match, alan-micro F1 1,0. Şablon-içi sonuçtur; insan yazımı OOD doğrulaması yok |
| Gerçek veriye bağlı dashboard | Tamamlandı | Grafikler ve 40 görevlik JSONL replay explorer |
| İnsan yazımı OOD sağlamlık paketi | Tamamlandı | 24 görev, sızıntı denetimi ve dondurulmuş protokol |
| Çok-seed sağlamlık sonucu | Tamamlandı | 144 GPU koşusu: Guarded %91,7, Unguarded %8,3; exact McNemar p=1,73×10⁻¹⁸ |
| ML Guard / Hybrid Guard ablation | Tamamlandı | Üç guarded sistem 66/72; H3 desteklenmedi. XLM-R metadata ve ham izler arşivlendi |
| Sınıf-ağırlıklı ML eğitim yolu | Kod tamamlandı | Varsayılan dengeli ağırlıklar, eksik sınıf koruması ve metadata kaydı; mevcut XLM-R v2 ağırlıksız kaldı, yeniden eğitim yeni sürüm olmalı |
| Kullanıcı ajan adaptörü / BYOA | Tamamlandı | `tr-pubagent.agent.v1` HTTP sözleşmesi, doğrudan/kural korumalı CLI, örnek ajan ve güvenlik kontrolleri |
| İkinci üretici model | Tamamlandı | Qwen2.5-7B: 8/24 → 24/24; 4 geçersiz eylem ve 2 ihlal → 0; p=3,05×10⁻⁵ |
| Guard v2.2 post-hoc düzeltme | Tamamlandı | 66/72 → 72/72; 6 yalnız-v2.2 başarısı, 0 regresyon, 0 ihlal; exact McNemar p=0,03125 |
| Altı ayrı portal yüzeyi | Tamamlandı | Burs, ders kaydı, randevu, belediye, sosyal yardım ve belge teslimi; tek guard motoruna bağlı erişilebilir sekmeler |
| Temiz makine Docker doğrulaması | Tamamlandı | GitHub temiz Ubuntu runner'ında production imajları, API sağlık ve dashboard HTTP smoke testi geçti (run 34162022568) |
| İngilizce README ve mimari görsel | Tamamlandı | İngilizce özet ve Mermaid mimarisi repoda |
| Scripted Oracle tam görev kontrolü | Tamamlandı | 80 görevin her biri için başarı, sıfır ihlal ve sıfır geçersiz eylem regresyon testi |
| Yerel gerçek tarayıcı yürütme | İlk sürüm tamamlandı | Playwright + gerçek HTML formları; 80/80 gold-aware Chromium ulaşılabilirlik kontrolü. Harici ajana yalnız DOM gözlemi. Yeni model ölçümü ve fixture upload henüz yok; `docs/BROWSER_BENCHMARK.md` |
| OpenAPI/TypeScript sözleşmesi | Tamamlandı | FastAPI'den otomatik üretilen tipli istemci, şema hash'i, eskime testi ve CI kontrolü |
| Eşzamanlı koşu izolasyonu | Tamamlandı | Atomik olay adımları, `(run_id, step)` benzersizliği; ayrı ve aynı run paralel yazım testleri |
| Demo videosu | Kullanıcı kararıyla iptal | AI tanıtımı ve klasik ekran kaydı kapsamdan çıkarıldı; release ön koşulu değil |
| Resmî v1.0.0 release | Bekliyor | Kapanış denetimi, lisans/kapsam kararları ve yayın onayı sonrası |

## Sıradaki karar kapıları

1. [Kapanış denetimindeki](CLOSEOUT_AUDIT.md) açık teknik kriterleri tamamla veya kapsam değişikliğini kullanıcıyla karara bağla.
2. Lisans ve yayın kontrolünü tamamla; kullanıcı onayı olmadan tag/release yayımlama.

TÜBİTAK başvurusu 8 Eylül 2026 tarihli kullanıcı kararıyla kapsamdan
çıkarılmıştır; tarihsel taslak yalnız arşivdir ve açık iş sayılmaz.
