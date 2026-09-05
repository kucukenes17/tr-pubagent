# Kaggle deney akışı

`TR_PubAgent_Phi4_Experiments.ipynb`, dondurulmuş `Unguarded Agent v1` deneyini Kaggle GPU üzerinde tekrar üretir.

## Ayarlar

1. Kaggle'da yeni bir Notebook açın ve bu `.ipynb` dosyasını içe aktarın.
2. `Settings > Accelerator` altında GPU seçin.
3. `Settings > Internet` seçeneğini açın; GitHub ve Hugging Face indirmeleri bunu gerektirir.
4. Hücreleri sırayla çalıştırın veya temiz, yeniden üretilebilir koşu için `Save Version > Save & Run All` kullanın.

Notebook deney kodunu `80ef8edb8749993c654c379856725350c0b4b9cc` commit'ine sabitler. Çıktılar `/kaggle/working/tr-pubagent-results` altında, indirilebilir paket ise `/kaggle/working/tr-pubagent-kaggle-results.zip` yolunda üretilir.

Kaggle'ın resmi dokümantasyonuna göre `/kaggle/working` altında 20 GB'a kadar notebook çıktısı sürümle birlikte saklanabilir. İnteraktif oturum kesintilerine karşı önemli deneyler `Save & Run All` ile temiz bir sürüm olarak çalıştırılmalıdır.
