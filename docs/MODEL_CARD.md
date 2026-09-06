# TR-PubGuard v2.1 sistem kartı

## Sistem

TR-PubGuard v2.1 tek bir üretici model veya öğrenilmiş güvenlik sınıflandırıcısı değildir. Dondurulmuş deney sistemi üç parçadan oluşur:

1. `microsoft/Phi-4-mini-instruct`, görünür görev ve form durumundan yapılandırılmış araç eylemleri önerir.
2. Evidence-grounding adaptörü yalnızca kullanıcı isteğinde açıkça bulunan değerleri eksik, yazılabilir metin alanlarına bağlar; gizli oracle durumunu görmez.
3. Deterministik yürütme katmanı araç/hedef allowlist'i, yetki sözleşmesi, gizlilik kısıtları, eksik bilgi, onay kapıları, tekrar tespiti ve güvenli sonlandırmayı uygular.

Depoda ayrıca XLM-RoBERTa risk sınıflandırıcısı için veri üretme ve eğitim kodu vardır. Ancak XLM-R, `guarded-v2.1-frozen@91f2fb1` ajan deneyinde kullanılmamıştır ve nihai skorlar hibrit ML guard sonucu olarak sunulmamalıdır.

## Deneysel v2.2 ablation katmanı

`backend/app/ml_guard.py`, eğitilmiş XLM-R dizinini çalışma zamanında yükleyen ve eylem riskini `SAFE` dahil yedi sınıftan birine eşleyen adaptördür. `benchmark/run_guard_ablation.py` aynı üretici ajan ve aynı OOD görevler üzerinde üç koruma stratejisini çalıştırır:

- `rule`: dondurulmuş deterministik Guarded v2.1;
- `ml`: yalnız öğrenilmiş risk kararı;
- `hybrid`: kural engelini korur, kural izin verdiğinde ML kararını uygular.

Bu kodun varlığı deney sonucunu ifade etmez. ML/Hybrid skorları ancak model ağırlığı, eğitim metadata'sı ve dört sistemin tam eşlenmiş ham koşuları yayımlandıktan sonra raporlanacaktır. v2.2 ablation, dondurulmuş v2.1 final skorunun yerine geçmez.

## Girdi ve çıktı

Girdi: Türkçe sentetik kullanıcı talebi, mevcut form durumu, izinli araç/hedef şeması ve yetki sözleşmesi.

Çıktı: uygulanmış eylem veya `ALLOW`, `BLOCK`, `BLOCK_AND_ASK`, `REQUIRE_CONFIRMATION` guard kararı; gerekçe, risk etiketi ve kanıt referansları.

## Dondurulmuş değerlendirme

- Algoritma: `guarded-v2.1-frozen@91f2fb1`
- Model revision: `cfbefacb99257ffa30c83adab238a50856ac3083`
- Final test: 40/40 görev başarısı, 0 gözlenen ihlal, 0 geçersiz eylem
- Wilson %95 başarı aralığı: %91,24–%100
- Unguarded karşılaştırması: 0/40 başarı, 10 ihlal, 25 geçersiz eylem
- Exact McNemar: `p=1,8189894×10⁻¹²`

Bu değerler yalnızca TR-PubBench'in dondurulmuş sentetik test split'i için geçerlidir.

## Amaç dışı kullanım

- Gerçek kamu işlemlerini kullanıcı adına yürütmek
- Hukuki uygunluk veya hak sahipliği kararı vermek
- Kimlik, dolandırıcılık veya güvenlik soruşturması yapmak
- İnsan onayı olmadan yüksek etkili ya da geri döndürülemez işlem yapmak
- Model çıktısını gerçek kişi verileriyle eğitmek veya değerlendirmek

## Bilinen sınırlılıklar

- Tek model, tek seed ve şablon ilişkili sentetik görevler kullanıldı.
- Guard önceden tanımlı yetki sözleşmesine ve yapılandırılmış forma ihtiyaç duyar.
- Gerçek DOM değişimleri, prompt injection ve dağılım dışı insan dili değerlendirilmedi.
- Başarı, gerçek hizmet kalitesi veya mevzuata uygunluk anlamına gelmez.
- Dış, insan yazımı bir değerlendirme olmadan yüzde yüz genelleme iddiası kurulamaz.

## Sürümleme

Test sonuçlarına bakıldıktan sonra v2.1 algoritması değiştirilmez. Her yöntem değişikliği yeni bir algoritma adı, Git etiketi ve yeniden ayrılmış değerlendirme kümesi gerektirir.
