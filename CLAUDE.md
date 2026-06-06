# Travel Planner Skill — Project Overview

## What This Project Does

This project builds a **Claude Skill** that generates comprehensive, personalized travel and outing plans for any trip a user describes. Given the number of travelers, destination, trip type, duration, and budget, the skill produces a fully structured plan including: packing lists tailored to destination and season, safety & health notices, a day-by-day timeline with activities, accommodation and transport recommendations, estimated budget breakdown, and emergency contacts.

The skill handles trips of all scales — from a one-day local outing with friends to a multi-week international vacation with family.

## Core Design Principles

- **Harness-first**: every phase is explicitly instructed; the agent never guesses what to do next
- **Input-driven personalization**: group size, age mix, trip type, budget tier all change the output meaningfully
- **Progressive disclosure**: sub-reference files loaded only when needed (packing, safety, budget, activities)
- **Completeness guarantee**: every plan covers all 6 output pillars; none are skipped
- **Actionable output**: every recommendation is specific enough to act on immediately

## Repository Structure

```
travel-planner-skill/
├── CLAUDE.md                              ← You are here
├── PROJECT-detail.md                      ← Full project specification
├── PROJECT-DEVELOPMENT-PHASE-TRACKING.md  ← Live development tracker
├── README.md                              ← Install & quick-start guide
├── skill/
│   ├── SKILL.md                           ← Main skill entrypoint (agent reads this)
│   ├── references/
│   │   ├── packing-library.md             ← Master packing list by category & context
│   │   ├── destination-profiles.md        ← Climate, culture, safety by region
│   │   ├── activity-database.md           ← Activity ideas by trip type & group profile
│   │   ├── budget-guide.md                ← Cost tiers, estimation formulas, currency notes
│   │   └── safety-health-guide.md         ← Health, safety, emergency, visa, insurance
│   ├── scripts/
│   │   ├── classify_trip.py               ← Classify trip type, season, group profile
│   │   ├── build_packing_list.py          ← Generate personalized packing list JSON
│   │   └── estimate_budget.py             ← Estimate budget ranges by tier and group
│   └── assets/
│       └── plan_template.md               ← Final plan skeleton with all sections
└── evals/
    └── evals.json                         ← Test cases for skill validation
```

## Trip Type Taxonomy

| Type | Description | Key Frameworks |
|---|---|---|
| Beach / Resort | Sea, sun, water sports | Packing (swim), Safety (sun/water), Activity (leisure) |
| Mountain / Trekking | Hiking, altitude, nature | Packing (gear), Safety (altitude/weather), Activity (outdoor) |
| City Break | Culture, food, sightseeing | Packing (urban), Safety (city), Activity (cultural) |
| Theme Park / Entertainment | Rides, shows, family fun | Packing (comfort), Safety (family), Activity (scheduled) |
| Road Trip | Self-drive, flexible route | Packing (car), Safety (drive), Activity (route) |
| Camping / Glamping | Outdoor overnight | Packing (camp), Safety (wilderness), Activity (nature) |
| Cruise | Sea-based multi-stop | Packing (formal+casual), Safety (maritime), Activity (port) |
| Cultural / Heritage | History, temples, museums | Packing (modest), Safety (culture), Activity (sightseeing) |
| Adventure / Sports | Extreme sports, diving | Packing (technical), Safety (sport-specific), Activity (adventure) |
| Relaxation / Wellness | Spa, retreat, slow travel | Packing (comfort), Safety (health), Activity (wellness) |

## Skill Workflow Summary

```
User Input
    │
    ▼
[INTAKE] Parse group, destination, dates, budget, preferences
    │
    ▼
[CLARIFY] Ask 2-3 questions if critical info missing
    │
    ▼
[CLASSIFY] Trip type, season, group profile, budget tier
    │
    ▼
[PACKING] Generate tailored packing list by category
    │
    ▼
[SAFETY] Flag health, legal, cultural, emergency notes
    │
    ▼
[ACTIVITIES] Day-by-day timeline with alternatives
    │
    ▼
[BUDGET] Cost breakdown with ranges
    │
    ▼
[PLAN] Render final structured travel plan
```

## Development Environment

- Language: Python 3.10+
- No external API calls required (fully offline)
- Install: `pip install tabulate rich --break-system-packages`
