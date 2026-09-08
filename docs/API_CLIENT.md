# Generated TypeScript API client

`lib/generated/tr-pubagent-api.ts` is generated from FastAPI's OpenAPI
document. It contains all component types, a typed operation map and a small
dependency-free `TrPubAgentApiClient`. The hosted research dashboard still
uses frozen static data; this client is the contract surface for a future
live/local integration and does not silently change the dashboard's data.

Regenerate and verify from repository root:

```powershell
python scripts/generate_api_client.py
python scripts/generate_api_client.py --check
npm run typecheck
```

The generated header records the canonical OpenAPI SHA-256. The backend test
regenerates the content in memory and requires exact equality, so model or
route changes cannot leave stale TypeScript unnoticed. CI performs the same
freshness check. The file is committed for reproducible consumers; edit the
FastAPI schema or generator, never the generated file by hand.

Example:

```ts
import { TrPubAgentApiClient } from '@/lib/generated/tr-pubagent-api'

const api = new TrPubAgentApiClient('http://127.0.0.1:8000')
const run = await api.call('create_run_v1_runs_post', {
  body: { task_id: 'BUR-001', agent: 'my-agent', seed: 0 },
})
```
