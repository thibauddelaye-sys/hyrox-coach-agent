# Hyrox Coach Agent

An autonomous AI agent that acts as a Hyrox training and nutrition coach: it reads your calendar, syncs your Strava activities, ingests body-metric screenshots, retrieves grounded coaching advice from a vetted knowledge base, and delivers a daily training brief plus on-demand chat — all via Telegram and a local Streamlit dashboard.

Built as the Module 3 project of the Ironhack AI bootcamp by Thibaud Delaye in 5 days, solo.

## Why this exists

For four months I prepared my first Hyrox race using a long-running LLM chat. The conversation became unusable: the model forgot 90% of context, started giving generic menus, didn't know my schedule, had no idea what I'd actually done in training, and lost my workout plan five scrolls up every time I asked a follow-up. This project is the tool I wish I'd had — built for my *second* Hyrox prep (the first race is too soon to dogfood a brand-new v0 agent during taper).

## What it does

| Workflow | Trigger | Behavior |
|---|---|---|
| Daily Briefing | Schedule, 7 AM | Reads today's calendar, last 7 days of Strava activities, latest body metrics, and the active training plan. Generates a personalised brief (workout + nutrition + recovery notes) using Claude with RAG citations. Posts to Telegram + logs to Airtable. |
| Conversational Chat | Telegram message | Lets the athlete adjust today's workout, ask coaching questions, request a meal idea, and so on. Has persistent memory (the conversation continues across days) and the same RAG-grounded advice. |
| Screenshot Ingestion | Telegram image | Athlete sends a photo of their Withings scale, Strava summary, or a meal. Vision LLM extracts the structured data (weight/body-fat/sleep, kilometers/pace/heart-rate, estimated macros) and writes it to the right Airtable table. |
| Strava Sync | Schedule, every 2 hours | Pulls new Strava activities into the `daily_logs` table so the chat and briefing always have fresh training context. |

Plus a **Streamlit dashboard** showing the current week's plan, recent metrics, and chat history.

## Repository map

| Path | Purpose |
|---|---|
| `README.md` | This file |
| `docs/architecture.md` | System diagram, data flow, design decisions |
| `docs/airtable-schema.md` | All 7 tables, columns, relationships |
| `docs/stories.md` | Sprint plan: user stories, tasks, estimates, dependencies, definition of done |
| `docs/project-specification.md` | Agent-facing spec written for the autonomous agent |
| `AGENTS.md` | Top-level instructions for AI assistants working on this repo |
| `skills/` | Reusable skill files (one per area: rag-ingestion, n8n-workflow-builder, etc.) |
| `workflows/` | Exported n8n workflow JSONs |
| `rag-ingestion/` | Python script that chunks and embeds the knowledge base into Pinecone |
| `dashboard/` | Streamlit app |
| `knowledge-base/` | Source PDFs and markdown for the RAG (Hyrox guide, ISSN nutrient timing, etc.) |
| `assets/` | Architecture diagram, screenshots, demo video link |

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Orchestration | n8n (self-hosted, instance: `thiba-d.n8n.irn.hk`) | Visual workflows, fast iteration, native Telegram + Schedule + HTTP nodes |
| Agent framework | n8n's built-in AI Agent node (LangChain under the hood) | Sufficient for this use case; LangGraph would be over-engineering for 4 workflows |
| LLM (briefing) | OpenAI **GPT-5.4** | Top model used where output quality matters most (the morning brief is the project's vitrine) |
| LLM (chat, vision, dev) | OpenAI **GPT-5.4-mini** | ~10x cheaper than the top model, more than enough for conversational replies and screenshot data extraction. Keeps the API budget under $5 for a full month of personal use. |
| Embeddings | OpenAI **text-embedding-3-small** | Industry standard, fractions of a cent per ingestion run |
| Vector DB | Pinecone | Already familiar from RAG Lab, reliable, generous free tier |
| Re-ranker | Cohere Rerank | Same — proven in the bootcamp RAG Lab; free tier covers 1000 reranks/month |
| Data store | Airtable | Single source of truth, mobile-friendly, free tier, easy to extend |
| Dashboard | Streamlit (local) | Python-native, 2-3h to build a clean UI, no deployment needed for MVP |
| Calendar | Google Calendar API (read-only) | Standard, OAuth in n8n is straightforward |
| Activity tracking | Strava API (read activities) | Garmin watches sync there automatically; one integration covers both |
| Body metrics | Telegram screenshots → Vision LLM | Withings API requires manual approval and would burn a day; screenshots cost nothing and generalise |
| Chat channel | Telegram bot | Already proven in the Lead Capture lab |

## How to run (setup quickstart)

Detailed instructions are in `docs/architecture.md` and individual skill files. High level:

1. Clone repo, create `.env` from `.env.example`
2. Set up Airtable base from `docs/airtable-schema.md` (or import the provided base JSON)
3. Configure n8n credentials: Telegram bot, Airtable PAT, OpenAI API, Google Calendar OAuth, Strava OAuth, Pinecone, Cohere
4. Import the 4 workflow JSONs from `workflows/`
5. Run `python rag-ingestion/ingest.py` once to populate Pinecone
6. Activate the workflows in n8n
7. Run `streamlit run dashboard/app.py` for the dashboard

## Status

Built in 5 days. See `docs/stories.md` for the full sprint trace.

## Author

Thibaud Delaye — Ironhack AI Bootcamp, Module 3 Project, May 2026.
