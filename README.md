# Taku — AI export sales team for a Japanese craftsman

An agent swarm that takes a product photo and a craftsman's note, then produces
export-ready merchandising: structured product analysis, an English listing with
a grounded provenance story, JA/FR/DE translations, back-translation
verification, and export feasibility computed by generated code running in a
Daytona sandbox.

Pipeline (see `orchestrator.py`):

1. **Intake** — Qwen-VL reads the product photo into structured JSON
2. **Merchandising** — GMI writes listing, grounded heritage story, translations
3. **Verification** — ai& back-translates the Japanese and checks meaning + tone
4. **Export Intelligence** — generates Python rules code and executes it in a
   Daytona sandbox (HS code, duty estimate, carry-vs-ship, courier)

## Setup

Requires **Python 3.9+**.

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in the six sponsor API keys
(Qwen, GMI, ai&, Daytona — plus base URLs/models). On Python 3.9 the
`daytona` + `eval_type_backport` pins in requirements.txt are both required.

Verify the LLM providers are reachable:

```bash
python orchestrator.py --warmup
```

Run the swarm:

```bash
python orchestrator.py
```
