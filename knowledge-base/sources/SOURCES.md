# Hyrox Coach — Knowledge Base Sources

This directory contains 9 curated sources used by the Hyrox Coach Agent's RAG pipeline. All sources are publicly available, peer-reviewed or from authoritative practitioner publications.

## Source inventory

| # | File | Type | Pages | Domain | License |
|---|------|------|-------|--------|---------|
| 01 | `01_hyrox_training_manual.pdf` | Official guide | ~30 | Training method | HYROX official |
| 02 | `02_hyrox_goruck_8week_plan.pdf` | Training plan | ~15 | Training programming | HYROX × GORUCK |
| 03 | `03_issn_nutrient_timing_2017.pdf` | Peer-reviewed position stand | 21 | Nutrition timing | CC-BY 4.0 |
| 04 | `04_precision_hydration_hyrox_fuel.pdf` | Practitioner guide | ~10 | Hyrox fueling & hydration | Precision F&H |
| 05 | `05_stronghold_wellness_hyrox_nutrition.pdf` | Practitioner guide | ~8 | Hyrox nutrition daily/race day | Stronghold Wellness |
| 06 | `06_sleep_hygiene_athletes_recovery.pdf` | Peer-reviewed review | ~12 | Sleep & recovery | Open Access |
| 07 | `07_recovery_resistance_training_microcycle.pdf` | Peer-reviewed review | ~15 | Resistance training recovery | Open Access |
| 08 | `08_periodized_carb_restriction_endurance.pdf` | Peer-reviewed meta-analysis | ~14 | Carbohydrate periodization by training intensity | CC-BY 4.0 |
| 09 | `09_resistance_training_body_recomposition.pdf` | Peer-reviewed study (2025) | ~12 | Body recomposition (RT + protein) | Open Access |

**Total : ~137 pages**, balanced across training method (~45p), nutrition timing (~39p), recovery (~27p), and macro periodization & recomposition (~26p).

## Detailed metadata

### 01 — HYROX Training Manual (2020)
- **Source** : compromisedrunning.com / HYROX official
- **URL** : https://www.compromisedrunning.com/post/hyrox-training-manual.files/HYROX_ENG_Manual_10_2020.pdf
- **Why included** : authoritative reference on race standards, movement technique, and training philosophy
- **Example RAG queries** : "What's the proper sled push technique?", "How should I structure my final taper week?"

### 02 — HYROX × GORUCK 8-Week Training Plan
- **Source** : hyroxus.com (HYROX official)
- **URL** : https://hyroxus.com/wp-content/uploads/2023/12/HYROXxGORUCK-8-Week-Training-Plan.pdf
- **Why included** : concrete example of week-by-week race prep programming
- **Example RAG queries** : "Build me week 4 of an 8-week prep", "What does a typical Hyrox simulation session look like?"

### 03 — ISSN Position Stand: Nutrient Timing (Kerksick et al., 2017)
- **Source** : Journal of the International Society of Sports Nutrition
- **DOI** : 10.1186/s12970-017-0189-4
- **URL** : https://pmc.ncbi.nlm.nih.gov/articles/PMC5596471/
- **Why included** : gold-standard evidence-based recommendations on macro timing for athletes
- **Example RAG queries** : "How many grams of carbs per kg pre-workout?", "Post-workout protein window?"

### 04 — Precision Fuel & Hydration: HYROX Fuel Guide
- **Source** : precisionhydration.com (PF&H sports nutritionists)
- **URL** : https://www.precisionhydration.com/performance-advice/nutrition/how-to-fuel-and-hydrate-a-hyrox-competition/
- **Why included** : Hyrox-specific practitioner guidance on fueling timing and hydration
- **Example RAG queries** : "What should I drink during a Hyrox race?", "Caffeine dosing for Hyrox?"

### 05 — Stronghold Wellness: HYROX Nutrition Guide
- **Source** : strongholdwellness.net (sports nutrition coaching)
- **URL** : https://www.strongholdwellness.net/blog/nutrition-for-hyrox-training-and-race-day-fueling-for-performance
- **Why included** : practical daily macro targets and meal examples for Hyrox athletes
- **Example RAG queries** : "What are typical daily macros for Hyrox training?", "How much protein should I spread per meal?"

### 06 — Sleep Hygiene for Optimizing Recovery in Athletes
- **Source** : peer-reviewed review article
- **URL** : https://pmc.ncbi.nlm.nih.gov/articles/PMC6988893/
- **Why included** : evidence-based sleep recommendations specifically for athletes, including jet lag and circadian considerations
- **Example RAG queries** : "How many hours of sleep before race day?", "Tips for sleeping the night before a race?"

### 07 — The Importance of Recovery in Resistance Training Microcycle Construction (2024)
- **Source** : peer-reviewed review
- **URL** : https://pmc.ncbi.nlm.nih.gov/articles/PMC11057610/
- **Why included** : recovery interval recommendations between resistance training sessions, directly applicable to Hyrox stations (sled pushes, wall balls, lunges)
- **Example RAG queries** : "How long between sled push sessions?", "Microcycle structure for hybrid athletes?"

### 08 — Periodized Carbohydrate Restriction in Endurance Athletes (Gejl & Nybo, 2021)
- **Source** : Journal of the International Society of Sports Nutrition, systematic review + meta-analysis
- **DOI** : 10.1186/s12970-021-00435-3
- **URL** : https://pmc.ncbi.nlm.nih.gov/articles/PMC8127206/
- **Why included** : evidence on "train low, race high" strategy — varying carb intake by session type and intensity
- **Example RAG queries** : "Should I do my morning Z2 run fasted?", "How to adjust carbs on a recovery day vs a high-intensity session?"

### 09 — Resistance Training as a Key Strategy for High-Quality Weight Loss (2025)
- **Source** : peer-reviewed study with DXA body composition assessment
- **URL** : https://pmc.ncbi.nlm.nih.gov/articles/PMC12851882/
- **Why included** : recent (2025) evidence on body recomposition protocols (FFM gain + FM loss simultaneously) with concrete macro targets
- **Example RAG queries** : "Can I lose fat without losing muscle while training for Hyrox?", "Protein target for recomposition?"

## Quality assurance

- ✅ All sources are publicly accessible (no paywalls)
- ✅ Peer-reviewed sources are open access under Creative Commons or PMC Open Access
- ✅ Practitioner sources are from established sports nutrition or HYROX-specific authorities
- ✅ Recency : 6 sources from 2017+, 3 from 2024-2025 — current evidence base
- ✅ Balanced coverage : training, nutrition timing, recovery, macro periodization, body composition

## How sources are used in the RAG pipeline

Sources are chunked (500 tokens, 50 overlap) and embedded with OpenAI `text-embedding-3-small`, then upserted to Pinecone with metadata fields `source_id`, `source_name`, `chunk_index`, and `page_estimate`. The agent retrieves the top-k chunks per query, reranks with Cohere `rerank-3.5`, and cites the source name in the brief's "📚 Sources" section.

See `rag-ingestion/README.md` and `skills/rag-ingestion/SKILL.md` for the technical pipeline.
