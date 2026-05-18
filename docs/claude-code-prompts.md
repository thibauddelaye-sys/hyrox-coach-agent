# Prompts for Claude Code — Day-by-Day

This is the playbook for using Claude Code (with the n8n-mcp server) during the 5-day sprint. Each day has one or two prompts to use as a starting point — adapt as the project evolves.

The pattern for every prompt:
1. Set context (what we've already built)
2. State the objective
3. List explicit constraints (from `AGENTS.md` and the relevant skill)
4. Specify expected deliverables

---

## Day 1 — Prompt 1: Stub Workflow A (Daily Briefing skeleton)

Use this once Airtable + all credentials are configured (after task S1-C1 in `docs/stories.md`).

```
You're helping me build "Hyrox Coach Agent", an autonomous AI coaching system 
for Hyrox race preparation. Read these files first to align on context:

- AGENTS.md (the unconditional rules for AI assistants working on this repo)
- docs/architecture.md (system overview, key design decisions)
- docs/airtable-schema.md (the 7 Airtable tables and their fields)
- docs/project-specification.md (the agent's role and tools)
- docs/stories.md (the 5-day sprint plan; we're at task S1-W1)
- skills/n8n-workflow-builder/SKILL.md (n8n conventions for this project)
- skills/airtable-operations/SKILL.md (Airtable patterns and gotchas)
- skills/telegram-channel-conventions/SKILL.md (Telegram formatting rules)

OBJECTIVE — task S1-W1
Build a stub for Workflow A "Daily Briefing", just enough to verify the 
plumbing works end to end before adding intelligence:

- Schedule Trigger (configured to fire every 5 minutes during dev — we'll 
  change to 7 AM Europe/Paris in S4-R1)
- Airtable node: read the single athlete_profile row
- Airtable node: read training_plan rows filtered to today
- Set node: package context into a single object
- Telegram Send node: post a plain-text message to the athlete channel 
  containing the athlete's name and the description of today's session 
  (or "no session today" if empty)

CONSTRAINTS
- Use n8n-mcp tools (search_nodes, get_node, validate_workflow) for every 
  node — never guess parameter names
- Set retryOnFail: true, maxTries: 3, waitBetweenTries: 5000 on every 
  non-trigger node
- Use the exact credential names from skills/n8n-workflow-builder/SKILL.md
- Use the date and field-name conventions from skills/airtable-operations/SKILL.md
- Use MarkdownV2 escaping per skills/telegram-channel-conventions/SKILL.md
- Telegram message uses the chat ID from the n8n variable 
  TELEGRAM_ATHLETE_CHAT_ID

DELIVERABLES
1. Complete workflow JSON I can paste into n8n
2. A brief explanation of each node and the data flow between them
3. Output of validate_workflow showing 0 errors
4. Three things I should test manually after importing, with the expected 
   result for each

Please produce the JSON and explanation. I'll review before importing.
```

---

## Day 2 — Prompt 1: RAG ingestion script

```
We've established the n8n-mcp workflow A stub from yesterday (S1-W1, done). 
Today we're building the knowledge base layer that grounds the agent's 
advice in vetted sources.

Read these files first:
- skills/rag-ingestion/SKILL.md (the playbook for this area)
- knowledge-base/SOURCES.md (the 5 sources I've curated)
- docs/project-specification.md (so you understand what the agent will 
  do with the retrieved chunks)

OBJECTIVE — task S2-R2
Write `rag-ingestion/ingest.py`: a one-shot script that reads everything 
in knowledge-base/, chunks it (500 tokens, 50 overlap), embeds, and upserts 
to Pinecone with the metadata schema specified in the SKILL file. The 
script must be idempotent: re-running it must not duplicate vectors.

Then write `rag-ingestion/retrieve.py`: a function `search_knowledge_base(query: str) -> list[dict]` 
that embeds the query, retrieves top 10 from Pinecone, reranks with Cohere, 
and returns the top 3 chunks (text + source_title + score).

CONSTRAINTS
- Python 3.8+, no async (keep it simple for the MVP)
- Load secrets from .env via python-dotenv
- Use the openai (OPENAI_API_KEY → text-embedding-3-small), pinecone-client, and cohere official clients
- Use tiktoken cl100k_base for chunking
- Deterministic chunk IDs: <source_slug>__<chunk_index> formatted as 
  zero-padded 4-digit indices
- Print progress (don't be silent on a 5-minute run)
- Add a __main__ block to retrieve.py that runs the 3 test queries from 
  the SKILL and prints relevance

DELIVERABLES
1. ingest.py
2. retrieve.py with the test queries wired in
3. A short README inside rag-ingestion/ explaining how to run both
```

---

## Day 2 — Prompt 2: Workflow A complete with RAG

```
The RAG layer is ready (S2-R2 done). Now we make Workflow A actually 
intelligent.

Read these to refresh context:
- docs/project-specification.md (the agent's identity, tools, and briefing 
  format — this is the most important file for this task)
- skills/n8n-workflow-builder/SKILL.md
- The current Workflow A JSON (I'll paste it below)

[paste current S1-W1 workflow JSON]

OBJECTIVE — task S2-W1
Replace the hardcoded Telegram message with an AI Agent node 
(OpenAI Chat Model, model from env var OPENAI_MODEL_BRIEFING → gpt-5.4) 
that:

1. Receives the packaged context from the Set node
2. Has access to one tool: search_knowledge_base, which is an HTTP Request 
   to a local endpoint POST http://localhost:8000/search wrapping retrieve.py
3. Generates the brief following the markdown structure in 
   docs/project-specification.md (Briefing role section)
4. Writes the brief text to a new daily_logs row with status "briefed"
5. Sends the brief to Telegram (athlete channel) in MarkdownV2

The tool description and instructions inside the AI Agent prompt must 
match docs/project-specification.md verbatim.

CONSTRAINTS
- Same reliability and naming conventions as before
- Idempotency: if a daily_logs row for today with status "briefed" already 
  exists, skip the whole workflow and log "already briefed today" to the 
  system channel — don't generate a duplicate brief
- Use the chat_memory table only in Workflow B; Workflow A doesn't write 
  to chat_memory

DELIVERABLES
1. Updated workflow JSON (full, not a diff)
2. The exact prompt text used in the AI Agent node
3. Output of validate_workflow
4. One sample brief I should expect when I trigger it (mock data is fine, 
   so I can compare against the real output)
```

---

## Day 3 — Prompt 1: Workflow B (Conversational chat)

```
Workflow A is shipped (S2-W1 done). Now we build the conversational 
counterpart.

Re-read:
- docs/project-specification.md (Conversational role section)
- skills/n8n-workflow-builder/SKILL.md (especially the "AI Agent with RAG 
  tool" pattern)
- skills/airtable-operations/SKILL.md (chat_memory table conventions)

OBJECTIVE — task S3-W2
Build Workflow B "Hyrox - B - Conversational Chat":

- Telegram Trigger (text messages only — photo messages are routed to 
  Workflow C; either filter here or split via IF)
- Read athlete_profile, today's training_plan row, last 7 days of 
  daily_logs, last 5 body_metrics
- Read last 20 turns of chat_memory for this session_id (= Telegram chat ID)
- Insert the user's incoming message into chat_memory immediately
- AI Agent node with:
  * search_knowledge_base tool (same as Workflow A)
  * update_training_session tool (HTTP to Airtable update endpoint)
  * read_daily_logs tool
  * read_training_plan tool
- Insert the agent's response into chat_memory
- Send the response back to Telegram

CONSTRAINTS
- Replies under 200 words by default
- Match coach_tone and coach_severity from athlete_profile
- All four tools' descriptions and signatures match docs/project-specification.md
- Reliability settings on every external call

DELIVERABLES
1. Workflow JSON
2. The system prompt text used in the AI Agent node (this should be the 
   "Conversational role" section of the project spec, lightly adapted)
3. A 5-turn test transcript: I'll give you the user's messages, you 
   predict what the agent should respond
```

---

## Day 3 — Prompt 2: Workflow C (Screenshot ingestion)

```
OBJECTIVE — task S3-W3
Build Workflow C "Hyrox - C - Screenshot Ingestion":

- Telegram Trigger (photo messages only)
- Download the image from Telegram
- Call OpenAI (model from env var OPENAI_MODEL_VISION → gpt-5.4-mini) 
  with the Vision message format. Prompt: 
  "Classify this image as one of: withings_scale, strava_summary, 
   meal_photo, other. Then extract structured fields per the schema below: 
   ..."
- Use a strict JSON Schema for the response so we get reliable structured 
  output
- Based on the classification, route to:
  * withings_scale → write to body_metrics
  * strava_summary → write to daily_logs (handle dedup against existing 
    strava_activity_id by date+activity_type)
  * meal_photo → write to nutrition_logs with source="photo"
  * other → reply asking the athlete what they meant
- Reply on Telegram confirming the extraction

CONSTRAINTS
- The structured-output JSON schema must include all fields in the target 
  Airtable tables, even if optional (Vision LLM is more reliable when it 
  has the full schema)
- Reliability settings everywhere
- Always echo extracted values back in the confirmation message

Same DELIVERABLES format as before.
```

---

## Day 4 — Prompt 1: Workflow D (Strava sync) + Reliability pass

```
OBJECTIVE — task S4-W4 + S4-R1

Part 1: Build Workflow D "Hyrox - D - Strava Sync":
- Schedule Trigger every 2 hours
- Fetch Strava activities for the last 24h (GET /api/v3/athlete/activities)
- For each activity: dedup against daily_logs.strava_activity_id, then 
  insert if new
- If the activity matches a planned training_plan row (same date, similar 
  type), update that row's status to "done"

Part 2: Reliability pass on all 4 workflows. Use the patterns from the 
Error Handling lab. For each workflow:
- Verify retry settings on every external call (HTTP, AI Agent, Airtable 
  if applicable)
- Add an Error Trigger that posts to the system Telegram channel using 
  the format in skills/telegram-channel-conventions/SKILL.md
- Configure the workflow's "Error Workflow" setting to point to itself 
  (so the Error Trigger fires correctly)

DELIVERABLES
1. Workflow D JSON
2. A diff or list of changes made to each of A, B, C for the reliability 
   pass
3. A test plan: 4 specific failure modes I should manually inject to 
   verify the Error Trigger fires correctly in each workflow
```

---

## Day 5 — Prompt 1: Streamlit dashboard

```
OBJECTIVE — task S5-D1

Build `dashboard/app.py` — a Streamlit app with 4 pages:

1. **Today** — Today's brief (read from daily_logs), today's planned 
   session, today's actual activity (if any), today's body metrics 
   (latest row up to today)
2. **This week** — Training plan table (Mon-Sun of current week), 
   completion status, a simple bar chart of training volume by day
3. **Metrics** — Body weight trend (line chart from body_metrics, last 
   90 days), training volume trend (last 90 days)
4. **Chat history** — Paginated table of chat_memory, newest first, 
   collapsed by day

CONSTRAINTS
- Use pyairtable
- Cache reads with @st.cache_data(ttl=300)
- Sidebar shows the athlete name and current phase (Base/Build/Peak/Taper) 
  computed from hyrox_target_date
- Plain Streamlit components only — no custom CSS, no extra plotly tricks
- Loads in under 3 seconds on a clean cache

DELIVERABLES
1. app.py (single file is fine)
2. Updated requirements.txt with streamlit + pandas + matplotlib (or 
   altair) + pyairtable + python-dotenv
3. A README inside dashboard/ explaining how to run and configure
```

---

## Generic prompt: when something is broken

```
I'm seeing this error in workflow <name>:

<paste the error and the n8n execution screenshot or JSON>

Read skills/<relevant>/SKILL.md and the workflow JSON below. Diagnose the 
root cause, propose a minimal fix, and show me the changed JSON. Do NOT 
refactor anything unrelated. If the cause is unclear from what I've 
given you, ask me ONE question that would resolve the ambiguity.

<paste workflow JSON>
```
