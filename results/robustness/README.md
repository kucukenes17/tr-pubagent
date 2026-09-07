# Human-authored OOD robustness v1

Bu klasör, `robustness-protocol-v1` etiketiyle algoritma dondurulduktan sonra Kaggle Tesla T4 üzerinde elde edilen sonuçları içerir.

- 24 insan yazımı OOD görev
- Seed: 0, 17, 42
- 72 Unguarded + 72 Guarded eşlenmiş koşu
- Phi-4-mini-instruct, NF4 4-bit
- Unguarded başarı: 6/72 (%8,3)
- Guarded v2.1 başarı: 66/72 (%91,7)
- Exact McNemar: `p=1.734723475976807e-18`

Guarded başarısızlıkları iki görevde ve üç seed'in tamamında kümelenir: `OOD-BLG-001` ve `OOD-RND-001`. Bunlar dondurulmuş sonucun parçası olarak korunur; sonraki düzeltmeler post-hoc v2.2 olarak raporlanmalıdır.

Rule/ML/Hybrid ablation aynı 72 koşu üzerinde tamamlandı. Üç guarded sistem de 66/72 başarı verdi; H3 desteklenmedi. ML ve Hybrid izleri ile kanonik özet bu klasörde saklanır.

`robustness_runs.db` yeniden üretilebilir çalışma veritabanıdır ve sürüm kontrolüne dahil edilmez.

## Guard v2.2 post-hoc sonucu

v2.1 hata analizi sonrasında, yalnız iki önceden belgelenmiş hata sınıfına yönelik v2.2 ayrı bir post-hoc protokolle değerlendirildi. Aynı 24 görev × 3 seed koşusunda başarı `66/72`den `72/72`ye çıktı; altı koşu yalnız v2.2 tarafından başarıldı ve regresyon görülmedi. Her iki sürümde de geçersiz eylem ve gözlenen ihlal sayısı sıfırdı. Exact McNemar `p=0,03125`; görev-kümeli bootstrap %95 fark aralığı, kazanımlar iki görevde kümelendiği için 0–20,83 yüzde puanıdır.

Ham iz `phi4_guarded_ood_v2_2.jsonl`, eşlenmiş özet `posthoc_v2_1_vs_v2_2_summary.json`, görev/seed tablosu `posthoc_v2_1_vs_v2_2_tasks.csv` ve ortam/provenance kaydı `posthoc_v2_2_metadata.json` dosyalarındadır. Ana v2.1 sonucu değiştirilmemiştir.
