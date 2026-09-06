# TR PubAgent

TR PubAgent, Türkçe kamu hizmeti benzeri çok adımlı web görevlerinde yapay zekâ ajanlarını yalnızca görev başarısı ile değil; yetki, eksik bilgi, gizlilik, geri döndürülemez işlem ve durum koruma açısından değerlendiren açık araştırma platformudur.

> Bu depo gerçek bir kamu hizmeti değildir. Gerçek kurumlara bağlanmaz, gerçek kişi verisi kullanmaz ve arayüzdeki tüm kimlikler sentetiktir.

## Neler var?

- **TR-PubBench:** Altı hizmet ailesinden programatik ve deterministik olarak üretilen 80 Türkçe görev.
- **Sentetik portal:** Burs başvurusu üzerinde çalışan, erişilebilir ve etkileşimli ilk hizmet yüzeyi.
- **TR-PubGuard v2.1:** Yetki sözleşmesi, kanıt bağlama, sabit güvenlik kuralları ve güvenli yürütme kontrolcüsü.
- **Deterministik değerlendirici:** Son ekran görüntüsü yerine veri tabanı durumunu puanlar.
- **Koşu tekrarı:** Gözlem → eylem → guard kararını adım adım gösteren araştırma paneli.
- **OOD sağlamlık paketi:** Ana şablonlardan bağımsız yazılmış 24 görev, sızıntı denetimi ve üç-seed GPU koşucusu.
- **ML paketi:** 3.000 sentetik eylem-risk örneği ve XLM-R eğitim betiği.
- **Sıfır maliyet akışı:** Scripted kontrol ile yerel geliştirme; Phi-4/XLM-R için Kaggle veya Colab.

## Dondurulmuş Phi-4 sonucu

| Sistem | 40 görevlik sentetik test başarısı | Geçersiz eylem | Gözlenen ihlal | Ort. adım |
| --- | ---: | ---: | ---: | ---: |
| Unguarded v1 | 0/40 (%0) | 25 | 10 | 9,20 |
| TR-PubGuard v2.1 | 40/40 (%100) | 0 | 0 | 2,20 |

Guarded v2.1 validation görülmeden önce `guarded-v2.1-frozen@91f2fb1` olarak donduruldu. Testteki eşleştirilmiş başarı farkı için exact McNemar `p=1,82×10⁻¹²`; Guarded başarı oranının Wilson %95 güven aralığı `%91,24–%100` ölçüldü. Üretilen token sayısı Unguarded'a göre `%92,7` azaldı.

Bu sonuç yalnızca programatik ve şablon ilişkili TR-PubBench sentetik test split'i için geçerlidir; gerçek kamu portallarında yüzde yüz başarı iddiası değildir. Ayrıntılar, protokol sapmaları ve sınırlılıklar [docs/EXPERIMENT_RESULTS.md](docs/EXPERIMENT_RESULTS.md) içindedir.

## Hızlı başlangıç

### Yalnız web arayüzü

Gereksinimler: Node.js 22+

```bash
npm install
npm run dev
```

Arayüz `http://localhost:3000` adresinde açılır.

### API

Gereksinimler: Python 3.12+

```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

API dokümantasyonu `http://localhost:8000/docs` adresindedir.

### Docker

```bash
docker compose up --build
```

Bu komut web arayüzünü `:3000`, API’yi `:8000` portunda başlatır. Docker Desktop bu bilgisayarda başlangıçta kurulu olmadığı için ilk yerel Docker denemesinde ayrıca kurulmalıdır.

## Depo yapısı

```text
app/                  Vinext/Next App Router sayfaları
components/           Portal, panel ve koşu tekrar bileşenleri
backend/app/           FastAPI, SQLite, PubGuard ve değerlendirici
backend/tests/         API, görev ve güvenlik birim testleri
benchmark/             Açık JSON görev şeması
ml/                    Risk veri üretimi ve XLM-R eğitimi
colab/                 Ücretsiz GPU deney defteri
kaggle/                Phi-4 için Kaggle GPU deney defteri
docs/                  Araştırma protokolü, veri ve model kartları
```

## Ana API örneği

```bash
curl -X POST http://localhost:8000/v1/guard/check \
  -H "Content-Type: application/json" \
  -d '{
    "user_request":"Başvuruyu hazırla ve göndermeden önce sor.",
    "action":{"tool":"submit","target_id":"submit","arguments":{}},
    "contract":{"goal":"burs","permitted_actions":["submit"],"prohibited_actions":[],"required_facts":[],"confirmation_gates":["submit"],"privacy_constraints":[]},
    "known_facts":{},
    "confirmed_actions":[]
  }'
```

Beklenen karar: `REQUIRE_CONFIRMATION`.

## Test ve doğrulama

```bash
npm run typecheck
npm run lint
npm run build

cd backend
pytest --cov=app --cov-report=term-missing

cd ..
python benchmark/generate_frozen_report.py
```

Temel deney protokolü ve gerçekleşen sapmalar [docs/RESEARCH_PROTOCOL.md](docs/RESEARCH_PROTOCOL.md), dondurulmuş sonuçlar [docs/EXPERIMENT_RESULTS.md](docs/EXPERIMENT_RESULTS.md), ham izler ve kanonik özet [results/frozen](results/frozen), CV ve mülakat anlatımı ise [docs/PORTFOLIO.md](docs/PORTFOLIO.md) içindedir.

İnsan yazımı genelleme deneyi [docs/ROBUSTNESS_PROTOCOL.md](docs/ROBUSTNESS_PROTOCOL.md) içinde ön kayıtlıdır. 12 haftalık planın güncel kontrol tablosu [docs/PLAN_STATUS.md](docs/PLAN_STATUS.md) içindedir.

## Araştırma etiği

- Gerçek e-Devlet veya hastane hesabı kullanılmaz.
- Gerçek vatandaş verisi, kimlik numarası veya belge saklanmaz.
- Ajanın ağ erişimi yalnızca yerel test alan adlarıyla sınırlandırılır.
- İnsan katılımcı çalışması bu sürümün kapsamı dışındadır.
- Negatif sonuçlar ve başarısız görevler seçilmeden raporlanır.

## Lisans

Kod Apache-2.0; görevler, sentetik veri ve yayımlanmış koşu kayıtları CC BY 4.0 altında planlanmıştır. Temel modeller kendi lisanslarını korur.
