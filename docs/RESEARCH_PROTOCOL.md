# TR PubAgent araştırma protokolü v0.1

## Araştırma sorusu

Yetki sözleşmesi, deterministik güvenlik kuralları ve öğrenilmiş risk sınıflandırıcısından oluşan TR-PubGuard; korumasız Türkçe web ajanına göre yetkisiz ve geri döndürülemez hataları azaltırken görev başarısını koruyabilir mi?

## Önceden belirlenmiş hipotezler

- H1: Kritik ihlal oranında korumasız ajana göre en az %40 göreli azalma.
- H2: Görev başarısında en fazla 5 yüzde puanı kayıp.
- H3: Hibrit PubGuard, yalnız kural ve yalnız ML yöntemlerinden daha iyi güvenlik–başarı dengesi.

Bu dosya test kümesi çalıştırılmadan önce commit ile dondurulmalıdır. Test sonuçlarına bakıldıktan sonra yapılan her yöntem değişikliği yeni protokol sürümü gerektirir.

## Veri bölünmesi

- Development: 24 görev
- Validation: 16 görev
- Test: 40 görev
- Bölünme sırası `backend/app/tasks.py` içinde sabittir.
- Aynı risk/hizmet kalıbının basit yeniden yazımları farklı split’lere taşınmamalıdır.

## Sistemler

1. Scripted Oracle — altyapı üst sınırı, bilimsel baseline değildir.
2. Unguarded — Phi-4-mini-instruct + ReAct.
3. Rule Guard — yalnız deterministik güvenlik kuralları.
4. ML Guard — yalnız XLM-R risk sınıflandırıcısı.
5. TR-PubGuard — yetki sözleşmesi + kurallar + XLM-R.

## Ana deney

- 80 görev × 3 yapılandırma: Unguarded, Rule Guard, TR-PubGuard.
- Deterministik çıkarım; sıcaklık 0, seed 0, en fazla 20 adım.
- Sağlamlık: 24 tabakalı görev × 4 yapılandırma × 3 seed.
- Model, prompt, eşik, görev ve kod commit’i her koşuda kaydedilir.

## Metrikler

Birincil: görev başarısı, kritik güvenlik ihlali, yetkisiz eylem, onaysız geri döndürülemez işlem, açıklama isteme F1 ve durum koruma.

İkincil: adım sayısı, geçersiz araç çağrısı, gereksiz soru, süre, token, risk macro-F1 ve yetki sözleşmesi alan F1.

## İstatistik

- Oranlar için görev düzeyinde %95 bootstrap güven aralığı.
- Eşleştirilmiş başarı farkında McNemar testi.
- Seyrek kritik ihlal sayılarında Fisher exact testi.
- Çoklu karşılaştırmalarda Holm düzeltmesi.
- P-değeri yanında mutlak fark ve etki büyüklüğü raporlanır.

## Durdurma ve raporlama

- Altyapı hatası, kota kesintisi veya model çökmesi ayrı hata sınıfıdır; sessizce görevden çıkarılmaz.
- Maksimum 20 adım sonrası koşu başarısız sonlandırılır.
- Bütün test görevleri sonuç tablosunda yer alır.
- İnsan katılımcı kullanılmaz; görev geçerliliğindeki bu sınırlılık raporda belirtilir.
