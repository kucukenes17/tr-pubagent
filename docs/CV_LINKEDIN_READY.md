# CV ve LinkedIn için hazır metinler

Bu metinler doğrudan kullanılabilir. Sonuçlar sentetik araştırma ortamıyla
sınırlıdır; “devlet sistemlerinde kullanıldı” veya “gerçek dünyada %100
güvenli” ifadeleri eklenmemelidir.

## Türkçe CV — önerilen iki madde

- **TR-PubAgent:** Altı kamu hizmeti benzeri alanda 80 görev içeren Türkçe,
  yeniden üretilebilir bir web-ajan benchmarkı; FastAPI/SQLite değerlendirme
  ortamı ve yetki, gizlilik, eksik bilgi, son onay ile durum bütünlüğünü
  denetleyen runtime guard geliştirdim.
- Dondurulmuş insan yazımı OOD deneyinde Phi-4 başarısını %8,3'ten %91,7'ye
  çıkarıp 45 geçersiz eylemi ve 12 gözlenen ihlali sıfıra indirdim; ayrı
  Playwright/Chromium aktarımında başarıyı 0/40'tan 25/40'a çıkarıp token
  kullanımını %53,9 azalttım (eşlenmiş istatistiksel testlerle doğrulandı).

## English CV — recommended two bullets

- **TR-PubAgent:** Built a reproducible 80-task Turkish benchmark, a
  FastAPI/SQLite evaluation environment, and an authorization-aware runtime
  guard for web agents covering privacy, missing information, confirmation
  gates, language interpretation, and state preservation.
- Improved Phi-4 success from 8.3% to 91.7% on a frozen human-authored OOD
  suite while reducing 45 invalid actions and 12 observed violations to zero;
  in a separate Playwright/Chromium transfer, improved completion from 0/40 to
  25/40 and reduced generated tokens by 53.9%.

## LinkedIn proje açıklaması

TR-PubAgent v1.0.0 yayımlandı. Proje, Türkçe web ajanlarını yalnız “görevi
bitirdi mi?” sorusuyla değil; yetki sınırı, eksik bilgi, gizlilik, son onay,
dil yorumlama ve durum bütünlüğü açısından değerlendiren açık kaynaklı bir
araştırma platformudur.

Altı hizmet ailesinde 80 sentetik görev, deterministik bir FastAPI/SQLite
değerlendirme ortamı, Rule/ML/Hybrid guard karşılaştırmaları ve kendi ajanını
getir protokolü geliştirdim. Dondurulmuş 24 görev × üç seed OOD deneyinde
Phi-4 başarısı %8,3'ten %91,7'ye çıkarken 45 geçersiz eylem ve 12 gözlenen
ihlal sıfıra indi. Qwen2.5-7B ile yapılan ikinci-model doğrulamasında başarı
8/24'ten 24/24'e yükseldi.

Ayrı bir Playwright/Chromium deneyinde ajan, yapılandırılmış simülatör yerine
gerçek HTML ve DOM üzerinden çalıştı: Rule Guard başarıyı 0/40'tan 25/40'a
çıkardı, 11 gözlenen durum-bozulması ihlalini sıfırladı ve token kullanımını
%53,9 azalttı. Bütün görevlerin ve portal sayfalarının sentetik olduğunu;
sonuçların canlı kamu sitelerine doğrudan genellenemeyeceğini açıkça
raporluyorum.

- Kaynak kod: https://github.com/kucukenes17/tr-pubagent
- Dashboard: https://tr-pubagent-dashboard.eneskucuk1617.chatgpt.site

## Kısa proje özeti

Türkçe web ajanlarında görev başarısı ile süreç güvenliğini birlikte ölçen;
Phi-4 ve Qwen üzerinde doğrulanmış, Rule/ML/Hybrid karşılaştırmaları ve gerçek
Chromium aktarımı içeren açık kaynaklı benchmark ve runtime guard projesi.
