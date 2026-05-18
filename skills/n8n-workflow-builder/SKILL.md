# Skill: n8n workflow builder

## When to use

Use this skill whenever you're constructing or modifying an n8n workflow JSON for this project, whether through the n8n-mcp tools or by hand.

## Required preflight

1. Call `search_nodes` on the n8n-mcp server before guessing any node name.
2. Call `get_node` for the full schema of each node you'll use.
3. Run `validate_workflow` on the final JSON before delivering it.

## Project-specific conventions

### Naming

- Workflow names follow `Hyrox - <Workflow Letter> - <Short Description>`. E.g.: `Hyrox - A - Daily Briefing`.
- Node names use Title Case and describe behaviour, not implementation: `Fetch Today's Calendar` not `HTTP Request 1`.

### Credentials

Use these credential names exactly (they're shared across workflows):

| Service | Credential name in n8n |
|---|---|
| Airtable | `Airtable - Hyrox Coach` |
| Telegram | `Telegram - Hyrox Bot` |
| OpenAI | `OpenAI - Hyrox Coach` |
| Google Calendar | `Google Calendar - Personal` |
| Strava | `Strava - Personal` |
| Pinecone | `Pinecone - Hyrox KB` |
| Cohere | `Cohere - Reranking` |

### Model selection per workflow

Use the env-driven model name conventions defined in `.env.example` rather than hardcoding model strings in node parameters:

| Workflow | Use the env var | Resolves to (default) |
|---|---|---|
| A — Daily Briefing | `OPENAI_MODEL_BRIEFING` | `gpt-5.4` (top tier — the brief is the user-facing vitrine) |
| B — Conversational Chat | `OPENAI_MODEL_CHAT` | `gpt-5.4-mini` (volume tier — ~10× cheaper, plenty good for chat replies) |
| C — Screenshot Ingestion (Vision) | `OPENAI_MODEL_VISION` | `gpt-5.4-mini` (vision-enabled — sufficient for structured-data extraction) |
| D — Strava Sync | n/a (no LLM call) | — |

This lets you tune cost vs quality later by changing one variable, without editing workflow JSONs.

### Required reliability settings

Every HTTP Request, AI Agent, Vector Store, and external-API node must have:

```json
"retryOnFail": true,
"maxTries": 3,
"waitBetweenTries": 5000
```

These are top-level node properties, **not inside `parameters`**. The Error Handling lab established this pattern; do not deviate.

### Error trigger

Every workflow must have an Error Trigger node connected to a Set node that formats the error, followed by a Telegram Send node that posts to the chat ID stored in the n8n variable `TELEGRAM_SYSTEM_CHAT_ID`. Workflow settings must reference the workflow itself as its own error workflow.

### Date and timezone

- Always use `$now.toISO()` for full timestamps.
- For date-only fields (used as primary keys in Airtable), use `$now.toFormat("yyyy-MM-dd")`.
- The instance timezone is `Europe/Paris`. Never hardcode a different timezone in expressions.

### Reading from Airtable

Use the native Airtable node, not raw HTTP. Always use `Mapping Column Mode: Map Each Column Manually` to make the field mapping explicit and reviewable.

## Common patterns

### Pattern: AI Agent with RAG tool

```
[Airtable Read context] → [AI Agent (Claude)] → [Format response] → [Telegram Send + Airtable Write]
                              │
                              └── tool: search_knowledge_base (HTTP to Pinecone + Cohere)
```

The agent's tool descriptions must match the tool definitions in `docs/project-specification.md` verbatim. Misalignment between the spec and the tool wiring is the most common bug.

### Pattern: Schedule trigger with idempotency

```
[Schedule Trigger] → [Compute today_date]
                          ↓
                     [Airtable: read daily_logs where date == today_date]
                          ↓
                     [IF: row exists?]
                       ├─ yes → [Log: "already ran today", end]
                       └─ no  → [main workflow] → [Write daily_logs row]
```

### Pattern: Telegram with photo

The Telegram Trigger with `Updates: message` fires on both text and photo messages. Use an IF node immediately after the trigger to route:

```
[Telegram Trigger] → [IF: $json.message.photo exists?]
                       ├─ yes → Workflow C (screenshot ingestion)
                       └─ no  → Workflow B (text chat)
```

If using separate workflows for text and photos, route via the Telegram Trigger's update-type filter instead.

## Anti-patterns to refuse

- ❌ Hardcoding any value that's already in Airtable (athlete name, target date, weight target...). Always read from `athlete_profile`.
- ❌ Writing business logic in Code nodes. If a transformation needs more than 5 lines of JS, it should be in a Set node with multiple assignments or — exceptionally — in a Python script outside n8n.
- ❌ Calling external APIs without an Airtable round-trip. The agent should read from Airtable, not from APIs directly.
