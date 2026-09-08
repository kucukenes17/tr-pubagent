# Phi-4 gerçek tarayıcı aktarım protokolü v2

> Durum: Bu protokol, v1 development pilotinde gözlenen eylem-hedef
> temellendirme başarısızlığından sonra ve v2 test sonuçları görülmeden
> önce hazırlanmıştır. V1 pilot sonuçları korunur ve v2 sonucu olarak
> yeniden etiketlenmez.

## Pilot bulgusu ve tek tasarım değişikliği

V1'de Phi-4, ARIA düğme etiketlerini tool/target kimliklerine güvenilir
biçimde bağlayamadı. Beş development görevinin hiçbiri tamamlanmadı;
model sayfa başlıklarını veya CSS benzeri ifadeleri hedef yaptı ve başarılı
eylemleri tekrarladı.

V2, canlı HTML formlarından çıkarılan bir public action catalog ekler.
Katalog yalnızca render edilmiş kontroldeki tool, target_id, etiket, mevcut
değer ve görünür select seçeneklerini taşır. Task oracle, authorization
contract, user response policy, beklenen alanlar ve gizli backend state katalogda
yer almaz. Aynı katalog unguarded ve rule sistemlerine verilir.

Rule sistemi ayrıca yapılandırılmış deneylerde zaten kullanılan deterministik
terminal controller'ı kullanır: gerekli alan kalmadığında onay, submit ve finish
adımlarını guard tarafından tamamlar. Bu controller modele oracle göstermez.

## Sabit v2 tasarımı

- Ortam: Playwright Chromium + loopback FastAPI HTML portalı.
- Model: `microsoft/Phi-4-mini-instruct`, NF4 4-bit, `do_sample=False`, seed 0.
- Sistemler: unguarded ve deterministic Rule Guard v2 controller.
- Development smoke: ilk 5 development görevi.
- Nihai aktarım: dondurulmuş 40 test görevi, bir koşu/sistem.
- V2 smoke sonrası prompt, katalog, guard veya görev değiştirilmez. Yalnızca
  sonuç kaydını engelleyen yürütme hataları ayrı commit ile düzeltilebilir.
- V1 ve v2 sonuçları farklı dosya ve sürüm etiketleriyle saklanır.

## Birincil ölçüm ve sınırlar

Birincil ölçüm aynı görevde başarı ve sıfır ihlalin birlikte sağlanmasıdır.
Ek olarak geçersiz eylem, sonlanma, adım, gecikme, token, guard block ve
enforcement sayıları raporlanır. Bu deney sentetik yerel portalları ölçer;
gerçek kamu sitelerine doğrudan genellenemez.
