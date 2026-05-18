# Skill: Airtable operations

## When to use

Any read or write against the Airtable base "Hyrox Coach", whether from an n8n node or a Python script.

## The schema

Authoritative schema: `docs/airtable-schema.md`. Read it before designing any query. Seven tables: `athlete_profile`, `training_plan`, `daily_logs`, `nutrition_logs`, `body_metrics`, `schedule_events`, `chat_memory`.

## Conventions

### Field names

- Field names match the schema exactly. **Case-sensitive.** "Chat ID" not "chatId" not "chat_id".
- When n8n field-mapping by hand, copy-paste from the schema doc; don't retype.

### Primary keys (de facto)

- `athlete_profile`: there is exactly one row. Use `Find First Record` not query by ID.
- `training_plan`, `daily_logs`, `nutrition_logs`, `body_metrics`, `schedule_events`: keyed by `date`. Most queries are "give me rows where date = today" or "rows where date BETWEEN x AND y".
- `daily_logs.strava_activity_id`: idempotency key. Use this to dedup before inserting a new activity.
- `chat_memory.timestamp` + `session_id`: combined effective key.

### Read patterns

#### Read athlete profile (every workflow)
```
Airtable: List records
- Table: athlete_profile
- Limit: 1
```

#### Read today's planned session
```
Airtable: List records
- Table: training_plan
- Filter formula: IS_SAME({date}, TODAY())
```

#### Read last 7 days of activities
```
Airtable: List records
- Table: daily_logs
- Filter formula: DATETIME_DIFF(TODAY(), {date}, 'days') <= 7
- Sort: date desc
```

### Write patterns

#### Idempotent insert (used by Strava sync)
```
1. Read existing row with same strava_activity_id
2. IF found → update if any field changed, else skip
3. IF not found → insert
```

#### Conversational chat memory append
```
1. Insert a new row with timestamp = $now.toISO()
2. No reads, no dedup — chat memory grows then is pruned by a separate weekly job
```

### Filtering with date

Airtable formula syntax for dates is its own dialect:

- `TODAY()` returns today
- `IS_SAME({date}, TODAY())` for "row dated today"
- `DATETIME_DIFF(TODAY(), {date}, 'days') <= 7` for "last 7 days"
- `DATETIME_DIFF({date}, TODAY(), 'days') <= 7` for "next 7 days"

Don't mix the order of args to `DATETIME_DIFF` — it's signed.

### What never to do

- ❌ Don't `Delete record` without explicit user confirmation. Use a `status: archived` field instead if a soft-delete is needed.
- ❌ Don't write to `schedule_events` from anywhere except Workflow A's morning refresh. This table is treated as a daily cache.
- ❌ Don't write to `athlete_profile` from a workflow without surfacing the change to the athlete in chat first. This table is intentionally human-editable only.
- ❌ Don't use `Upsert` operations until you're sure of the matching field — Airtable's upsert is unforgiving if the match field has duplicates.

## Performance notes

- Each Airtable list call is rate-limited to 5 requests/second per base. For workflows that read 5+ tables, this is fine; just don't loop reads in a tight loop.
- Long-text fields ("notes", "description") can be up to 100k characters. Don't paste a full chat history into one cell; use the `chat_memory` table instead.
