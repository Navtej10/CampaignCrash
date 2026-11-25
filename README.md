# CampaignCrash

Crash-test your marketing campaign before you spend money on it.

CampaignCrash simulates how different audience personas (student, parent,
professional, price-sensitive buyer, first-time customer, existing customer)
read your ad + landing page, then clusters their reactions into named
confusion points, scores the campaign on a few dimensions with reasons
attached to each score, and proposes targeted fixes.

## Structure

```
campaigncrash/
  backend/     FastAPI service — persona simulation, clustering, scoring
  frontend/    React + Vite + TypeScript UI
```

## Quick start

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add ANTHROPIC_API_KEY, or leave blank to use mock mode
uvicorn app.main:app --reload --port 8000
```

Without an API key set, the engine runs in **mock mode**: it returns
realistic-looking canned personas and scores so you can build and demo the
frontend before wiring up a real model. Flip it on for real by setting
`ANTHROPIC_API_KEY` in `.env`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The dev server proxies `/api` to
`http://localhost:8000`.

## Design decisions baked into this scaffold

- **Scores always carry a reason.** `DimensionScore` in `models.py` requires
  a `reason` string pulled from persona reactions — there's no bare number
  anywhere in the schema. Don't add one.
- **Disagreement is a first-class field**, not something averaged away. See
  `DisagreementPoint` and the `DisagreementPanel` component.
- **Separate, modular pipeline stages:** `generate_personas` → `generate_reactions` →
  parallel (`cluster_confusion` + `identify_strengths`) → deterministic `compute_headline_metrics`
  + anchored `score_dimensions` (low temperature) → `suggest_fixes`.
- **Platform vs. Format separation:** `CampaignInput.platform` supplies uniform
  `PLATFORM_CONTEXT` to every persona rather than per-persona platform notes.
- **Apples-to-apples re-testing via `run_id` store:** Every run is assigned a
  `run_id` and stored in an in-memory TTL store (`_RUN_STORE` in `engine.py`)
  with its generated persona roster and results. `POST /api/crash-test/retest`
  re-runs evaluation on revised copy using the exact same persona set and
  computes before/after score, headline, and cluster deltas.
- **No live URL fetching.** Landing page content is pasted as text or uploaded
  as a screenshot. Don't add a scraper unless you have real spare time.

## Next build steps (not yet done)

- Wire real prompts in `backend/app/prompts.py` — the current ones are
  starting points, not tuned.
- Add streaming so persona reactions appear one at a time in the UI instead
  of waiting for the whole batch.
- Add a screenshot-upload path for the landing page instead of text-only.
