# Hyrox Coach Agent

An autonomous AI agent that acts as a personal Hyrox training and nutrition coach: it reads your calendar, pulls recent Strava activities, retrieves grounded coaching advice from a vetted knowledge base, and delivers a daily training brief plus on-demand chat — all via Telegram and a local Streamlit dashboard.

Built as the Module 3 project of the Ironhack AI Bootcamp by Thibaud Delaye in 5 days, solo.

## Why this exists

For four months I prepared my first Hyrox race using a long-running LLM chat. The conversation became unusable: the model forgot 90% of context, started giving generic menus, didn't know my schedule, had no idea what I'd actually done in training, and lost my workout plan five scrolls up every time I asked a follow-up. This project is the tool I wish I'd had — built for my *second* Hyrox prep (the first race is too soon to dogfood a brand-new v0 agent during taper).

## What it does

| Workflow | Trigger | Behavior |
|---|---|---|
| **A — Daily Briefing** | Cron, 6:00 AM daily | Reads athlete_profile, this week's training plan, today's Google Calendar events, and last 10 Strava activities. Generates a 4-section brief (Workout / Nutrition / Recovery / Sources) using GPT-4.1 with RAG citations. Posts to Telegram and logs to Airtable. |
| **B — Chat Agent** | Telegram message | Conversational coach with persistent memory across days. Calls three tools: `search_knowledge_base` (RAG), `update_training_session` (single-session edits), `replan_week` (full 7-day replan). Replies on Telegram. |
| **B-tool — Update Session** | Called by Chat Agent | Sub-workflow: finds the session for a given date in Airtable, parses updated fields from the agent's query string, writes the update, returns a confirmation. |
| **B-sub — Replan Week** | Called by Chat Agent | Sub-workflow: generates a new 7-day training + nutrition plan (GPT-4.1, structured JSON output), clears the existing week, bulk-inserts the new plan. |
| **C — Screenshot Ingestion** | Telegram photo message | GPT-4.1 Vision classifies the image (body_metrics / nutrition / training_summary / other), extracts structured fields from each type, writes to the appropriate Airtable table, and replies with a confirmation (e.g. "✅ Logged: 79.4 kg, 14.2% BF"). |
| **D — Strava Sync** | Cron, every 2 hours | Fetches the last 7 days of Strava activities, loops over them, deduplicates by `strava_activity_id`, and inserts new activities into `daily_logs`. |
| **E — Weekly Planner** | Cron, Friday 1:00 PM | Generates next week's 7 training sessions + 7 daily nutrition plans + batch cooking suggestions. Detects travel days from Google Calendar and adapts sessions to ≤45 min easy. Writes to two Airtable tables. Sends 3 Telegram messages. |

Plus a **Streamlit dashboard** with 6 pages (see below).

## Repository map

| Path | Purpose |
|---|---|
| `README.md` | This file |
| `docs/stories.md` | Sprint plan: user stories, tasks, estimates, dependencies, definition of done |
| `docs/project-specification.md` | Agent-facing specification |
| `docs/architecture.md` | System diagram and data flow |
| `docs/airtable-schema.md` | Table schema reference |
| `AGENTS.md` | Instructions for AI assistants working on this repo |
| `skills/` | Reusable skill files (RAG ingestion, n8n workflow patterns, etc.) |
| `workflows/` | 7 exported n8n workflow JSONs (A, B, B-tool, B-sub, C, D, E) |
| `rag-ingestion/` | `ingest.py` — chunks + embeds 9 sources into Pinecone; `test_retrieve.py` — retrieval smoke tests |
| `dashboard/` | Streamlit app (6 pages) |
| `knowledge-base/sources/` | 9 vetted PDFs: Hyrox training, ISSN nutrient timing, sleep/recovery, body recomposition |
| `assets/` | Architecture diagram and screenshots |

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Orchestration | n8n (self-hosted, `thiba-d.n8n.irn.hk`) | Visual workflows, fast iteration, native Telegram + Schedule + HTTP nodes |
| Agent framework | n8n AI Agent node (LangChain under the hood) | Function-calling loop, window memory, and tool routing without over-engineering |
| LLM — briefing, planning, chat | OpenAI **GPT-4.1** | Best quality for the morning brief, weekly planning, and conversational coaching |
| LLM — dashboard UI | OpenAI **GPT-4o** | Strong, cost-efficient for interactive features (shopping list builder, dashboard chat) |
| Embeddings | OpenAI **text-embedding-3-small** | Industry standard; fractions of a cent per ingestion run |
| Vector DB | Pinecone | Reliable, generous free tier |
| Re-ranker | Cohere Rerank v3 (`rerank-english-v3.0`) | Improves precision on top-10 Pinecone hits; free tier covers 1,000 reranks/month |
| Data store | Airtable | Single source of truth: athlete profile, training plan, nutrition plans, daily logs, chat memory |
| Dashboard | Streamlit (local) | Python-native, fast to build, no deployment needed for MVP |
| Calendar | Google Calendar API (read-only) | Used in both Daily Briefing and Weekly Planner for travel-day detection |
| Activity tracking | Strava API | On-demand reads (last 10 activities) in Workflows A and B; automated sync every 2 hours in Workflow D |
| Chat channel | Telegram bot | Low-latency push notifications and conversational interface |

## Dashboard pages

| Page | Content |
|---|---|
| **Home** (`Dashboard.py`) | Today's session card, 7-day week strip, sidebar with training phase and weeks-to-race countdown |
| **Weekly Plan** (`pages/1_Weekly_Plan.py`) | Week selector slider, 4 summary metrics, expandable day cards, full table view |
| **Nutrition** (`pages/2_Nutrition.py`) | Daily macro charts (Altair), meal checkboxes, GPT-4.1 shopping list builder, one-tap share via WhatsApp / Telegram / plain text |
| **Chat** (`pages/3_Chat.py`) | Conversational coach with the same 3 tools as the Telegram agent; auto-refreshes plan cache after any write |
| **Metrics** (`pages/4_Metrics.py`) | Training volume bar charts, body weight / body fat trend lines, weekly adherence donut chart |
| **Chat History** (`pages/5_Chat_History.py`) | Paginated conversation log pulled from Airtable `chat_memory` |

## Knowledge base (RAG)

9 vetted sources ingested into Pinecone (`text-embedding-3-small`, 500-token chunks, 50-token overlap, Cohere rerank at query time):

1. Hyrox Official Training Manual
2. Hyrox / GORUCK 8-Week Preparation Plan
3. ISSN Position Stand: Nutrient Timing (2017)
4. Precision Hydration — Hyrox Fueling Guide
5. Stronghold Wellness — Hyrox Nutrition Guide
6. Sleep Hygiene for Athletes — Recovery Guide
7. Recovery in Resistance Training — Microcycle Design
8. Periodized Carbohydrate Restriction for Endurance Athletes
9. Resistance Training for Body Recomposition

## API integrations

| Service | Usage |
|---|---|
| OpenAI | GPT-4.1 (agent, planner, Vision), GPT-4o (dashboard), text-embedding-3-small (RAG) |
| Pinecone | Vector store for knowledge base chunks |
| Cohere | Reranker — top-3 from top-10 Pinecone results |
| Airtable | All persistent state: sessions, nutrition, logs, body metrics, profile, chat memory |
| Telegram | Outbound briefs + inbound chat and photo messages |
| Google Calendar | Travel detection and schedule context |
| Strava | On-demand activity feed (A, B) + scheduled 2-hour sync (D) |

## How to run

1. Clone repo, create `.env` from `.env.example`
2. Set up the Airtable base (see `docs/airtable-schema.md`)
3. Configure n8n credentials: Telegram bot, Airtable PAT, OpenAI API, Google Calendar OAuth, Strava API, Pinecone, Cohere
4. Import the 7 workflow JSONs from `workflows/`
5. Run `python rag-ingestion/ingest.py` once to populate Pinecone
6. Activate the 3 scheduled/triggered workflows in n8n (A, B, E)
7. Run `streamlit run dashboard/Dashboard.py` for the local dashboard

## Beyond the original spec

The original 5-day plan budgeted for 4 workflows and a 4-page dashboard. What shipped:

- 7 n8n workflows (A, B, B-tool, B-sub, C, D, E)
- 6 Streamlit pages, including Nutrition with a GPT-4.1 shopping list builder and Chat with full tool-calling
- Strava Sync (D) running every 2 hours with dedup, in addition to the on-demand reads in A and B
- Vision ingestion (C) covering three screenshot types (body metrics, nutrition, training summaries)

## Status

Built in 5 days. See `docs/stories.md` for the full sprint trace.

## Author

Thibaud Delaye — Ironhack AI Bootcamp, Module 3 Project, May 2026.
