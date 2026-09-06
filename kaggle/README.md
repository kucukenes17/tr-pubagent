# Kaggle deney akışı

`TR_PubAgent_Phi4_Experiments.ipynb`, dondurulmuş `Unguarded Agent v1` deneyini Kaggle GPU üzerinde tekrar üretir.

## Ayarlar

1. Kaggle'da yeni bir Notebook açın ve bu `.ipynb` dosyasını içe aktarın.
2. `Settings > Accelerator` altında GPU seçin.
3. `Settings > Internet` seçeneğini açın; GitHub ve Hugging Face indirmeleri bunu gerektirir.
4. Hücreleri sırayla çalıştırın veya temiz, yeniden üretilebilir koşu için `Save Version > Save & Run All` kullanın.

Notebook deney kodunu `80ef8edb8749993c654c379856725350c0b4b9cc` commit'ine sabitler. Çıktılar `/kaggle/working/tr-pubagent-results` altında, indirilebilir paket ise `/kaggle/working/tr-pubagent-kaggle-results.zip` yolunda üretilir.

Kaggle'ın resmi dokümantasyonuna göre `/kaggle/working` altında 20 GB'a kadar notebook çıktısı sürümle birlikte saklanabilir. İnteraktif oturum kesintilerine karşı önemli deneyler `Save & Run All` ile temiz bir sürüm olarak çalıştırılmalıdır.

## İnsan yazımı OOD sağlamlık koşusu

Ana sonuçlardan bağımsız 24 görev × 2 sistem × 3 seed koşusu:

```python
%cd /kaggle/working/tr-pubagent
!git pull --ff-only origin main
!python -m benchmark.check_task_leakage --output /kaggle/working/tr-pubagent-results/task_leakage_report.json --strict
!python -m benchmark.export_robustness_tasks --output /kaggle/working/tr-pubagent-results/robustness_tasks_v1.jsonl
!python -m benchmark.run_robustness \
  --seeds 0 17 42 \
  --systems unguarded guarded \
  --output-dir /kaggle/working/tr-pubagent-results/robustness
!python -m benchmark.analyze_robustness \
  --unguarded /kaggle/working/tr-pubagent-results/robustness/phi4_unguarded_ood_v1.jsonl \
  --guarded /kaggle/working/tr-pubagent-results/robustness/phi4_guarded_ood_v2_1.jsonl \
  --output /kaggle/working/tr-pubagent-results/robustness/robustness_summary.json \
  --csv /kaggle/working/tr-pubagent-results/robustness/robustness_task_comparison.csv
```

Kesilen oturumda aynı `run_robustness` hücresi yeniden çalıştırılabilir; bitmiş görev/seed çiftleri tekrar üretilmez.

Önce v2 çalışma zamanı formatıyla XLM-R modelini üretin:

```python
!python -m ml.generate_risk_dataset --output /kaggle/working/tr-pubagent-results/risk_dataset_v2.jsonl
!python -m ml.train_risk_classifier \
  --data /kaggle/working/tr-pubagent-results/risk_dataset_v2.jsonl \
  --output /kaggle/working/tr-pubagent-results/xlmr-risk-v2
```

XLM-R modeli hazır olduğunda H3 ablation:

```python
!python -m benchmark.run_guard_ablation \
  --systems ml hybrid \
  --seeds 0 17 42 \
  --ml-model-path /kaggle/working/tr-pubagent-results/xlmr-risk-v2 \
  --output-dir /kaggle/working/tr-pubagent-results/robustness
!python -m benchmark.analyze_ablation \
  --unguarded /kaggle/working/tr-pubagent-results/robustness/phi4_unguarded_ood_v1.jsonl \
  --rule /kaggle/working/tr-pubagent-results/robustness/phi4_guarded_ood_v2_1.jsonl \
  --ml /kaggle/working/tr-pubagent-results/robustness/phi4_ml_guard_ood_v2_2.jsonl \
  --hybrid /kaggle/working/tr-pubagent-results/robustness/phi4_hybrid_guard_ood_v2_2.jsonl \
  --output /kaggle/working/tr-pubagent-results/robustness/guard_ablation_summary.json
```
