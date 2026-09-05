# TR-PubGuard model kartı

## Sistem

TR-PubGuard tek bir üretici model değildir. Üç katmanlı karar sistemidir:

1. Kullanıcı talebinden yapılandırılmış yetki sözleşmesi.
2. Eksik bilgi, açık yasak ve onay kapıları için deterministik kurallar.
3. XLM-RoBERTa-base ile çok sınıflı eylem risk tahmini.

## Girdi ve çıktı

Girdi: Türkçe kullanıcı talebi, mevcut form durumu, planlanan eylem ve bilinen gerçekler.

Çıktı: `ALLOW`, `BLOCK`, `BLOCK_AND_ASK` veya `REQUIRE_CONFIRMATION`; risk etiketi, güven ve kanıt.

## Amaç dışı kullanım

- Gerçek kamu işlemlerini kullanıcı adına yürütmek
- Hukuki uygunluk kararı vermek
- Kimlik veya dolandırıcılık tespiti yapmak
- İnsan onayı olmadan yüksek etkili karar almak

## Eşik

Kritik eylemlerde model güveni 0,65 altındaysa eylem uygulanmaz ve açıklama istenir. Kural tabanlı kritik yasaklar ML skoruyla geçersiz kılınamaz.

## Değerlendirme durumu

Bu depo eğitim ve değerlendirme kodunu içerir; yayımlanmış gerçek model ağırlığı veya bilimsel skor henüz içermez. Arayüzdeki örnek skorlar demo verisidir.
