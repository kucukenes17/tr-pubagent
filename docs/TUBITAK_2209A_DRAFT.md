# TÜBİTAK 2209-A proje önerisi taslağı

## Proje başlığı

Türkçe Kamu Hizmeti Benzeri Web Ajanlarında Yetki, Gizlilik ve Geri Döndürülemez Eylem Güvenliğinin Ölçülmesi: TR PubAgent

## Özet

Üretken yapay zekâ tabanlı web ajanları, kullanıcı adına çok adımlı dijital işlemler gerçekleştirebilmektedir. Ancak yalnız görev başarısına odaklanan değerlendirmeler; kullanıcının vermediği bilgiyi üretme, özel veriyi forma aktarma, olumsuz Türkçe talimatı yanlış yorumlama veya açık onay olmadan geri döndürülemez işlem yapma gibi hataları görünmez bırakabilmektedir. Bu projede Türkçe kamu hizmeti benzeri fakat gerçek kurum ve kişisel veri içermeyen sentetik bir değerlendirme ortamı geliştirilecektir. TR-PubBench görevleri yetki sözleşmesi, görünür portal durumu ve gizli oracle koşullarıyla tanımlanacak; korumasız ajan, deterministik Rule Guard, öğrenilmiş XLM-R ML Guard ve Hybrid Guard aynı koşullarda karşılaştırılacaktır. Görev başarısı, kritik ihlal, geçersiz eylem, durum koruma, adım ve token maliyeti birlikte ölçülecektir. Ana sentetik deney tamamlanmış olup genişletme çalışması insan yazımı dağılım dışı görevler ve çok-seed ablation üzerine kuruludur. Beklenen çıktı; açık kaynak benchmark, tekrar üretilebilir deney kayıtları, güvenlik katmanı ve Türkçe ajan güvenliği için ölçüm protokolüdür.

Anahtar kelimeler: yapay zekâ ajanları, web ajanı, güvenli yapay zekâ, Türkçe NLP, yetki kontrolü, benchmark

## Problem ve özgün değer

Web ajanı çalışmalarında “görev tamamlandı mı?” sorusu yaygın birincil ölçüttür. Oysa yüksek etkili formlarda doğru sonuca yanlış veya yetkisiz bir karar zinciriyle ulaşmak kabul edilebilir değildir. Türkçe eklemeli yapı, olumsuzluk, dolaylı onay ve bağlama bağlı özel veri kısıtları bu problemi daha belirgin hâle getirir. Projenin özgün değeri:

1. Türkçe talimatlarda başarı ve güvenliği aynı görev üzerinde birlikte ölçmesi,
2. görünür ajan bilgisi ile gizli değerlendirici koşullarını ayırması,
3. yetki sözleşmesini makinece denetlenebilir hâle getirmesi,
4. ham karar izlerini ve post-hoc bulunan olumsuz bulguları saklaması,
5. Rule-only, ML-only ve Hybrid yöntemleri eşlenmiş görevlerde karşılaştırmasıdır.

## Araştırma soruları ve hipotezler

- AS1: Guard katmanı kritik ihlal oranını korumasız ajana göre azaltır mı?
- AS2: Bu azalma görev başarısında kabul edilemez bir kayıp yaratır mı?
- AS3: Hybrid Guard, Rule-only ve ML-only yöntemlerinden daha yüksek ortak güvenli-başarı oranı sağlar mı?

H1: Kritik ihlal oranında en az %40 göreli azalma.  
H2: Görev başarısında en fazla 5 yüzde puanı kayıp.  
H3: Hybrid Guard'ın aynı koşuda başarı ve sıfır ihlal oranı, Rule ve ML oranlarından ayrı ayrı yüksektir.

## Yöntem

### Veri ve ortam

Ana veri 80 programatik sentetik görevden oluşur. Geliştirme/doğrulama/test ayrımı 24/16/40 olarak dondurulmuştur. Genelleme için ana cümle kalıplarından bağımsız yazılmış 24 OOD görev kullanılacaktır. Altı hizmet ailesi burs, ders kaydı, hastane randevusu, belediye talebi, sosyal yardım ve belge gönderimidir. Hiçbir gerçek vatandaş verisi kullanılmaz.

### Sistemler

- Unguarded: Phi-4-mini-instruct ve yapılandırılmış araç çağırma.
- Rule Guard: yetki, eksik bilgi, gizlilik, onay ve durum kuralları.
- ML Guard: yedi sınıflı XLM-R eylem-risk sınıflandırıcısı.
- Hybrid Guard: Rule ve ML kararlarının güvenli bileşimi.

### Deney tasarımı

OOD deneyinde 24 görev, dört sistem ve üç seed ile 288 koşu planlanmıştır. Model çıkarımı deterministiktir; seed tekrarları bağımsız örnek gibi değil görev içi tekrar olarak ele alınacaktır. OOD sonucu görülmeden protokol, eşik ve görevler dondurulur. Kota veya altyapı kesintileri veri satırı silinmeden ayrıca kaydedilir.

### Değerlendirme

Görev başarısı ve ihlal oranları için Wilson aralığı; eşlenmiş başarı için exact McNemar; seyrek ihlal karşılaştırmaları için Fisher exact; çoklu testlerde Holm düzeltmesi uygulanacaktır. Başarı farkı görev düzeyinde cluster bootstrap ile raporlanacaktır. P değeri yanında mutlak fark ve ham sayılar verilecektir.

## İş-zaman planı

| Ay | Faaliyet | Çıktı |
| --- | --- | --- |
| 1 | OOD görev uzman kontrolü, sızıntı denetimi | Dondurulmuş 24 görev ve ön kayıt |
| 2 | XLM-R v2 eğitimi, eşik sabitleme | Model, metadata, test raporu |
| 3 | 288 GPU koşusu | Ham JSONL ve ortam bilgisi |
| 4 | İstatistik, hata taksonomisi | Ablation tablosu ve grafikler |
| 5 | Portal/replay iyileştirmesi, Docker doğrulama | Tek komut kurulum ve canlı demo |
| 6 | Rapor, video ve açık veri paketi | Makale biçimli rapor ve v1.0.0 |

## Riskler ve önlemler

| Risk | Etki | Önlem |
| --- | --- | --- |
| GPU kotası kesintisi | Koşuların yarıda kalması | Task/seed bazlı devam mekanizması ve Kaggle çıktı arşivi |
| Şablon ezberleme | Yanıltıcı yüksek başarı | İnsan yazımı OOD kümesi ve benzerlik denetimi |
| ML veri alanı kayması | ML Guard başarısının düşmesi | Eğitim ve runtime için ortak JSON özellik şeması |
| Yanlış genelleme | Bilimsel iddianın aşılması | Sentetik/tek-model sınırlılığını her tabloda belirtme |
| Gerçek veri sızıntısı | Etik ve güvenlik riski | Yalnız sentetik fixture, ağ allowlist'i ve veri kartı |

## Beklenen sonuç ve yaygın etki

Beklenen çıktı yalnız yüksek başarı skoru değildir. Hangi hata sınıflarında hangi korumanın işe yaradığı, güvenlik katmanının görev maliyeti ve başarısız örneklerin tekrar üretilebilir izleri yayımlanacaktır. Platform; Türkçe NLP, güvenli ajan tasarımı ve insan denetimli otomasyon üzerine öğrenci projeleri için yeniden kullanılabilir bir başlangıç sunacaktır.

## Mevcut ön sonuç

Dondurulmuş 40 sentetik test görevinde Unguarded 0/40, Guarded v2.1 40/40 başarı göstermiş; gözlenen ihlal 10'dan 0'a inmiştir. Exact McNemar `p=1,82×10⁻¹²` bulunmuştur. Bu güçlü fakat tek model ve şablon ilişkili sonuç, OOD deneyinin gerekçesidir; gerçek dünya performansı olarak sunulmaz.

## Etik, açık bilim ve veri yönetimi

İnsan katılımcı ve gerçek kişisel veri yoktur. Gerçek kamu sistemlerine işlem gönderilmez. Kod, görev tanımları, model metadata'sı, bağımlılık sürümleri, ham izler, özetler ve checksum manifesti sürümlü olarak saklanır. Dondurulmuş sonuçlar sonradan değiştirilmez; bulunan tekrar ve protokol sapmaları açıkça raporlanır. Veri lisansı nihai yayımdan önce kaynak ve türev hakları bakımından ayrıca denetlenecektir.

## Başvuru öncesi doldurulacak alanlar

- Yürütücü öğrenci, danışman ve kurum bilgileri
- TÜBİTAK çağrı dönemine göre bütçe kalemleri ve gerekçeleri
- Güncel kaynakça ve ilgili çalışma karşılaştırma tablosu
- Danışman onaylı etik kurul gereklilik beyanı
- Proje başlangıç/bitiş tarihleri
