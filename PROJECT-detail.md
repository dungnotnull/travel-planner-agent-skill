# PROJECT-detail.md — Travel Planner Skill

## 1. Project Vision

Build a reusable Claude Skill that, given any trip description, automatically generates a **complete, personalized travel plan** covering every dimension a traveler needs to prepare, execute, and enjoy their trip safely. The output should be good enough to be shared directly in a WhatsApp group or printed as a trip handbook.

---

## 2. Problem Statement

When people plan a trip — especially group trips — they face:

- **Forgotten essentials**: Someone always forgets sunscreen, a plug adapter, or motion sickness pills
- **No structured timeline**: Activities are figured out on the day, leading to wasted time and missed highlights
- **Safety blind spots**: Visa requirements, local health risks, water safety, emergency numbers — usually Googled last minute
- **Budget drift**: No upfront estimate means surprise overspending
- **Group coordination chaos**: No shared reference document means repeated WhatsApp questions

This skill solves all of the above in one pass.

---

## 3. Target Users

| User | Example Use Case |
|---|---|
| Friend group organizer | Plan a 4-day beach trip for 8 people |
| Family trip planner | 2-week Southeast Asia trip with kids aged 5 and 10 |
| Solo adventurer | 3-day solo mountain trek in unfamiliar area |
| Corporate team outing | 1-day company trip for 30 employees |
| Couple | Weekend city break in a new country |
| Backpacker | Low-budget 10-day multi-city trip |

---

## 4. Input Specifications

### 4.1 Required Inputs
- **Destination**: City, country, or region
- **Duration**: Number of days / dates
- **Group size**: Number of people
- **Trip type**: What kind of trip (beach, city, mountain, etc.) — inferred if not stated

### 4.2 Optional Inputs (improve output quality)
- **Group composition**: Ages, physical fitness, special needs (children, elderly, disabilities)
- **Budget tier**: Budget (backpacker), Mid-range, Luxury — inferred from context if not stated
- **Interests**: Food, history, adventure, nightlife, nature, shopping, etc.
- **Starting location**: For travel time and transport recommendations
- **Accommodation preference**: Hostel, hotel, resort, Airbnb, camping
- **Known constraints**: Dietary restrictions, mobility limitations, visa issues

### 4.3 Input Mode Detection
- **Mode A — Full input**: User provides most details → proceed directly to classification
- **Mode B — Partial input**: Key details missing → ask 2–3 targeted questions
- **Mode C — Conversational**: User describes trip casually → extract what's there, ask for the rest

---

## 5. Group Profile Classification

The skill classifies the group into a profile that drives all downstream decisions:

| Profile | Definition | Key Adjustments |
|---|---|---|
| Solo | 1 person | Safety emphasis, solo-friendly activities, flexible timeline |
| Couple | 2 people, adults | Romantic options, couple pricing, shared accommodation |
| Friend Group | 3–15 adults | Group dynamics, splitting costs, nightlife options |
| Large Group | 16+ adults | Logistics focus, group bookings, coordination tips |
| Family (Young Kids) | Any group with children < 12 | Kid-friendly activities, safety, medical kit emphasis |
| Family (Teens) | Any group with teens 12–17 | Mix of teen + adult activities, some independence |
| Mixed Ages | Multi-generation | Accessible activities, pacing, rest considerations |
| Corporate | Work team | Team building focus, professional logistics |

---

## 6. Trip Classification System

After receiving inputs, the skill runs `scripts/classify_trip.py` to determine:

### 6.1 Trip Type (Primary)
One of: Beach, Mountain/Trek, City Break, Theme Park, Road Trip, Camping, Cruise, Cultural/Heritage, Adventure/Sports, Relaxation/Wellness

### 6.2 Season Classification
Based on destination + travel dates:
- **Dry Season / Peak**: Best weather, crowded, expensive
- **Shoulder Season**: Good weather, fewer crowds, better value
- **Wet Season / Off-Peak**: Rain risk, cheapest, some closures
- **Winter / Cold**: Cold weather gear, indoor activity bias

### 6.3 Budget Tier
- **Budget (< $50/person/day)**: Hostels, street food, public transport, free activities
- **Mid-range ($50–$150/person/day)**: 3-star hotels, local restaurants, some paid attractions
- **Comfort ($150–$300/person/day)**: 4-star hotels, curated dining, private transport
- **Luxury ($300+/person/day)**: 5-star, private guides, premium experiences

---

## 7. Output Pillars (All 6 Required in Every Plan)

### Pillar 1: Trip Overview
- Destination summary (what it is, why people go)
- Best time to visit vs. user's travel dates
- Group profile summary and key considerations
- Trip type and estimated pace (relaxed / moderate / packed)

### Pillar 2: Packing List
Generated from `references/packing-library.md` using:
- Base list (universally needed for any trip)
- Trip-type additions (beach gear, hiking boots, formal dinner wear, etc.)
- Season/weather additions (rain gear, sun protection, warm layers, etc.)
- Group-specific additions (baby items, teen entertainment, group first aid, etc.)
- Destination-specific additions (plug adapters, local SIM, mosquito repellent, etc.)

Categories:
- Documents & Money
- Clothing & Footwear
- Toiletries & Medication
- Electronics & Accessories
- Entertainment & Extras
- Safety & Emergency
- Destination-Specific Items

### Pillar 3: Safety & Health Notices
Generated from `references/safety-health-guide.md`:
- Visa and entry requirements
- Vaccinations recommended
- Food and water safety
- Health risks (sun, altitude, insects, etc.)
- Local laws and cultural norms to respect
- Scam and safety alerts for the destination
- Emergency contacts (local police, ambulance, nearest hospital, embassy)
- Travel insurance recommendation
- Emergency phrase card (3–5 phrases in local language)

### Pillar 4: Day-by-Day Timeline
Generated from `references/activity-database.md`:
- One section per day
- Morning / Afternoon / Evening structure
- Activity name + duration + cost estimate + booking required? + tips
- Meals: Recommended restaurant or food type for each meal slot
- Transport: How to get between activities
- Flexibility notes: What to skip if pressed for time
- Alternative: Rainy day / budget version of the day

### Pillar 5: Budget Breakdown
Generated from `references/budget-guide.md` + `scripts/estimate_budget.py`:
- Total estimated cost per person and for whole group
- Breakdown by category:
  - Flights / Transport to destination
  - Accommodation (per night × nights)
  - Daily activities (entrance fees, tours, etc.)
  - Food & drink (per day estimate)
  - Local transport (taxi, bus, metro)
  - Shopping / souvenirs buffer
  - Emergency buffer (10%)
- Currency note: local currency, exchange rate tip, best way to pay

### Pillar 6: Practical Tips & Logistics
- Best apps to download (maps, transport, translation, booking)
- SIM card / data recommendation
- Accommodation area recommendation (which neighborhood to stay in and why)
- Transport from airport/station to accommodation
- Group coordination tips (if group trip)
- 3 "insider" tips specific to the destination
- What NOT to do (common tourist mistakes)

---

## 8. Skill Workflow — Detailed Harness

### Phase 0: INPUT INTAKE
```
1. Parse user input for: destination, duration, group size, trip type, dates, budget, interests
2. Run classify_trip.py to get: trip_type, season, group_profile, budget_tier
3. Identify missing critical fields
4. Output: intake_summary.json
```

### Phase 1: CLARIFICATION (conditional)
```
IF destination OR duration OR group_size is missing:
  Ask: "To build your perfect plan, I need a few details:"
  Max 3 questions, numbered, asked together in one message
  Wait for response
ELSE:
  State extracted info and proceed, flagging any assumptions made
```

### Phase 2: CLASSIFICATION
```
Load destination profile from references/destination-profiles.md
Determine:
  - Trip type (primary + secondary if applicable)
  - Season + weather context
  - Group profile
  - Budget tier
  - Special considerations (kids, elderly, dietary, medical)
Output: classification_summary (shown to user as brief intro)
```

### Phase 3: PACKING LIST GENERATION
```
Load references/packing-library.md
Run build_packing_list.py with classification inputs
Generate categorized packing list:
  - Mark items as ESSENTIAL / RECOMMENDED / OPTIONAL
  - For groups: note shared items (bring 1 per group vs 1 per person)
  - For families: flag which items are per-child
```

### Phase 4: SAFETY & HEALTH BRIEF
```
Load references/safety-health-guide.md
Pull destination-specific and trip-type-specific warnings
Generate:
  - Visa/entry requirements (with official source note)
  - Health alerts and vaccinations
  - Local laws/cultural norms
  - Emergency contacts
  - Safety tips specific to trip type
  - 5 local language phrases
```

### Phase 5: TIMELINE GENERATION
```
Load references/activity-database.md
Calculate: number of days, pace preference, group energy
For each day:
  - Select 3–5 activities (morning/afternoon/evening)
  - Include meal recommendations
  - Estimate time and cost per activity
  - Add transport notes between activities
  - Include rainy-day alternative for each day
```

### Phase 6: BUDGET ESTIMATION
```
Load references/budget-guide.md
Run estimate_budget.py with: group_size, days, budget_tier, destination
Generate:
  - Per-person cost estimate (low / mid / high range)
  - Total group cost
  - Category breakdown
  - Money-saving tips for this specific trip
```

### Phase 7: PLAN ASSEMBLY
```
Load assets/plan_template.md
Assemble all 6 pillars into the final structured plan
Add: Trip title, emoji-rich section headers, quick-glance summary box at top
Format for sharing (WhatsApp-friendly sections, clear headers)
```

---

## 9. Output Format

The final plan uses this structure:
```
# 🌏 [Trip Title]: [Destination] — [Duration] with [Group Description]

## ✈️ Quick Glance
[3-line summary: when, who, vibe]

## 📋 Packing List
[By category with ESSENTIAL / RECOMMENDED / OPTIONAL markers]

## ⚠️ Safety & Health
[Notices, emergency contacts, local phrases]

## 📅 Day-by-Day Plan
[Day 1, Day 2, ... with morning/afternoon/evening]

## 💰 Budget Breakdown
[Per person and total with category split]

## 💡 Tips & Logistics
[Apps, SIM, neighborhoods, insider tips, what not to do]
```

---

## 10. Quality Criteria

1. Packing list is specific (not generic — "SPF 50 reef-safe sunscreen" not just "sunscreen")
2. Timeline is realistic (travel time between places accounted for)
3. Safety notes are destination-specific (not copy-paste warnings)
4. Budget matches stated tier (budget plan doesn't recommend luxury restaurants)
5. Group profile is reflected throughout (kids plan ≠ friend group plan for same destination)
6. Every plan has at least one "non-obvious" local tip

---

## 11. Edge Cases

| Situation | Handling |
|---|---|
| Destination not recognized | Ask user to clarify; apply general regional guidance |
| Group > 20 people | Flag logistics complexity; add group booking and coordination section |
| Very young children (< 3) | Add infant essentials section; flag activity suitability |
| Medical conditions mentioned | Add "consult your doctor" notice; flag relevant safety items |
| Budget not stated | Default to mid-range; note assumption prominently |
| Dates not stated | Ask for approximate timing; ask about dry/wet season preference |
| Single-day outing | Skip accommodation pillar; compress to half-day timeline |
| Domestic trip | Skip visa/vaccination section; keep local safety + packing |
