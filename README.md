# travel-planner — Agent Skill

Generate a complete, personalized travel plan for any trip or outing — from a one-day local outing to a multi-week international journey.

## What It Does

Given destination, duration, group size, and trip type, this skill produces a full trip plan covering all 6 pillars:

1. **📋 Packing List** — tailored to trip type, season, group profile, and destination
2. **⚠️ Safety & Health** — visa, vaccinations, local laws, emergency contacts, local phrases
3. **📅 Day-by-Day Timeline** — morning/afternoon/evening structure with rainy-day alternatives
4. **💰 Budget Breakdown** — per-person and group total with category split
5. **💡 Tips & Logistics** — apps, SIM, neighborhoods, transport, insider tips
6. **❌ What NOT To Do** — common tourist mistakes for this specific destination

## Quick Start

Just describe your trip naturally:

> "Plan a 4-day beach trip to Phuket for 8 friends, mid-range budget"
> "Family trip to Vietnam 6 days with 3 kids aged 4, 7, 10"
> "Solo trekking Annapurna Base Camp 7 days, tight budget"
> "Corporate outing for 30 people to Vung Tau, 1 day"
> "Romantic 5-day Tokyo trip for our anniversary"

## File Structure

```
travel-planner-skill/
├── CLAUDE.md                              ← Project overview
├── PROJECT-detail.md                      ← Full specification
├── PROJECT-DEVELOPMENT-PHASE-TRACKING.md ← Dev phase tracker
├── README.md                              ← This file
├── skill/
│   ├── SKILL.md                           ← Main harness (8 phases)
│   ├── references/
│   │   ├── packing-library.md             ← Master packing lists
│   │   ├── destination-profiles.md        ← 20+ destination profiles
│   │   ├── activity-database.md           ← Activities by trip type
│   │   ├── budget-guide.md                ← Cost estimation reference
│   │   └── safety-health-guide.md         ← Health, safety, laws
│   ├── scripts/
│   │   ├── classify_trip.py               ← Trip classification
│   │   ├── build_packing_list.py          ← Packing list generator
│   │   └── estimate_budget.py             ← Budget estimator
│   └── assets/
│       └── plan_template.md               ← 6-pillar report skeleton
└── evals/
    └── evals.json                         ← 6 test cases, 30 assertions
```

## Trip Types Supported

Beach · Mountain/Trekking · City Break · Theme Park · Road Trip · Camping · Cruise · Cultural/Heritage · Adventure/Sports · Wellness/Spa

## Group Profiles Supported

Solo · Couple · Friend Group · Large Group (16+) · Family (Young Kids) · Family (Teens) · Mixed Ages · Corporate Team

## Script Dependencies

```bash
pip install --break-system-packages  # no external deps required — stdlib only
```

All three scripts use Python standard library only.

## Script Usage Examples

```bash
# Classify a trip
python skill/scripts/classify_trip.py --pretty --text "8 friends beach trip Phuket 4 days December"

# Generate packing list
python skill/scripts/build_packing_list.py --quick --trip beach --season peak --group friends --days 4 --markdown-only

# Estimate budget
python skill/scripts/estimate_budget.py --quick --group 8 --days 4 --tier mid --region southeast_asia --markdown-only
```

## Version

v1.0.0 — Initial release
