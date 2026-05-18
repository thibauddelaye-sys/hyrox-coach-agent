# Workflows

Exported n8n workflow JSONs. Will be populated as workflows are built across Days 1-4.

| File | Status | Story | Description |
|---|---|---|---|
| `A-daily-briefing.json` | 🔲 not yet exported | S2-W1 | Morning brief at 7 AM |
| `B-conversational-chat.json` | 🔲 not yet exported | S3-W2 | Telegram chat agent |
| `C-screenshot-ingestion.json` | 🔲 not yet exported | S3-W3 | Vision LLM screenshot ingestion |
| `D-strava-sync.json` | 🔲 not yet exported | S4-W4 | Strava activities → daily_logs |

## Export procedure

In n8n, for each workflow:
1. Open the workflow
2. Menu ⋮ (top right) → Download
3. Save the file here with the names above
4. Strip any embedded credential IDs (n8n includes them by default, but the values themselves stay in your instance)

## Import procedure (someone else reproducing the project)

1. Create all the credentials listed in `skills/n8n-workflow-builder/SKILL.md` first
2. In n8n, Workflows → Import from File
3. After import, re-link each node to your own credentials (the JSON references credentials by ID, which differs across instances)
