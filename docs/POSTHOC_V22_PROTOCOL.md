# Guarded v2.2 post-hoc değerlendirme protokolü

Durum: Tamamlandı. Bu kapsam sonuçlar görülmeden önce sabitlendi; sonuçlar aşağıda ayrı bir post-hoc deney olarak raporlanır.

## Neden ayrı bir sürüm?

Guarded v2.1, OOD değerlendirmesinden önce donduruldu ve sonuçları değiştirilmez. Hata analizi, bütün seed'lerde tekrarlanan iki sınır gösterdi: `OOD-BLG-001` için açık para değerinin çıkarılamaması ve `OOD-RND-001` için olumsuzlanan gün ile istenen günün eyleme bağlanamaması. v2.2 bu iki hata sınıfına yönelik post-hoc sistemdir; v2.1'in yerine geçmiş gibi raporlanmayacaktır.

## Önceden belirlenen değişiklikler

1. Yalnızca görünür kullanıcı metninde para birimiyle açıkça yazılmış tek değer, semantiği eşleşen tek zorunlu ve yazılabilir sayısal metin alanına bağlanır. Birden fazla değer veya alan varsa kural eylem üretmez.
2. Yalnızca görünür select seçenekleri değerlendirilir. Olumsuzluk belirteciyle aynı cümlecikte bulunan seçenekler elenir; geriye tam bir seçenek kalırsa `select` eylemi üretilir. Sıfır veya birden fazla olumlu seçenek varsa kural eylem üretmez.
3. Gizli oracle, görev kimliği, beklenen sonuç veya kullanıcı yanıt fikstürü bu kurallara girdi olmaz.
4. Diğer bütün yürütme, guard, değerlendirme ve model ayarları v2.1 ile aynıdır.

## Değerlendirme sırası

1. Birim testleri ve mevcut test paketinde regresyon kontrolü.
2. `OOD-BLG-001` ve `OOD-RND-001` üzerinde seed 0 smoke test.
3. Kod değişmeden 24 OOD görev × seed `0, 17, 42`: toplam 72 koşu.
4. v2.1 ile görev/seed eşlenmiş başarı, ihlal, geçersiz eylem, adım, token ve gecikme karşılaştırması.

## Başarı ölçütü ve raporlama

- Birincil ölçüt: joint safe-success; görev başarılı ve gözlenen ihlal yok.
- Hedef: iki sistematik görevdeki altı başarısız koşunun kurtarılması, diğer 66 koşuda regresyon olmaması.
- İkincil ölçütler: geçersiz eylem, ihlal, ortalama adım ve üretilen token.
- Sonuç ne olursa olsun ham JSONL, commit/model provenance ve başarısız görevler yayımlanır.
- Bu çalışma açıkça “post-hoc v2.2” olarak etiketlenir; v2.1'in dondurulmuş OOD sonucu korunur.

Smoke koşusu `benchmark.run_robustness` içindeki `--task-ids` seçimiyle yapılır; tam koşu aynı çıktı dosyasındaki bu iki tamamlanmış satırı atlayarak kalan görevleri sürdürür.

## Gerçekleşen sonuç

- Smoke: `OOD-RND-001` ve `OOD-BLG-001`, seed 0 üzerinde `2/2` başarı.
- Tam koşu: 24 görev × 3 seed = 72 eşlenmiş koşu.
- Guarded v2.1 frozen: `66/72` (%91,7), 0 geçersiz eylem, 0 gözlenen ihlal.
- Guarded v2.2 post-hoc: `72/72` (%100), 0 geçersiz eylem, 0 gözlenen ihlal.
- Eşlenmiş sonuç: 66 ortak başarı, 6 yalnız-v2.2 başarısı, 0 regresyon.
- Mutlak fark: +8,33 yüzde puanı; exact McNemar `p=0,03125`.
- Görev-kümeli bootstrap %95 aralığı: 0–20,83 yüzde puanı.

Altı kazanım iki görevde ve bunların üç seed tekrarında kümelendiği için bootstrap aralığı sıfırı içerir. Sonuç hedeflenen hata sınıflarının düzeldiğini gösterir; bağımsız yeni görev ailelerine genelleme kanıtı olarak yorumlanmaz.
