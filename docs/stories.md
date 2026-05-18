# Sprint Plan — Hyrox Coach Agent

5 days, solo, ~6h focused work per day = ~30h budget. Tasks below total ~28h, leaving 2h buffer for unblockers.

## Conventions

- **ID**: `S<day>-<area><number>` (e.g. `S2-R1` = Day 2, RAG, task 1)
- **Estimate**: in hours (1h = "one hour of focused work")
- **Deps**: prerequisite task IDs
- **DoD** (Definition of Done): explicit criteria; the task isn't done until all are checked
- **Status**: 🔲 not started / 🟡 in progress / ✅ done / 🚫 blocked

---

## Day 1 — Foundation (Mon)
**Goal:** all credentials configured, Airtable schema live, repo scaffold pushed, first n8n workflow stub running.

### S1-F1 — Repo + scaffolding (1h)
- [ ] Create GitHub repo `hyrox-coach-agent`, push the scaffold from this template
- [ ] Set up `.env.example` with all keys needed
- [ ] Create `requirements.txt` (anthropic, pinecone-client, cohere, streamlit, python-dotenv, pyairtable)
- **DoD:** repo is public, README renders correctly on GitHub, `.env` is gitignored

### S1-A1 — Airtable base creation (1h) — deps: none
- [ ] Create base "Hyrox Coach" from `docs/airtable-schema.md`
- [ ] Seed `athlete_profile` with 1 row (yourself, target_date = mid-August 2026)
- [ ] Create Airtable Personal Access Token scoped to this base only (`data.records:read`, `data.records:write`, `schema.bases:read`)
- **DoD:** all 7 tables exist, profile row visible, PAT saved in password manager

### S1-C1 — Credentials in n8n (1.5h) — deps: S1-A1
- [ ] Configure OpenAI API credential in n8n (using the bootcamp key OR your personal key — see `.env.example` for the rationale)
- [ ] Configure Airtable PAT credential
- [ ] Configure Telegram bot credential (reuse the Lead Capture bot or create a new one)
- [ ] Configure Google Calendar OAuth (this is the one that takes time — Google Cloud project + OAuth consent)
- [ ] Configure Strava API credential (create app at developers.strava.com, generate a personal refresh token via the OAuth dance, save refresh token in n8n)
- [ ] Configure Pinecone + Cohere credentials
- **DoD:** "Test connection" returns ✓ for all seven credentials

### S1-W1 — Workflow A stub — Daily Briefing skeleton (1h) — deps: S1-C1
- [ ] Schedule Trigger (test value: every 5 minutes for now; will change to 7 AM before activation)
- [ ] Airtable node: read athlete_profile
- [ ] Airtable node: read training_plan for today
- [ ] Set node: package context
- [ ] Telegram Send: post a hardcoded "Daily brief test" message
- **DoD:** triggering manually posts a Telegram message that contains the athlete name from Airtable

### S1-P1 — Stories file + Day 2 plan (0.5h)
- [ ] Commit `docs/stories.md` (this file) to repo
- [ ] Verify Day 2 dependencies are unblocked
- **DoD:** stories.md visible on GitHub, no S2 task is blocked by an undone S1 task

**Day 1 total: 5h**

---

## Day 2 — Knowledge base + Workflow A complete (Tue)
**Goal:** RAG pipeline works; Workflow A generates a real (LLM-produced, RAG-grounded) brief end-to-end.

### S2-R1 — Knowledge base curation (1h)
- [ ] Download/extract the 5 sources into `knowledge-base/`:
  - Hyrox Training Guide (hyrox.com)
  - Joe Friel — periodization principles (extracts)
  - ISSN Position Stand: Nutrient Timing (paper)
  - Asker Jeukendrup — Sport Nutrition (web articles)
  - 1-2 community articles on first-time Hyrox prep
- [ ] Convert PDFs to markdown where possible (better chunking)
- **DoD:** `knowledge-base/` contains 5 documents totaling ≥30 pages, no copyright violations (extracts only, with sources cited)

### S2-R2 — RAG ingestion script (2h) — deps: S2-R1, S1-C1
- [ ] Write `rag-ingestion/ingest.py`: chunk (500 tokens, 50 overlap), embed (OpenAI text-embedding-3-small), upsert to Pinecone
- [ ] Test retrieval with 3 queries: "best meal pre-workout", "how to pace the SkiErg in Hyrox", "taper protocol for a first Hyrox"
- [ ] Add Cohere rerank to the retrieval flow
- **DoD:** for each test query, top-3 reranked results are clearly relevant (you can read and confirm)

### S2-W1 — Workflow A complete — Daily Briefing with RAG (2h) — deps: S2-R2, S1-W1
- [ ] Replace hardcoded message with an AI Agent node calling Claude
- [ ] Add a custom HTTP Request tool to the agent: "search_knowledge_base" → calls Pinecone + Cohere
- [ ] Compose the prompt: system role + context from Airtable + today's calendar
- [ ] Format the brief in markdown for Telegram (workout / nutrition / recovery / sources)
- [ ] Write the result to `daily_logs` (status: "briefed")
- **DoD:** triggering manually produces a structured brief in Telegram that cites at least one source from the knowledge base

### S2-V1 — Validation pass on Day 2 (0.5h)
- [ ] Run the brief 3 times back-to-back; check responses vary meaningfully (no copy-paste from sources)
- [ ] Check idempotency: same date should not produce duplicate `daily_logs` rows
- **DoD:** 3 distinct briefs generated, 1 idempotency check passed

**Day 2 total: 5.5h**

---

## Day 3 — Conversational chat + screenshot ingestion (Wed)
**Goal:** Workflows B and C are live; you can chat with the agent and send a screenshot, both work end-to-end.

### S3-W2 — Workflow B — Conversational Chat (2.5h) — deps: S2-W1
- [ ] Telegram Trigger on message (text only for this workflow)
- [ ] Simple Memory node configured with sessionId from `chat_memory` table (session key = Telegram chat ID)
- [ ] AI Agent node (Claude) with the same RAG tool as Workflow A
- [ ] Three additional tools: `read_training_plan`, `read_today_logs`, `update_training_session` (all call Airtable)
- [ ] On every turn, append both user and assistant messages to `chat_memory`
- **DoD:** you can have a 5-turn conversation that references something from turn 1; the agent can modify today's session via chat

### S3-W3 — Workflow C — Screenshot Ingestion (1.5h) — deps: S1-C1
- [ ] Telegram Trigger on message with photo
- [ ] Download image, pass to Claude with the Vision message format
- [ ] Prompt asks Claude to identify the source (withings / strava / meal / other) and extract structured fields
- [ ] Route to the right Airtable table based on the source
- [ ] Reply on Telegram confirming what was extracted ("✓ logged: weight 79.4 kg, body fat 14.2%")
- **DoD:** sending a real Withings screenshot creates a `body_metrics` row with the correct values; sending a meal photo creates a `nutrition_logs` row

### S3-T1 — Tests + early refactors (1h)
- [ ] Send 3 different screenshot types; verify all routing decisions
- [ ] Have a chat conversation that crosses Workflow A and B (e.g. "the brief this morning said X, can we change it?")
- [ ] Fix anything embarrassing
- **DoD:** smoke test passes; no console errors in n8n executions

**Day 3 total: 5h**

---

## Day 4 — Strava sync + reliability + first end-to-end (Thu)
**Goal:** Workflow D live, all four workflows have error handling, full end-to-end demo works.

### S4-W4 — Workflow D — Strava Sync (2h) — deps: S1-C1
- [ ] Schedule Trigger every 2 hours
- [ ] HTTP Request to `https://www.strava.com/api/v3/athlete/activities?after=<24h ago>`
- [ ] Loop activities, dedup against `daily_logs.strava_activity_id`
- [ ] For new activities, map fields (Strava → Airtable) and insert
- [ ] If the activity matches a planned `training_plan` session (same date, same type), update `training_plan.status` to "done"
- **DoD:** running a Strava-recorded activity → the row appears in `daily_logs` within 2 hours and the matching plan row flips to "done"

### S4-R1 — Reliability pass on all workflows (2h) — deps: S2-W1, S3-W2, S3-W3, S4-W4
- [ ] Add `retryOnFail: true, maxTries: 3, waitBetweenTries: 5000` to every HTTP/AI node
- [ ] Add an Error Trigger to each workflow → format error → send to a private Telegram "system" channel
- [ ] Set Workflow A and B to be each other's error workflow (cross-monitoring)
- [ ] Test by temporarily breaking each workflow (bad URL, bad credential) and confirming the error notification arrives
- **DoD:** breaking each workflow on purpose produces exactly one Telegram error message with the right fields

### S4-E1 — End-to-end demo run (1h)
- [ ] At 7 AM, the brief arrives (or trigger manually)
- [ ] Chat with the agent to swap a session
- [ ] Send a withings screenshot
- [ ] Do a 20-min Strava-tracked activity
- [ ] Confirm everything propagates correctly through all 4 workflows + Airtable
- **DoD:** all 4 workflows ran successfully in one session, no manual intervention beyond the four triggers above

**Day 4 total: 5h**

---

## Day 5 — Dashboard + polish + demo prep (Fri)
**Goal:** Streamlit dashboard, all rubric artefacts complete, demo video recorded, repo pushed final.

### S5-D1 — Streamlit dashboard (3h)
- [ ] `dashboard/app.py`: 4 pages
  - **Today**: current brief, today's planned session, today's logged activities
  - **This week**: training plan table, completion status, daily metrics chart
  - **Metrics**: body weight evolution (from `body_metrics`), training volume (from `daily_logs`)
  - **Chat history**: paginated view of `chat_memory`
- [ ] Connect via `pyairtable`
- **DoD:** `streamlit run dashboard/app.py` opens a working 4-page app showing real data

### S5-P1 — Rubric artefacts (1h)
- [ ] Finalize `docs/architecture.md` (already drafted)
- [ ] Finalize `docs/project-specification.md` (already drafted)
- [ ] Finalize `AGENTS.md` (already drafted)
- [ ] Populate `skills/` with reusable skill files
- [ ] Export the 4 n8n workflows as JSON into `workflows/`
- [ ] Add 2-3 sample reports (saved briefs) to `assets/sample-reports/`
- **DoD:** every rubric line item maps to a file or section in the repo

### S5-V1 — Demo video (1h)
- [ ] Script: 1 min context, 3 min live demo, 2 min architecture walkthrough, 1 min reflections
- [ ] Record 5-7 minutes (Loom or OBS)
- [ ] Upload, embed link in README
- **DoD:** video uploaded, link in README, watchable end-to-end

### S5-S1 — Stretch goal (optional, 1h)
- [ ] Meal photo → macros estimation in Workflow C
- [ ] OR: simple weather node in Workflow A
- [ ] OR: anything else from the "OUT of scope" list
- **DoD:** stretch chosen and shipped, or explicitly skipped and noted

**Day 5 total: 5-6h**

---

## Risk register

| Risk | Mitigation |
|---|---|
| Google Calendar OAuth eats half a day | Pre-create the Google Cloud project tonight; fallback to manual `.ics` import if OAuth fails |
| Strava refresh token flow is fiddly | Use a one-shot Python script to generate the initial token; the script is in `rag-ingestion/strava-bootstrap.py` (also helpful as a code sample) |
| RAG returns irrelevant chunks | Reuse the reranking from the bootcamp lab; budget 30 min Day 2 for prompt tuning |
| Telegram bot can only have one active trigger per token | Use the same bot for all three Telegram-triggered workflows; n8n routes by message type and presence of photo |
| Vision LLM mis-reads a screenshot | Always show the extracted values in the confirmation message; the athlete can correct via chat |
| Schedule timezone confusion | Set the n8n instance timezone explicitly to Europe/Paris in Settings before activating Workflow A |

## Definition of Done — project level

The project is done when all of these are true:

- [ ] All 4 workflows run successfully end-to-end without manual intervention
- [ ] Daily Briefing fires on schedule (verified by waiting one cycle in production)
- [ ] At least 2 sample briefs are saved in `assets/sample-reports/`
- [ ] Streamlit dashboard runs locally and shows real data
- [ ] All rubric artefacts present and reviewed: README, architecture, schema, stories, project spec, AGENTS.md, skills/
- [ ] Demo video uploaded, ≤7 minutes
- [ ] Repo is public on GitHub, commit history shows incremental progress across the 5 days
