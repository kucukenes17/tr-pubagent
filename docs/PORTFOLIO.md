# CV, portföy ve mülakat anlatımı

Bu metinler dondurulmuş sentetik test sonucuyla sınırlıdır. “Gerçek dünyada yüzde yüz güvenlik” veya “devlet sistemlerinde kullanıldı” ifadeleri kullanılmamalıdır.

## Türkçe CV — tek satır

**TR-PubAgent:** Türkçe yetki-duyarlı web ajanları için 80 görevlik yeniden üretilebilir sentetik benchmark ve runtime guard geliştirdim; Phi-4-mini-instruct üzerinde dondurulmuş 40 görevlik testte başarıyı 0/40'tan 40/40'a çıkarırken gözlenen 10 güvenlik ihlalini sıfıra, token kullanımını %92,7 azalttım (exact McNemar p<2×10⁻¹²).

## English CV — one line

**TR-PubAgent:** Built a reproducible 80-task synthetic Turkish benchmark and authorization-aware runtime guard for web agents; on a frozen 40-task Phi-4-mini-instruct test split, improved task success from 0/40 to 40/40, eliminated 10 observed safety violations, and reduced generated tokens by 92.7% (exact McNemar p<2×10⁻¹²).

## CV maddeleri

- Designed an 80-task Turkish benchmark spanning six public-service-like domains and five risk families: missing information, confirmation gates, privacy, language interpretation, and state preservation.
- Implemented a FastAPI/SQLite agent environment, deterministic state-based evaluator, action traces, authorization contracts, evidence grounding, and a guarded execution controller.
- Ran reproducible NF4 4-bit Phi-4 experiments on Kaggle T4 with frozen Git/model/prompt provenance and published raw JSONL traces plus SHA-256 manifests.
- Evaluated paired development, validation, and held-out synthetic test splits; final test success increased from 0/40 to 40/40 with no observed guarded violations and 92.7% fewer generated tokens.
- Confirmed the frozen guard on a second producer model: Qwen2.5-7B improved from 8/24 to 24/24 on the pre-specified OOD suite, with invalid actions falling from 4 to 0 and observed violations from 2 to 0 (exact McNemar p=3.05×10⁻⁵).
- Documented negative results, protocol deviations, confidence intervals, exact McNemar tests, limitations, and non-generalization claims.

## LinkedIn proje açıklaması

TR-PubAgent, Türkçe web ajanlarını yalnızca “görevi bitirdi mi?” sorusuyla değil; yetki sınırı, eksik bilgi, gizlilik, son onay ve durum bütünlüğü açısından ölçen açık kaynaklı bir araştırma projesidir. Projede 80 sentetik görev, FastAPI/SQLite tabanlı deterministik değerlendirme ortamı ve yetki-duyarlı bir runtime guard geliştirdim. Yöntemi validation öncesinde dondurup 40 görevlik ayrılmış Phi-4 testinde başarıyı 0/40'tan 40/40'a çıkardım. Sonuçlar görülmeden önce sabitlenen ikinci-model doğrulamasında Qwen2.5-7B başarısı 8/24'ten 24/24'e çıktı; gözlenen ihlaller 2'den 0'a indi. Ham izler, commit/model provenance bilgisi ve SHA-256 manifestleri repoda yayımlanmıştır. Sonuçların sentetik benchmark ile sınırlı olduğunu ve gerçek kamu portallarına doğrudan genellenemeyeceğini özellikle raporladım.

## Mülakatta iki dakikalık anlatım

“Projeye Türkçe kamu hizmeti benzeri görevlerde ajan güvenliğini ölçmek için başladım. Başarıyı yalnızca son ekrana göre değil, gerçek form durumu ve eylem günlüğüne göre tanımladım. İlk Phi-4 ajanı development görevlerinde yalnızca 2/20 başarı elde etti; tekrar döngüleri, geçersiz araç çağrıları, gizlilik ve olumsuzluk yorumlama hataları gördüm. Bunun üzerine hedef allowlist'i, yetki sözleşmesi, eksik bilgi ve onay kapıları, tekrar tespiti, güvenli sonlandırma ve kullanıcı metnindeki açık değerleri forma bağlayan bir katman geliştirdim. Yöntemi validation öncesinde dondurdum; 40 görevlik testte başarı 0/40'tan 40/40'a çıktı. Sonra ayrı bir ön kayıtla aynı guard'ı Qwen2.5-7B üzerinde sınadım ve OOD başarısı 8/24'ten 24/24'e yükseldi. En önemli dersim, yüksek görünen ortalama safety score'un görev başarısızlığını ve kontrol döngülerini saklayabilmesi oldu. Sonuçları iki model ve sentetik ortamla sınırlı olarak raporluyorum.”

## Teknik anahtar kelimeler

`LLM agents`, `AI safety`, `tool calling`, `authorization`, `runtime guardrails`, `evidence grounding`, `FastAPI`, `SQLite`, `Pydantic`, `Next.js`, `Kaggle`, `Phi-4`, `Qwen2.5`, `4-bit quantization`, `JSONL traces`, `McNemar test`, `Wilson confidence interval`, `reproducible ML evaluation`
