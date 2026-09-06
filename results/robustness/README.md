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

`robustness_runs.db` yeniden üretilebilir çalışma veritabanıdır ve sürüm kontrolüne dahil edilmez.
