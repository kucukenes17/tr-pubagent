# Third-party components

TR PubAgent depends on third-party packages and model providers but does not
vendor their model weights.

## Models used for research

| Identifier | Role | Included in this repository? |
| --- | --- | --- |
| `microsoft/Phi-4-mini-instruct` | Primary action-producing model | No |
| `Qwen/Qwen2.5-7B-Instruct` | Cross-model confirmation | No |
| `FacebookAI/xlm-roberta-base` | Base model for the experimental risk classifier | No |

Users who reproduce the experiments must review and accept the current license
and usage terms published with each upstream model. Repository metadata,
configuration and evaluation output do not grant rights to those weights.

## Software dependencies

Python and JavaScript dependencies are installed from their package registries
and retain their own licenses. Exact direct JavaScript versions are recorded in
`package.json` and `package-lock.json`; Python requirements are recorded under
`backend/requirements.txt` and the experiment notebooks. Generated production
bundles may contain dependency code subject to those licenses.

Product and project names are used descriptively. No affiliation or
endorsement is implied.
