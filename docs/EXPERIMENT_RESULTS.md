# İlk deney sonuçları

Bu belge, TR-PubAgent'ın 5 Eylül 2026 tarihinde Google Colab T4 GPU üzerinde yürütülen ilk uçtan uca deneyinin yeniden üretilebilir özetidir. Sonuçlar bir fizibilite kanıtıdır; gerçek kamu hizmetlerinde güvenilirlik veya yüzde yüz güvenlik iddiası değildir.

## Deneyde ne yapıldı?

1. Türkçe dijital kamu hizmetlerini taklit eden 80 sentetik görev üretildi.
2. Yetki, gizlilik, eksik bilgi, geri döndürülemez işlem ve durum bütünlüğü risklerini kapsayan 3.000 sentetik eylem örneği oluşturuldu.
3. Görevlerin 24 tanesi, değerlendirme hattının doğru çalıştığını sınamak için kuralları bilen `scripted-oracle` ajanıyla oynatıldı.
4. `xlm-roberta-base`, yedi risk sınıfını tahmin etmek üzere eğitildi.
5. Model; eğitim, doğrulama ve test grupları birbirine karışmayacak biçimde ayrılan veri üzerinde değerlendirildi.

## Veri ve çalışma özeti

| Bileşen | Sonuç |
| --- | ---: |
| Benchmark görevleri | 80 |
| Sentetik risk örnekleri | 3.000 |
| Eğitim örnekleri | 2.113 |
| Doğrulama örnekleri | 489 |
| Test örnekleri | 398 |
| Risk sınıfları | 7 |
| Oracle ile oynatılan görevler | 24 |
| Oracle görev başarısı | 24/24 |
| Donanım | Google Colab NVIDIA T4 |
| Eğitim süresi | 333,9 saniye |
| Tamamlanan epoch | 3 |
| Eğitim kaybı | 0,2202 |
| Test macro-F1 | 1,000 |

Test kümesindeki yedi sınıfın tamamında precision, recall ve F1 değeri 1,000 ölçüldü. Sınıf destekleri: `SAFE` 105, `PRIVACY_VIOLATION` 75, `MISSING_INFORMATION` 59, `IRREVERSIBLE_CONFIRMATION_REQUIRED` 45, `STATE_CORRUPTION_RISK` 40, `UNAUTHORIZED` 39 ve `LANGUAGE_INTERPRETATION_ERROR` 35 örnektir.

## Sonuç nasıl yorumlanmalı?

`scripted-oracle` gerçek bir yapay zekâ ajanı değildir. Beklenen doğru davranışı baştan bilen bir kontrol ajanıdır. Dolayısıyla 24/24 sonucu, benchmark ve değerlendirme yazılımının uçtan uca çalıştığını gösterir; bağımsız bir ajanın bütün görevleri çözdüğünü göstermez.

Benzer biçimde 1,000 macro-F1, modelin mevcut sentetik şablonları ayırabildiğini gösterir. Bu veri görece temiz ve sınıflar belirgin olduğu için sonuç gerçek kullanıcı dili, örtük yetki ifadeleri veya saldırgan girdiler üzerinde aynı performansı garanti etmez. CV ve sunumlarda metrik mutlaka “ayrı tutulan sentetik test kümesi” ifadesiyle birlikte verilmelidir.

## Üretilen çıktılar

Yerel `outputs/tr-pubagent-results.zip` arşivi şunları içerir:

- eğitilmiş XLM-R model ağırlıkları ve tokenizer;
- ayrıntılı `test_report.json` sınıflandırma raporu;
- 80 görevlik `tr_pubbench_tasks.jsonl`;
- 3.000 örnekli `risk_dataset.jsonl`;
- oracle koşu sonuçları ve SQLite olay günlüğü.

Arşiv büyük model ağırlıkları içerdiği için Git'e eklenmez. Model kartıyla birlikte Hugging Face Hub gibi model depolamaya uygun bir serviste ayrıca yayımlanabilir.

## Bilimsel olarak sıradaki deneyler

- En az iki gerçek ajanı aynı 80 görevde, aynı bütçe ve araçlarla karşılaştırmak.
- Şablon dışı insan paraphrase'leri, zor negatifler ve örtük yetki örnekleri eklemek.
- En az üç farklı rastgele tohumla eğitim yapıp ortalama ve standart sapma raporlamak.
- İnsan etiketli küçük bir dış test kümesi oluşturarak sentetikten gerçeğe genellemeyi ölçmek.
- Eğitilen sınıflandırıcıyı TR-PubGuard çalışma zamanına bağlayıp kural tabanlı, ML tabanlı ve hibrit korumayı karşılaştırmak.

## CV için doğrulanabilir ifade

> Developed TR-PubAgent, an open-source Turkish benchmark for evaluating task success and authorization-aware safety of web agents; built an 80-task FastAPI/SQLite evaluation pipeline and fine-tuned XLM-RoBERTa on 3,000 synthetic risk actions across seven classes, achieving 1.00 macro-F1 on a held-out synthetic test set (398 samples).

Bu ifade projenin mevcut durumunu doğru yansıtır. Gerçek ajan karşılaştırmaları tamamlanıncaya kadar “ajanlarda yüzde yüz başarı” veya “gerçek dünyada yüzde yüz güvenlik” denmemelidir.
