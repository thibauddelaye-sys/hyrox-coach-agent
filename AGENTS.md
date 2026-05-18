# AGENTS.md — Instructions for AI assistants

This file is read by any AI assistant (Claude Code, Cursor, n8n's AI Agent node, etc.) working on this repository. Follow these rules unconditionally.

## Repository purpose

This is an MVP autonomous coaching agent for Hyrox preparation, built in 5 days as a bootcamp Module 3 project. The owner is the athlete and the only end user. Prioritize: shipping the MVP, code clarity over cleverness, and clear separation between data, orchestration, and presentation.

## What lives where

- **n8n workflows** = orchestration, scheduling, tool calls, conversation routing. Build new ones via the n8n MCP server when possible.
- **Airtable** = single source of truth. Never bypass it from a workflow.
- **Python** = used for two things only: (1) the one-shot RAG ingestion script, (2) the Streamlit dashboard. Do not move business logic into Python.
- **Knowledge base** = curated PDFs/markdown in `knowledge-base/`. Do not scrape new content without asking the human.

## When generating n8n workflow JSON

1. Always use the n8n-mcp tools `search_nodes` and `get_node` before writing JSON, to ground node names and parameter shapes in real, current schemas. Never guess.
2. Use `validate_workflow` before delivering. Fix any errors. Document any warnings you choose to ignore.
3. Set `retryOnFail: true, maxTries: 3, waitBetweenTries: 5000` on every HTTP, AI, and external-service node. This is non-negotiable.
4. Every workflow that can fail silently must have an Error Trigger that posts to the system Telegram channel (chat ID stored in n8n credentials as `TELEGRAM_SYSTEM_CHAT_ID`).
5. Reference the project specification (`docs/project-specification.md`) for any prompt used inside an AI Agent node.

## When writing Python

1. Use `pyairtable` for Airtable, not raw HTTP — the SDK handles pagination correctly.
2. Use Pinecone's official Python client (`pinecone-client`), and Cohere's official client (`cohere`).
3. Load secrets only from `.env` via `python-dotenv`. Never accept them as function arguments.
4. Keep scripts idempotent. Re-running `rag-ingestion/ingest.py` must not produce duplicate vectors (use deterministic IDs like `sha256(source_path + chunk_index)`).
5. Streamlit: prefer `@st.cache_data(ttl=300)` for Airtable reads. Don't poll faster than every 5 minutes.

## When committing

1. One concern per commit. Use Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`.
2. Reference the story ID from `docs/stories.md` in the commit body when applicable.
3. Never commit `.env`, `*.json` exports that contain secrets, or files inside `assets/` larger than 5 MB.

## When in doubt

1. Re-read `docs/project-specification.md`.
2. Check the relevant skill file under `skills/`.
3. If still uncertain, ask the human — do not silently make architectural decisions.

## Don't

- Don't add dependencies without justifying them in the commit message.
- Don't refactor working code unless the human explicitly asked.
- Don't expand scope: features outside `docs/stories.md` are not in the MVP.
- Don't write tests longer than the code they cover. Spot-check, don't TDD an MVP.
