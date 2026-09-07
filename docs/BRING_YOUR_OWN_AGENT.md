# Kendi ajanını getir (BYOA)

TR-PubAgent yalnızca depodaki Phi-4 ajanını ölçmez. `tr-pubagent.agent.v1` HTTP sözleşmesini uygulayan herhangi bir ajanı aynı görev ortamı ve deterministik değerlendirici üzerinde çalıştırabilir.

## Çalışma biçimi

```text
TR-PubBench gözlemi → yerel benchmark CLI → sizin POST /act endpoint'iniz
                    ← tek araç eylemi ←
                    → sentetik ortam → durum tabanlı değerlendirme → JSONL iz
```

Benchmark CLI geliştiricinin bilgisayarında çalışır. Ana TR-PubAgent sunucusu kullanıcı tarafından verilen URL'lere bağlanmaz; böylece sunucu tarafında SSRF yüzeyi oluşmaz. Varsayılan olarak yalnız `localhost`, `127.0.0.1` ve `::1` kabul edilir.

## 1. Ajan sözleşmesi

Ajanınız bir HTTP endpoint'i sunmalı ve `POST /act` isteğini kabul etmelidir.

İstek:

```json
{
  "protocol_version": "tr-pubagent.agent.v1",
  "run_id": "7bfe...",
  "task_id": "BUR-001",
  "observation": {
    "task": "Öğrenci bursu taslağını hazırla...",
    "state": {"fields": {}, "submitted": false},
    "form_fields": [],
    "candidate_actions": ["fill", "ask_user", "finish"],
    "action_targets": {"fill": ["income"], "finish": ["task"]},
    "step": 1,
    "max_steps": 20
  },
  "feedback": ""
}
```

Yanıt:

```json
{
  "protocol_version": "tr-pubagent.agent.v1",
  "action": {
    "tool": "ask_user",
    "target_id": "household_size",
    "arguments": {},
    "evidence_refs": ["user_request:missing_fact"],
    "reason": "Zorunlu bilgi kullanıcı talebinde yok."
  },
  "metadata": {"model": "my-model-v1"}
}
```

`action.tool` şu değerlerden biri olmalıdır:

`navigate`, `click`, `fill`, `select`, `upload_fixture`, `ask_user`, `request_confirmation`, `submit`, `finish`.

Her adımda kullanılabilen araçlar `candidate_actions`, geçerli hedefler ise `action_targets` içinde verilir. `metadata` isteğe bağlıdır ve model sürümü, token sayısı veya sağlayıcı gecikmesi gibi JSON-uyumlu tanı bilgileri için kullanılabilir.

## 2. Örnek ajanı çalıştırma

Depo kökünde:

```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r backend/requirements.txt
uvicorn examples.http_agent:app --port 9001
```

Yeni bir terminalde doğrudan ajan testi:

```bash
python -m benchmark.run_external_agent \
  --agent-url http://127.0.0.1:9001/act \
  --agent-name my-agent-v1 \
  --split development \
  --limit 20 \
  --guard none \
  --output outputs/my-agent-direct.jsonl
```

Aynı ajanı TR-PubGuard v2.1 kural korumasıyla ölçmek için:

```bash
python -m benchmark.run_external_agent \
  --agent-url http://127.0.0.1:9001/act \
  --agent-name my-agent-v1 \
  --split development \
  --limit 20 \
  --guard rule \
  --output outputs/my-agent-guarded.jsonl
```

Belirli görevler `--task-ids BUR-001 BUR-002` ile seçilebilir. Var olan JSONL koşuları aynı ajan, endpoint, seed ve guard modu için otomatik atlanır; yeniden çalıştırmak için `--overwrite` kullanılır.

## 3. Uzak ve kimlik doğrulamalı ajan

Uzak endpoint'e gönderilen gözlemler sentetik olsa da görev metnini ve ajan izini içerir. Bilinçli olarak uzak servis kullanıyorsanız:

```bash
set TR_PUBAGENT_AGENT_TOKEN=your-token
python -m benchmark.run_external_agent \
  --agent-url https://agent.example/act \
  --allow-remote \
  --agent-name hosted-agent-v1
```

Token komut satırı argümanı değildir; süreç listesine ve shell geçmişine yazılmaması için yalnız `TR_PUBAGENT_AGENT_TOKEN` ortam değişkeninden okunur. Sonuç dosyasına URL sorgu parametreleri ve token kaydedilmez.

## 4. Çıktı ve yorumlama

Her JSONL satırı bir görev koşusudur ve şunları içerir:

- `task_success`, `safety_score`, `violations`
- `termination`, `invalid_action`, `semantic_errors`
- `steps`, `latency_seconds`
- `guard_blocks`, `guard_enforcements`
- gözlem, önerilen eylem, uygulanan eylem ve ortam sonucunu içeren `trace`

Adil bir karşılaştırma için aynı split, görev sırası ve seed ile önce `--guard none`, sonra `--guard rule` çalıştırılmalıdır. Test split'i nihai rapora kadar kapalı tutulmalı; geliştirme sırasında `development`, model seçimi sırasında `validation` kullanılmalıdır.

## Güvenlik sınırları

- Ortam sentetiktir; gerçek kamu portalı veya gerçek kişi verisi kullanılmaz.
- URL içinde kullanıcı adı/parola reddedilir.
- Uzak endpoint'ler `--allow-remote` olmadan reddedilir.
- Yanıtlar yürütülmeden önce Pydantic ile kesin eylem şemasına göre doğrulanır.
- `--guard rule`, ajanın önerisini değiştirebilir; bu sonuç çıplak ajan sonucu olarak raporlanmamalıdır.
- Endpoint kodu benchmark sürecinden ayrı çalışır. Güvenilmeyen ajan kodu için ayrıca container/sandbox kullanılması önerilir.
