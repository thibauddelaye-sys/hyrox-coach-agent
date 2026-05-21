"""One-shot demo seed script — inserts sessions + nutrition for demo purposes.

Run once:  python scripts/seed_demo_week.py
Safe to re-run: deletes existing planned sessions/nutrition in the range before inserting.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from dashboard.lib import airtable_client as db

PHASE       = "Build"
WEEK_NUMBER = 12

# ── This week Thu–Sun (21–24 May) ─────────────────────────────────────────────
THIS_WEEK = [
    {
        "date": "2026-05-21",
        "phase": PHASE,
        "week_number": WEEK_NUMBER,
        "session_type": "Strength",
        "description": (
            "Full-body strength session focused on Hyrox accessory work. "
            "4×8 sled push (bodyweight), 3×10 DB lunges, 3×12 farmer carry, "
            "3×15 wall ball, 2×20 burpee broad jump. Rest 90s between sets."
        ),
        "duration_min": 60,
        "intensity": "moderate",
        "notes": "Last heavy session before wedding weekend — keep form tight, no grinding.",
        "status": "planned",
    },
    {
        "date": "2026-05-22",
        "phase": PHASE,
        "week_number": WEEK_NUMBER,
        "session_type": "Z2 endurance",
        "description": (
            "60-min easy run at conversational pace (Z2, HR 130–145 bpm). "
            "Flat route, no watch pressure. Focus on nasal breathing and cadence ~170 spm."
        ),
        "duration_min": 60,
        "intensity": "moderate",
        "notes": "Pre-wedding flush run — keeps aerobic base ticking without fatigue.",
        "status": "planned",
    },
    {
        "date": "2026-05-23",
        "phase": PHASE,
        "week_number": WEEK_NUMBER,
        "session_type": "Mobility",
        "description": (
            "30-min morning mobility flow: hip flexors, thoracic rotation, hamstring, "
            "shoulder capsule. Finish with 10-min breathwork. Done before 11h."
        ),
        "duration_min": 30,
        "intensity": "easy",
        "notes": "Wedding day — morning only, done before 11h. Event starts 13h.",
        "status": "planned",
    },
    {
        "date": "2026-05-24",
        "phase": PHASE,
        "week_number": WEEK_NUMBER,
        "session_type": "Rest",
        "description": "Full rest day. Post-wedding recovery.",
        "duration_min": 0,
        "intensity": "easy",
        "notes": "Back at 2AM — prioritise sleep and hydration.",
        "status": "planned",
    },
]

# ── Last week Mon–Sun (13–19 May) — mix of done/skipped for adherence chart ──
LAST_WEEK = [
    {
        "date": "2026-05-13",
        "phase": PHASE,
        "week_number": WEEK_NUMBER - 1,
        "session_type": "Strength",
        "description": "Lower body + posterior chain: deadlift, step-ups, sled row, core.",
        "duration_min": 65,
        "intensity": "hard",
        "notes": "",
        "status": "done",
    },
    {
        "date": "2026-05-14",
        "phase": PHASE,
        "week_number": WEEK_NUMBER - 1,
        "session_type": "Z2 endurance",
        "description": "55-min easy run, HR capped at 145 bpm.",
        "duration_min": 55,
        "intensity": "moderate",
        "notes": "",
        "status": "done",
    },
    {
        "date": "2026-05-15",
        "phase": PHASE,
        "week_number": WEEK_NUMBER - 1,
        "session_type": "Rest",
        "description": "Planned rest day.",
        "duration_min": 0,
        "intensity": "easy",
        "notes": "",
        "status": "done",
    },
    {
        "date": "2026-05-16",
        "phase": PHASE,
        "week_number": WEEK_NUMBER - 1,
        "session_type": "Intervals",
        "description": "6×800m at 5K pace, 2-min walk recovery. 10-min warm-up + cool-down.",
        "duration_min": 60,
        "intensity": "hard",
        "notes": "",
        "status": "done",
    },
    {
        "date": "2026-05-17",
        "phase": PHASE,
        "week_number": WEEK_NUMBER - 1,
        "session_type": "Active recovery",
        "description": "30-min easy walk + foam rolling.",
        "duration_min": 30,
        "intensity": "easy",
        "notes": "",
        "status": "skipped",
    },
    {
        "date": "2026-05-18",
        "phase": PHASE,
        "week_number": WEEK_NUMBER - 1,
        "session_type": "Hyrox simulation",
        "description": (
            "Full Hyrox race simulation: 8×1km run + 8 functional stations. "
            "Target race pace. SkiErg 1000m / Sled Push 50m / Sled Pull 50m / "
            "Burpee Broad Jump 80m / Row 1000m / Farmers Carry 200m / "
            "Sandbag Lunges 100m / Wall Balls 100 reps."
        ),
        "duration_min": 90,
        "intensity": "max",
        "notes": "",
        "status": "done",
    },
    {
        "date": "2026-05-19",
        "phase": PHASE,
        "week_number": WEEK_NUMBER - 1,
        "session_type": "Mobility",
        "description": "40-min full-body mobility + cold shower protocol.",
        "duration_min": 40,
        "intensity": "easy",
        "notes": "",
        "status": "done",
    },
]


# ── Nutrition Thu–Sun (21–24 May) ─────────────────────────────────────────────
NUTRITION = [
    {
        "date": "2026-05-21",
        "phase": PHASE,
        "week_number": WEEK_NUMBER,
        "calories": 2550,
        "protein_g": 172,
        "carbs_g": 285,
        "fat_g": 76,
        "meals": (
            "Breakfast: Oats 80g + whey 30g + banana + almond butter 15g\n"
            "Pre-workout (60min before): 2 rice cakes + honey\n"
            "Lunch: Chicken breast 180g + sweet potato 200g + broccoli\n"
            "Post-workout (within 30min): Whey shake 40g + milk 300ml\n"
            "Dinner: Salmon 200g + quinoa 130g + roasted courgette & peppers\n"
            "Snack: Greek yogurt 150g + blueberries"
        ),
        "notes": "Strength day -- fuel well around the session.",
    },
    {
        "date": "2026-05-22",
        "phase": PHASE,
        "week_number": WEEK_NUMBER,
        "calories": 2480,
        "protein_g": 168,
        "carbs_g": 275,
        "fat_g": 74,
        "meals": (
            "Breakfast: 3 eggs scrambled + 2 slices sourdough + half avocado\n"
            "Pre-workout (90min before): Banana + slice toast + peanut butter\n"
            "Lunch: Tuna wrap (1 large tortilla, tuna 150g, salad, light mayo)\n"
            "Post-workout (within 30min): Whey shake 40g\n"
            "Dinner: Ground turkey 200g + pasta 100g + tomato sauce + parmesan\n"
            "Snack: Cottage cheese 150g + peach"
        ),
        "notes": "Pre-wedding Z2 day -- top up glycogen without heavy meals.",
    },
    {
        "date": "2026-05-23",
        "phase": PHASE,
        "week_number": WEEK_NUMBER,
        "calories": 3300,
        "protein_g": 148,
        "carbs_g": 360,
        "fat_g": 112,
        "meals": (
            "Breakfast: Greek yogurt 200g + granola 60g + mixed fruit\n"
            "Pre-workout (60min before): 2 rice cakes + jam (morning mobility)\n"
            "Lunch: Chicken & rice bowl 350g\n"
            "Dinner: Cheat meal -- enjoy freely, no tracking needed. (Wedding reception)"
        ),
        "notes": "Cheat meal day (dinner) -- planned indulgence. Wedding day. Back on track tomorrow morning.",
    },
    {
        "date": "2026-05-24",
        "phase": PHASE,
        "week_number": WEEK_NUMBER,
        "calories": 2050,
        "protein_g": 165,
        "carbs_g": 195,
        "fat_g": 66,
        "meals": (
            "Breakfast: 2 eggs + 2 slices sourdough + avocado\n"
            "Lunch: Lentil soup 400ml + sourdough slice\n"
            "Dinner: Chicken breast 160g + roasted veg + sweet potato 150g\n"
            "Snack: Handful almonds + apple"
        ),
        "notes": "Rest day -- rehydrate after last night. Light, nutrient-dense meals.",
    },
]


def main():
    all_sessions = LAST_WEEK + THIS_WEEK
    start = all_sessions[0]["date"]
    end   = all_sessions[-1]["date"]

    print(f"Deleting existing planned sessions from {start} to {end}…")
    deleted = db.delete_sessions_by_date_range(start, end, status_filter="planned")
    print(f"  → {deleted} planned sessions deleted.")

    print(f"Inserting {len(all_sessions)} sessions…")
    db.insert_sessions(all_sessions)

    nutr_start = NUTRITION[0]["date"]
    nutr_end   = NUTRITION[-1]["date"]
    print(f"Deleting existing nutrition from {nutr_start} to {nutr_end}…")
    db.delete_nutrition_by_date_range(nutr_start, nutr_end)

    print(f"Inserting {len(NUTRITION)} nutrition plans…")
    db.insert_nutrition_plans(NUTRITION)

    print("  → Done. Reload the dashboard to see the data.")


if __name__ == "__main__":
    main()
