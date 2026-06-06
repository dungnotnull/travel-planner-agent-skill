#!/usr/bin/env python3
"""
estimate_budget.py — Travel Budget Estimator
Part of the travel-planner skill.

Usage:
    python estimate_budget.py --group 8 --days 4 --tier mid --region southeast_asia
    python estimate_budget.py --json '{"group_size":8,"days":4,"budget_tier":"mid","destination_region":"southeast_asia"}'
    python estimate_budget.py --stdin

Output (JSON):
    {
        "per_person": {"low": 280, "mid": 380, "high": 520},
        "total_group": {"low": 2240, "mid": 3040, "high": 4160},
        "breakdown": { ... category-level estimates ... },
        "currency_note": "Thai Baht (THB) — approx. 35 THB/USD",
        "money_tips": [...],
        "markdown_table": "...",
        "assumptions": [...]
    }
"""

import sys
import json
import argparse


# ─── Base Daily Cost Ranges (USD/person/day) ────────────────────────────────────

TIER_DAILY = {
    "budget": {
        "accommodation": (5, 15),    # hostel dorm
        "food": (8, 18),
        "local_transport": (2, 6),
        "activities": (5, 15),
        "misc": (3, 8),
    },
    "mid": {
        "accommodation": (25, 60),   # 3-star, room split 2 pax
        "food": (20, 40),
        "local_transport": (8, 18),
        "activities": (15, 35),
        "misc": (8, 18),
    },
    "comfort": {
        "accommodation": (70, 150),  # 4-star
        "food": (40, 80),
        "local_transport": (20, 45),
        "activities": (35, 70),
        "misc": (15, 30),
    },
    "luxury": {
        "accommodation": (180, 400),
        "food": (80, 200),
        "local_transport": (60, 150),
        "activities": (80, 200),
        "misc": (30, 80),
    },
}

# ─── Regional Cost Multipliers ──────────────────────────────────────────────────

REGION_MULTIPLIER = {
    "southeast_asia": 0.45,
    "south_asia": 0.35,
    "east_asia": 1.10,   # Japan/Korea
    "middle_east": 1.40,
    "europe": 1.60,
    "americas": 1.50,
    "africa": 0.75,
    "oceania": 1.65,
    "unknown": 1.00,     # default: no adjustment
}

REGION_CURRENCY = {
    "southeast_asia": "varies by country (THB ~35/USD in Thailand; VND ~25,000/USD in Vietnam; IDR ~16,000/USD in Indonesia)",
    "south_asia": "varies (INR ~83/USD; NPR ~133/USD; LKR ~300/USD)",
    "east_asia": "varies (JPY ~150/USD; KRW ~1,350/USD)",
    "middle_east": "varies (AED 3.67/USD fixed; JOD 0.71/USD; MAD ~10/USD)",
    "europe": "EUR ~0.93/USD (Eurozone); GBP ~0.79/USD (UK)",
    "americas": "USD in USA; MXN ~17/USD in Mexico; varies in South America",
    "africa": "varies (ZAR ~18/USD; MAD ~10/USD)",
    "oceania": "AUD ~1.55/USD; NZD ~1.65/USD",
    "unknown": "USD — check xe.com for current rates",
}

REGION_MONEY_TIPS = {
    "southeast_asia": [
        "Use ATMs at destination (7-Eleven ATMs in Thailand, Agribank in Vietnam) — expect $3–5 fee per withdrawal",
        "Carry cash: most local restaurants, tuk-tuks, and markets are cash-only",
        "Avoid airport money changers — their rates are 5–10% worse than city ATMs",
    ],
    "east_asia": [
        "Japan is heavily cash-based — 7-Eleven and Japan Post ATMs accept foreign cards",
        "Load a Suica/Pasmo (Japan) or T-money (Korea) transit card at the airport",
        "Cards are increasingly accepted in cities; carry ¥10,000–20,000 cash at all times in Japan",
    ],
    "europe": [
        "Tap-to-pay (contactless) is near-universal — keep one contactless card handy",
        "No-fee cards (Wise, Revolut, Starling) save significantly vs standard foreign transaction fees",
        "Keep €50–100 cash for street markets, small cafés, and smaller towns",
    ],
    "americas": [
        "US: tip 18–22% at restaurants and bars — this is not optional, it forms most server wages",
        "Mexico: avoid Cambio booths at airports — use bank ATMs in the city",
        "Split payments with Venmo/PayPal (US) or transfer apps for group cost sharing",
    ],
    "default": [
        "Load a Wise or Revolut card with local currency before departure for best rates",
        "Notify your bank before travel to avoid your card being blocked for suspicious foreign activity",
        "Always have a backup payment method in a separate bag from your primary card and cash",
    ]
}

GROUP_ACCOMMODATION_SAVING = {
    1: 0.0,    # solo — full room cost
    2: 0.5,    # couple — split room 50/50
    3: 0.45,
    4: 0.42,
    5: 0.40,
    6: 0.38,
    8: 0.35,
    10: 0.32,
    15: 0.28,
    20: 0.25,
    30: 0.22,
}


def get_accommodation_factor(group_size: int) -> float:
    """Return per-person accommodation cost factor based on room sharing."""
    if group_size <= 1:
        return 1.0
    sizes = sorted(GROUP_ACCOMMODATION_SAVING.keys())
    for size in sizes:
        if group_size <= size:
            return 1 - GROUP_ACCOMMODATION_SAVING[size]
    return 1 - GROUP_ACCOMMODATION_SAVING[30]  # max group saving


def estimate(group_size: int, days: int, budget_tier: str, region: str) -> dict:
    assumptions = []

    if budget_tier not in TIER_DAILY:
        budget_tier = "mid"
        assumptions.append("Budget tier defaulted to 'mid-range'")

    if region not in REGION_MULTIPLIER:
        region = "unknown"
        assumptions.append("Region not recognized — using global average costs (no multiplier)")

    base = TIER_DAILY[budget_tier]
    multiplier = REGION_MULTIPLIER[region]
    accom_factor = get_accommodation_factor(group_size)

    breakdown = {}
    total_low_pp = 0
    total_high_pp = 0

    # Accommodation (per person per night, adjusted for sharing)
    accom_low = base["accommodation"][0] * multiplier * accom_factor
    accom_high = base["accommodation"][1] * multiplier * accom_factor
    accom_total_low = accom_low * days
    accom_total_high = accom_high * days
    breakdown["accommodation"] = {
        "label": f"🏨 Accommodation ({days} nights)",
        "per_person_low": round(accom_total_low),
        "per_person_high": round(accom_total_high),
        "note": f"Per person assuming room sharing ({group_size} travelers)"
    }
    total_low_pp += accom_total_low
    total_high_pp += accom_total_high

    # Food & drink
    food_low = base["food"][0] * multiplier * days
    food_high = base["food"][1] * multiplier * days
    breakdown["food"] = {
        "label": "🍜 Food & Drink",
        "per_person_low": round(food_low),
        "per_person_high": round(food_high),
        "note": "All meals + drinks per person"
    }
    total_low_pp += food_low
    total_high_pp += food_high

    # Local transport
    transport_low = base["local_transport"][0] * multiplier * days
    transport_high = base["local_transport"][1] * multiplier * days
    # Group saves on shared taxis
    if group_size >= 4:
        transport_low *= 0.75
        transport_high *= 0.80
    breakdown["local_transport"] = {
        "label": "🚗 Local Transport",
        "per_person_low": round(transport_low),
        "per_person_high": round(transport_high),
        "note": "Metro, taxi, grab, tuk-tuk within destination"
    }
    total_low_pp += transport_low
    total_high_pp += transport_high

    # Activities
    activities_low = base["activities"][0] * multiplier * days
    activities_high = base["activities"][1] * multiplier * days
    breakdown["activities"] = {
        "label": "🎯 Activities & Entrance Fees",
        "per_person_low": round(activities_low),
        "per_person_high": round(activities_high),
        "note": "Tours, entry tickets, experiences"
    }
    total_low_pp += activities_low
    total_high_pp += activities_high

    # Flights — rough estimate based on region and budget tier
    flight_estimates = {
        "budget": {"southeast_asia": (80, 300), "europe": (200, 600), "americas": (200, 700),
                   "east_asia": (300, 800), "default": (150, 500)},
        "mid": {"southeast_asia": (200, 600), "europe": (400, 1000), "americas": (400, 900),
                "east_asia": (500, 1200), "default": (300, 800)},
        "comfort": {"southeast_asia": (400, 900), "europe": (600, 1400), "americas": (600, 1200),
                    "east_asia": (700, 1500), "default": (500, 1200)},
        "luxury": {"southeast_asia": (800, 3000), "europe": (1200, 5000), "americas": (1000, 4000),
                   "east_asia": (1200, 5000), "default": (1000, 4000)},
    }
    flight_range = flight_estimates.get(budget_tier, flight_estimates["mid"])
    fl = flight_range.get(region, flight_range.get("default", (300, 800)))
    breakdown["flights"] = {
        "label": "✈️ Return Flights",
        "per_person_low": fl[0],
        "per_person_high": fl[1],
        "note": "Economy return — book 6–8 weeks ahead for best prices"
    }
    total_low_pp += fl[0]
    total_high_pp += fl[1]
    assumptions.append("Flight estimates are very rough — use Google Flights or Skyscanner for actual prices")

    # Misc (shopping, souvenirs)
    misc_pp = round(base["misc"][0] * multiplier * days)
    misc_high_pp = round(base["misc"][1] * multiplier * days)
    breakdown["misc"] = {
        "label": "🛍️ Shopping & Souvenirs",
        "per_person_low": misc_pp,
        "per_person_high": misc_high_pp,
        "note": "Optional buffer — adjust to your shopping habits"
    }
    total_low_pp += misc_pp
    total_high_pp += misc_high_pp

    # Emergency buffer (10%)
    buffer_low = round(total_low_pp * 0.10)
    buffer_high = round(total_high_pp * 0.10)
    breakdown["emergency_buffer"] = {
        "label": "🆘 Emergency Buffer (10%)",
        "per_person_low": buffer_low,
        "per_person_high": buffer_high,
        "note": "Do not skip — covers delays, medical, unexpected costs"
    }
    total_low_pp += buffer_low
    total_high_pp += buffer_high

    # Totals
    total_low_pp = round(total_low_pp)
    total_high_pp = round(total_high_pp)

    # Currency
    currency_note = REGION_CURRENCY.get(region, REGION_CURRENCY["unknown"])
    money_tips = REGION_MONEY_TIPS.get(region, REGION_MONEY_TIPS["default"])

    # Markdown table
    md = generate_markdown_table(breakdown, total_low_pp, total_high_pp, group_size, currency_note)

    return {
        "per_person": {"low": total_low_pp, "mid": round((total_low_pp + total_high_pp) / 2), "high": total_high_pp},
        "total_group": {
            "low": total_low_pp * group_size,
            "mid": round((total_low_pp + total_high_pp) / 2) * group_size,
            "high": total_high_pp * group_size
        },
        "breakdown": breakdown,
        "currency_note": currency_note,
        "money_tips": money_tips,
        "markdown_table": md,
        "assumptions": assumptions,
        "inputs": {
            "group_size": group_size,
            "days": days,
            "budget_tier": budget_tier,
            "region": region,
        }
    }


def generate_markdown_table(breakdown: dict, total_low: int, total_high: int,
                             group_size: int, currency_note: str) -> str:
    lines = [
        "## 💰 Budget Breakdown",
        "",
        f"> _All amounts in USD. Estimates only — actual costs vary. Currency: {currency_note}_",
        "",
        "| Category | Per Person (Low) | Per Person (High) | Notes |",
        "|---|---|---|---|",
    ]

    for item in breakdown.values():
        low = f"${item['per_person_low']:,}"
        high = f"${item['per_person_high']:,}"
        note = item.get("note", "")
        lines.append(f"| {item['label']} | {low} | {high} | {note} |")

    lines.append(f"| **💵 TOTAL (per person)** | **${total_low:,}** | **${total_high:,}** | Incl. flights + buffer |")
    lines.append(f"| **💵 TOTAL (group of {group_size})** | **${total_low * group_size:,}** | **${total_high * group_size:,}** | |")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Estimate travel budget by group size, duration, and tier.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--json", type=str)
    group.add_argument("--stdin", action="store_true")
    group.add_argument("--quick", action="store_true")

    parser.add_argument("--group", type=int, default=4)
    parser.add_argument("--days", type=int, default=4)
    parser.add_argument("--tier", type=str, default="mid")
    parser.add_argument("--region", type=str, default="southeast_asia")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--markdown-only", action="store_true")

    args = parser.parse_args()

    if args.quick:
        data = {"group_size": args.group, "days": args.days, "budget_tier": args.tier, "destination_region": args.region}
    elif args.json:
        try:
            data = json.loads(args.json)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": str(e)}))
            sys.exit(1)
    else:
        data = json.loads(sys.stdin.read())

    result = estimate(
        group_size=data.get("group_size", 4),
        days=data.get("days", 4),
        budget_tier=data.get("budget_tier", "mid"),
        region=data.get("destination_region", "unknown"),
    )

    if args.markdown_only:
        print(result["markdown_table"])
    else:
        indent = 2 if args.pretty else None
        print(json.dumps(result, indent=indent))


if __name__ == "__main__":
    main()
