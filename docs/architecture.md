# Architecture

## System overview

The Hyrox Coach is built around a **single source of truth in Airtable** that's read and written by four independent n8n workflows. The LLM (Claude) never talks to external APIs directly — every piece of context it sees is already structured in Airtable. This isolation means new data sources can be added later (Withings API, Komoot, weather) without touching the agent's logic.

## High-level data flow

```
                       ┌─────────────────────────────────┐
                       │       ATHLETE (Thibaud)          │
                       └──────┬─────────────────┬────────┘
                              │                 │
                       Telegram in/out      Dashboard view
                              │                 │
                              ▼                 ▼
        ┌──────────────────────────────────────────────────────┐
        │                  n8n INSTANCE                         │
        │                                                       │
        │   ┌─────────────────┐   ┌────────────────────────┐  │
        │   │  Workflow A     │   │  Workflow B            │  │
        │   │  Daily Briefing │   │  Conversational Chat   │  │
        │   │  (Schedule 7h)  │   │  (Telegram trigger)    │  │
        │   └─────────────────┘   └────────────────────────┘  │
        │                                                       │
        │   ┌─────────────────┐   ┌────────────────────────┐  │
        │   │  Workflow C     │   │  Workflow D            │  │
        │   │  Screenshot     │   │  Strava Sync           │  │
        │   │  Ingestion      │   │  (Schedule 2h)         │  │
        │   │  (Telegram img) │   │                        │  │
        │   └─────────────────┘   └────────────────────────┘  │
        │                                                       │
        └─────────┬─────────────────────────┬───────────────────┘
                  │                         │
            reads context              writes results
                  │                         │
                  ▼                         ▼
        ┌──────────────────────────────────────────────────────┐
        │           AIRTABLE BASE — "Hyrox Coach"               │
        │                                                       │
        │  athlete_profile  training_plan    daily_logs        │
        │  nutrition_logs   body_metrics     schedule_events    │
        │  chat_memory                                          │
        └──────┬───────────────────────────────────────┬────────┘
               │                                       │
       Streamlit dashboard reads                       │
               │                                       │
               ▼                                       │
        ┌─────────────────┐                            │
        │  Streamlit App  │                            │
        │  (4 pages)      │                            │
        └─────────────────┘                            │
                                                       │
                                                       ▼
                                       ┌──────────────────────────┐
                                       │      External APIs        │
                                       │                           │
                                       │  • OpenAI (GPT-5.4 +       │
                                       │    GPT-5.4-mini + Vision)  │
                                       │  • OpenAI embeddings       │
                                       │  • Pinecone (RAG vectors)  │
                                       │  • Cohere (reranking)     │
                                       │  • Google Calendar (read) │
                                       │  • Strava (read activ.)   │
                                       │  • Telegram Bot API       │
                                       └──────────────────────────┘
```

## Key design decisions

### 1. Airtable as single source of truth
All four workflows converge on Airtable. Adding a new data source later is a 1-day job: write a new workflow that pushes to the right table, and the existing agents pick up the data automatically without modification.

### 2. n8n native AI Agent node instead of LangGraph
The agent loop here is simple: fetch context → reason → optionally call a tool → respond. LangGraph would be over-engineering. The n8n AI Agent node (which wraps LangChain) handles tool calls, memory, and streaming out of the box. We reserve LangGraph for cases where the agent needs branching state machines that n8n can't express.

### 3. Screenshots for body metrics instead of Withings API
The Withings public API requires manual approval that can take weeks. Screenshots cost zero setup and generalise: the same Vision-LLM ingestion pipeline handles Withings scale photos, Strava activity summaries, and meal photos. Trade-off accepted: slightly higher LLM cost per ingestion (~€0.01) vs days of OAuth setup.

### 4. RAG on five vetted sources only, not the open web
A small, curated knowledge base produces better answers than scraping the web. The five sources are: the Hyrox Training Guide, Joe Friel periodization principles, the ISSN Position Stand on nutrient timing, Asker Jeukendrup's sports nutrition material, and a handful of curated community articles on first-time Hyrox prep. All cite-able.

### 5. Two trigger surfaces (Schedule + Telegram), not one
The athlete experience requires both push (the morning brief arrives automatically) and pull (chatting on demand). These are two independent workflows that share Airtable state — a separation that makes each easier to debug and test.

### 6. Streamlit local instead of deployed web app
For a 5-day MVP with a single user (the athlete is also the developer), a local Streamlit app is a 2-3 hour build. Deploying it adds 2+ hours, an SSL cert, and a hosting bill — none of which adds product value at MVP stage. Easy to deploy later (Streamlit Community Cloud is free).

### 7. Tiered LLM strategy (GPT-5.4 + GPT-5.4-mini)
The project uses two OpenAI models, picked per task by cost-vs-quality fit. **GPT-5.4** powers the daily brief — the project's most visible output, where reasoning depth and natural language matter. **GPT-5.4-mini** powers conversational chat, screenshot vision extraction, and all dev iteration — it's about ten times cheaper and more than sufficient for these tasks. Embeddings use `text-embedding-3-small` (effectively free at this volume). Total estimated cost over the 5 dev days + 30 days of personal use: under $5, comfortably within the $15 bootcamp credit allowance.

### 8. Two OpenAI keys (bootcamp + personal)
Dev and tests use a personal OpenAI key with dashboard visibility (so the developer can monitor real-time spend and tune prompts before they leak into production). Once workflows are stable from Day 3 onwards, production runs switch to the bootcamp key. This protects the limited bootcamp credits and provides accurate cost data for the project documentation.

## Reliability layer

Every workflow has:
- **Retry on failure** (3 retries, 5s delay) on all HTTP and AI nodes — copied directly from the Error Handling lab pattern.
- **Error Trigger** at the workflow level that catches uncaught failures and posts to a "system" Telegram channel.
- **Idempotency check** on Workflow A (Daily Briefing) using the `date` field, so re-running the same day doesn't duplicate the brief.
- **Validation** of all data going into Airtable (typed fields enforced at the Airtable schema level; types double-checked in Set nodes before insert).

See `docs/stories.md` task `S5-R1` for the full reliability checklist.

## Why this architecture meets the rubric

| Rubric criterion | How this architecture addresses it |
|---|---|
| Agent-based system with justified framework | n8n AI Agent node; rationale documented above |
| 2+ real API integrations | Strava API + Google Calendar API + Pinecone + Cohere + OpenAI (5 integrations total, well over the 2 minimum) |
| Comprehensive structured reports | Daily Briefing is a structured, multi-section report (workout, nutrition, recovery, citations) tailored to the athlete |
| Error handling and reliability | Retry + Error Trigger + idempotency on every workflow |
| Operates autonomously after trigger | Daily Briefing runs unattended at 7 AM with no human in the loop |
| Optional advanced: RAG | Pinecone + Cohere on five Hyrox/nutrition sources |
| Optional advanced: MCP | n8n-mcp used during development to accelerate workflow construction with Claude Code |
