# Sprint Plan — Hyrox Coach Agent

5 days, solo, ~6h focused work per day = ~30h budget.

## Conventions

- **ID**: `S<day>-<area><number>` (e.g. `S2-R1` = Day 2, RAG, task 1)
- **Estimate**: in hours (1h = one hour of focused work)
- **Deps**: prerequisite task IDs
- **DoD**: explicit criteria; the task isn't done until all are checked
- **Status**: 🔲 not started / 🟡 in progress / ✅ done / 🚫 scoped out

---

## Day 1 — Foundation (Mon)
**Goal:** all credentials configured, Airtable schema live, repo scaffold pushed, first n8n workflow stub running.

### S1-F1 — Repo + scaffolding (1h) ✅
- [x] Create GitHub repo, push the scaffold
- [x] Set up `.env.example` with all keys needed
- [x] Create `requirements.txt`
- **DoD:** repo exists, README renders, `.env` is gitignored

### S1-A1 — Airtable base creation (1h) ✅
- [x] Create base "Hyrox Coach" from `docs/airtable-schema.md`
- [x] Seed `athlete_profile` with 1 row (target_date = mid-August 2026)
- [x] Create Airtable Personal Access Token
- **DoD:** all tables exist, profile row visible, PAT saved

### S1-C1 — Credentials in n8n (1.5h) ✅
- [x] OpenAI API credential
- [x] Airtable PAT credential
- [x] Telegram bot credential
- [x] Google Calendar OAuth
- [x] Strava API credential
- [x] Pinecone + Cohere credentials
- **DoD:** "Test connection" returns ✓ for all credentials

### S1-W1 — Workflow A stub (1h) ✅
- [x] Schedule Trigger
- [x] Airtable node: read athlete_profile
- [x] Airtable node: read training_plan
- [x] Set node: package context
- [x] Telegram Send: test message
- **DoD:** triggering manually posts a Telegram message with the athlete name

### S1-P1 — Stories file + Day 2 plan (0.5h) ✅
- [x] Commit `docs/stories.md`
- **DoD:** stories.md visible on GitHub

**Day 1 total: 5h**

---

## Day 2 — Knowledge base + Workflow A complete (Tue)
**Goal:** RAG pipeline works; Workflow A generates a real, RAG-grounded brief end-to-end.

### S2-R1 — Knowledge base curation (1h) ✅
- [x] Curate 9 sources into `knowledge-base/sources/`:
  1. Hyrox Official Training Manual
  2. Hyrox / GORUCK 8-Week Preparation Plan
  3. ISSN Position Stand: Nutrient Timing (2017)
  4. Precision Hydration — Hyrox Fueling Guide
  5. Stronghold Wellness — Hyrox Nutrition Guide
  6. Sleep Hygiene for Athletes — Recovery Guide
  7. Recovery in Resistance Training — Microcycle Design
  8. Periodized Carbohydrate Restriction for Endurance Athletes
  9. Resistance Training for Body Recomposition
- **DoD:** 9 documents in `knowledge-base/sources/`, SOURCES.md lists all with citations

### S2-R2 — RAG ingestion script (2h) ✅ — deps: S2-R1, S1-C1
- [x] Write `rag-ingestion/ingest.py`: chunk (500 tokens, 50 overlap), embed (text-embedding-3-small), upsert to Pinecone
- [x] Write `rag-ingestion/test_retrieve.py`: smoke tests with 3 queries + Cohere rerank
- **DoD:** top-3 reranked results are clearly relevant for test queries

### S2-W1 — Workflow A complete (2h) ✅ — deps: S2-R2, S1-W1
- [x] n8n AI Agent node with GPT-4.1
- [x] RAG tool: embed query → Pinecone top-10 → Cohere rerank top-3
- [x] Read Google Calendar events for today
- [x] Read last 10 Strava activities
- [x] 4-section brief: Workout / Nutrition / Recovery / Sources
- [x] Write result to `daily_logs`
- [x] Schedule: 6:00 AM daily (`0 6 * * *`)
- **DoD:** brief fires on schedule, cites at least one knowledge base source

**Day 2 total: 5h**

---

## Day 3 — Conversational chat (Wed)
**Goal:** Workflow B is live; the agent can answer coaching questions and modify a session.

### S3-W2 — Workflow B — Chat Agent (2.5h) ✅ — deps: S2-W1
- [x] Telegram Trigger on text message
- [x] Window Memory node (Airtable `chat_memory`, session key = Telegram chat ID)
- [x] AI Agent node (GPT-4.1) with three tools: `search_knowledge_base`, `update_training_session`, `replan_week`
- [x] Package Chat Context node: injects athlete profile, week plan, recent logs
- [x] Reply on Telegram with the agent's response
- **DoD:** 5-turn conversation works, agent can modify today's session via chat

### S3-W3 — Workflow C — Screenshot Ingestion (1.5h) ✅ — deps: S1-C1
- [x] Telegram Trigger on photo messages; `Photos Only` IF filters out non-photo messages
- [x] Get File Path + Build Image URL: resolves Telegram file_id to a download URL
- [x] Classify Image: GPT-4.1 Vision call → one of body_metrics / nutrition / training_summary / other
- [x] Route by Type: Switch node with 4 branches
- [x] Branch body_metrics: extract weight_kg, body_fat_pct, muscle_mass_kg → insert to Airtable → Telegram confirmation
- [x] Branch nutrition: extract meal_type + macros (kcal, P, C, F) → insert to nutrition_logs → Telegram confirmation
- [x] Branch training_summary: extract activity_type, duration, distance, HR → insert to daily_logs → Telegram confirmation
- [x] Branch other: polite "cannot process" reply
- **DoD:** sending a Withings screenshot creates a body_metrics row with correct values and a Telegram confirmation

### S3-W2a — B-tool — Update Session sub-workflow (1h) ✅ — deps: S3-W2
- [x] Execute Workflow Trigger (passthrough)
- [x] Find Session by Date via Airtable search with IS_SAME formula + today fallback
- [x] Prepare Update Fields: regex parse of flat query string (session_type, duration_min, intensity, description, notes)
- [x] Skip If No Record IF guard (prevents null-ID crash)
- [x] Update Session Record in Airtable
- [x] Build Confirmation: returns human-readable result string to parent agent
- **DoD:** agent can edit any single session by date; null date falls back to today; missing record returns a clear error message

### S3-W2b — B-sub — Replan Week sub-workflow (1h) ✅ — deps: S3-W2
- [x] Execute Workflow Trigger (passthrough)
- [x] Compute week dates (next Mon–Sun), phase, weeks-to-race
- [x] Fetch done/skipped sessions to preserve
- [x] GPT-4.1 generates full 7-day plan as structured JSON
- [x] Delete existing sessions for the week, bulk-insert new plan
- [x] Return recap string to parent agent
- **DoD:** asking the agent to replan the week produces a complete new 7-day plan in Airtable

**Day 3 total: 7h**

---

## Day 4 — Weekly Planner + reliability (Thu)
**Goal:** Workflow E live, all workflows have retry logic, full end-to-end demo works.

### S4-W4 — Workflow D — Strava Sync (2h) ✅ — deps: S1-C1
- [x] Schedule Trigger every 2 hours
- [x] Fetch Strava Activities: last 7 days, up to 50 activities
- [x] Loop Over Activities (SplitInBatches, batch size 1)
- [x] Check if Exists: Airtable search on `strava_activity_id` for dedup
- [x] Is New Activity? IF node: True → insert, False → skip and loop
- [x] Insert Activity: date, activity_type, duration_min, distance_km, avg_heart_rate, strava_activity_id, notes (Strava activity name)
- [x] Log Summary: timestamps the sync completion
- **DoD:** running a Strava-recorded activity → row appears in daily_logs within 2 hours; rerunning the sync does not create duplicates

### S4-W5 — Workflow E — Weekly Planner (2.5h) ✅
- [x] Cron trigger, Friday 1:00 PM (`0 13 * * 5`)
- [x] Read athlete profile and last 10 daily logs
- [x] Read Google Calendar for next 7 days (travel detection)
- [x] GPT-4.1 generates 7 training sessions + 7 nutrition plans + batch cooking (structured output parser enforces JSON schema)
- [x] Travel-day logic: if location ≠ home city → cap session at 45 min easy Z2 / active recovery
- [x] Write training sessions to `training_plan`, nutrition plans to `nutrition_plans`
- [x] Send 3 Telegram messages: training week summary, nutrition week summary, batch cooking list
- **DoD:** workflow fires Thursday; Airtable shows 7 new sessions and 7 nutrition rows; Telegram receives 3 messages

### S4-R1 — Reliability pass (2h) ✅ — deps: S2-W1, S3-W2, S4-W5
- [x] `retryOnFail: true, maxTries: 3, waitBetweenTries: 5000` on all HTTP / AI / Airtable nodes
- [x] Rate-limit fix: `contextWindowLength` reduced from 10 to 4 in Chat Agent (prevents TPM overflow on gpt-4.1 30k limit)
- [x] Session key versioned (`-v2`) to clear poisoned memory after failed tool calls
- [x] IF guard in B-tool to skip Airtable update when record not found
- **DoD:** no unhandled crashes in n8n; rate-limit and null-ID errors resolved

**Day 4 total: 4.5h**

---

## Day 5 — Dashboard + polish (Fri)
**Goal:** Streamlit dashboard complete, all rubric artefacts present, demo ready.

### S5-D1 — Streamlit dashboard (3h) ✅
- [x] `dashboard/Dashboard.py` — Home: today's session card, 7-day week strip, sidebar with phase / weeks-to-race
- [x] `dashboard/pages/1_Weekly_Plan.py` — Week selector slider, 4 summary metrics, expandable day cards, table view
- [x] `dashboard/pages/2_Nutrition.py` — Macro charts (Altair), meal checkboxes, GPT-4.1 shopping list builder, share via WhatsApp / Telegram / plain text
- [x] `dashboard/pages/3_Chat.py` — Chat UI with same 3 tools as Telegram agent; auto-cache refresh after writes
- [x] `dashboard/pages/4_Metrics.py` — Training volume, body weight / fat trends, adherence donut chart
- [x] `dashboard/pages/5_Chat_History.py` — Paginated conversation history from Airtable `chat_memory`
- [x] `dashboard/lib/airtable_client.py` — all Airtable reads/writes
- [x] `dashboard/lib/chat_engine.py` — OpenAI function-calling loop (3 tools, streaming)
- **DoD:** `streamlit run dashboard/Dashboard.py` opens a working 6-page app with real data

### S5-P1 — Rubric artefacts (1h) ✅
- [x] `docs/stories.md` (this file)
- [x] `docs/project-specification.md`
- [x] `AGENTS.md`
- [x] `skills/` with reusable skill files
- [x] 5 n8n workflow JSONs exported to `workflows/`
- [x] `README.md` updated to reflect actual delivery
- **DoD:** every rubric line item maps to a file in the repo

### S5-V1 — Demo prep (1h) ✅
- [x] Demo walkthrough scripted (see presentation notes)
- [x] Live end-to-end: brief fires, chat modifies a session, weekly planner generates new week
- **DoD:** 8-minute demo works end-to-end without manual intervention

**Day 5 total: 5h**

---

## Risk register

| Risk | Mitigation |
|---|---|
| Google Calendar OAuth eats half a day | Pre-created Google Cloud project beforehand; fallback to manual context injection |
| Strava refresh token flow is fiddly | One-shot Python script to generate initial token |
| RAG returns irrelevant chunks | Cohere reranker on top of Pinecone top-10; 500-token chunk size tuned for paragraph-level content |
| Telegram bot can only have one active trigger per token | Single bot handles both image and text triggers; routed by message type |
| OpenAI TPM rate limit (30k for gpt-4.1) | Reduced context window from 10 to 4 turns in Chat Agent |
| n8n toolWorkflow passes args as flat string | Regex extraction in B-tool; today fallback for missing date |

---

## Definition of Done — project level

- [x] 7 workflows run successfully end-to-end (A, B + B-tool + B-sub, C, D, E)
- [x] Daily Briefing fires on schedule (9:45 AM)
- [x] Chat Agent handles tool calls without crashing (update session, replan week, RAG search)
- [x] Weekly Planner generates 7 sessions + 7 nutrition plans every Thursday
- [x] Streamlit dashboard runs locally with real data across all 6 pages
- [x] RAG pipeline: 9 sources ingested, retrieval returns relevant results
- [x] All rubric artefacts present: README, stories, project-spec, AGENTS.md, skills/
- [x] Repo on GitHub with commit history showing incremental progress
- [ ] Demo video uploaded (≤7 minutes) — replaced by live 8-minute presentation
