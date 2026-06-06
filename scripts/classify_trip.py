#!/usr/bin/env python3
"""
classify_trip.py — Trip Classification Script
Part of the travel-planner skill.

Classifies a trip from user input text or structured JSON into:
- trip_type, season, group_profile, budget_tier, special_flags

Usage:
    python classify_trip.py --text "4 days beach trip to Bali for 8 friends"
    python classify_trip.py --json '{"destination":"Bali","days":4,"group_size":8}'
    python classify_trip.py --stdin

Output (JSON):
    {
        "trip_type": "beach",
        "season": "shoulder",
        "group_profile": "friends",
        "budget_tier": "mid",
        "destination_region": "southeast_asia",
        "special_flags": ["large_group"],
        "days": 4,
        "group_size": 8,
        "confidence": "high",
        "assumptions": ["budget assumed mid-range (not stated)"]
    }
"""

import sys
import json
import argparse
import re
from datetime import datetime


# ─── Signal Dictionaries ────────────────────────────────────────────────────────

TRIP_TYPE_SIGNALS = {
    "beach": {
        "keywords": ["beach", "sea", "ocean", "coastal", "island", "surf", "snorkel",
                     "dive", "diving", "scuba", "reef", "swimm", "resort", "sun",
                     "sand", "bali", "phuket", "samui", "boracay", "maldives",
                     "cancun", "hawaii", "coast"],
        "weight": 1.0
    },
    "mountain": {
        "keywords": ["mountain", "trek", "trekking", "hike", "hiking", "trail",
                     "summit", "peak", "altitude", "camp", "camping", "national park",
                     "everest", "himalaya", "alps", "patagonia", "kilimanjaro",
                     "backpack", "wilderness", "nature", "forest"],
        "weight": 1.0
    },
    "city": {
        "keywords": ["city", "urban", "museum", "gallery", "restaurant", "food",
                     "culture", "street", "market", "shopping", "nightlife",
                     "paris", "tokyo", "london", "nyc", "new york", "singapore",
                     "bangkok", "rome", "barcelona", "berlin", "architecture"],
        "weight": 1.0
    },
    "theme_park": {
        "keywords": ["theme park", "disneyland", "disney", "universal", "legoland",
                     "ride", "roller coaster", "amusement", "waterpark",
                     "six flags", "busch gardens", "sea world"],
        "weight": 1.5  # higher weight — very specific keyword
    },
    "road_trip": {
        "keywords": ["road trip", "drive", "driving", "car", "route", "highway",
                     "road", "rental car", "campervan", "rv", "pit stop"],
        "weight": 1.2
    },
    "camping": {
        "keywords": ["camp", "camping", "glamping", "tent", "bonfire", "outdoor",
                     "campsite", "rv", "caravan", "overnight", "backcountry"],
        "weight": 1.0
    },
    "cruise": {
        "keywords": ["cruise", "ship", "yacht", "sailing", "port", "deck",
                     "mediterranean cruise", "caribbean cruise", "river cruise"],
        "weight": 1.5
    },
    "cultural": {
        "keywords": ["temple", "heritage", "history", "historical", "ancient",
                     "monument", "ruins", "museum", "art", "culture", "local",
                     "tradition", "pilgrimage", "spiritual", "religious"],
        "weight": 1.0
    },
    "adventure": {
        "keywords": ["adventure", "extreme", "bungee", "skydive", "rafting",
                     "kayak", "paraglide", "via ferrata", "canyoning",
                     "zip line", "sport", "adrenaline"],
        "weight": 1.2
    },
    "wellness": {
        "keywords": ["spa", "wellness", "yoga", "meditation", "retreat",
                     "relax", "relaxation", "rest", "detox", "rejuvenate",
                     "massage", "hot spring", "thermal"],
        "weight": 1.2
    }
}

GROUP_PROFILE_SIGNALS = {
    "solo": ["solo", "alone", "by myself", "just me", "1 person", "one person"],
    "couple": ["couple", "two of us", "2 people", "partner", "wife", "husband",
               "girlfriend", "boyfriend", "honeymoon", "anniversary", "romantic"],
    "friends": ["friends", "buddy", "buddies", "crew", "gang", "group of friends",
                "mates", "classmates", "college", "uni"],
    "family_young": ["kids", "children", "child", "toddler", "baby", "infant",
                     "family", "son", "daughter", "age 1", "age 2", "age 3",
                     "age 4", "age 5", "age 6", "age 7", "age 8", "age 9",
                     "age 10", "age 11"],
    "family_teens": ["teen", "teenager", "adolescent", "age 12", "age 13",
                     "age 14", "age 15", "age 16", "age 17"],
    "mixed_ages": ["grandparent", "grandma", "grandpa", "elderly", "senior",
                   "multi-generation", "all ages", "different ages"],
    "corporate": ["team", "company", "office", "corporate", "colleague",
                  "work trip", "team building", "staff", "employees", "outing"]
}

BUDGET_SIGNALS = {
    "budget": ["budget", "cheap", "backpack", "hostel", "affordable",
               "low cost", "frugal", "shoestring", "economy"],
    "mid": ["mid-range", "moderate", "comfortable", "3 star", "normal",
            "reasonable", "standard"],
    "comfort": ["comfort", "4 star", "boutique", "nice", "quality",
                "premium", "semi-luxury"],
    "luxury": ["luxury", "5 star", "five star", "high-end", "exclusive",
               "lavish", "splurge", "first class", "suite", "villa"]
}

DESTINATION_REGIONS = {
    "southeast_asia": ["thailand", "bali", "indonesia", "vietnam", "cambodia",
                       "myanmar", "laos", "philippines", "malaysia", "singapore",
                       "phuket", "samui", "ho chi minh", "hanoi", "bangkok",
                       "chiang mai", "kuala lumpur", "kl", "danang", "hoi an",
                       "ubud", "lombok", "komodo"],
    "east_asia": ["japan", "korea", "china", "taiwan", "hong kong", "tokyo",
                  "osaka", "kyoto", "seoul", "beijing", "shanghai", "taipei"],
    "south_asia": ["india", "nepal", "sri lanka", "maldives", "delhi", "mumbai",
                   "jaipur", "goa", "kathmandu", "colombo"],
    "middle_east": ["dubai", "uae", "jordan", "morocco", "egypt", "turkey",
                    "israel", "petra", "cairo", "marrakech", "istanbul"],
    "europe": ["paris", "france", "italy", "rome", "spain", "barcelona", "madrid",
               "germany", "berlin", "london", "uk", "amsterdam", "netherlands",
               "portugal", "lisbon", "greece", "athens", "santorini", "croatia",
               "prague", "budapest", "switzerland", "austria", "scandinavia",
               "norway", "sweden"],
    "americas": ["usa", "new york", "los angeles", "miami", "chicago", "las vegas",
                 "mexico", "cancun", "canada", "toronto", "vancouver",
                 "brazil", "rio", "argentina", "buenos aires", "peru", "machu picchu",
                 "colombia", "costa rica"],
    "africa": ["south africa", "kenya", "tanzania", "safari", "morocco",
               "marrakech", "egypt", "cape town", "johannesburg", "nairobi"],
    "oceania": ["australia", "new zealand", "sydney", "melbourne", "queensland",
                "bora bora", "fiji", "queenstown"]
}

SEASON_BY_REGION_MONTH = {
    "southeast_asia": {
        (11, 12, 1, 2, 3, 4): "peak",
        (5, 6): "shoulder",
        (7, 8, 9, 10): "off_peak"
    },
    "east_asia": {
        (3, 4, 5, 9, 10, 11): "peak",  # Cherry blossom + autumn
        (6, 7, 8): "off_peak",  # Hot and humid
        (12, 1, 2): "shoulder"
    },
    "europe": {
        (6, 7, 8): "peak",
        (4, 5, 9, 10): "shoulder",
        (11, 12, 1, 2, 3): "off_peak"
    },
    "americas": {
        (6, 7, 8): "peak",
        (3, 4, 5, 9, 10): "shoulder",
        (11, 12, 1, 2): "off_peak"
    },
    "default": {
        "all": "shoulder"  # Unknown destination defaults to shoulder
    }
}

SPECIAL_FLAG_SIGNALS = {
    "has_kids": ["kid", "child", "children", "baby", "infant", "toddler", "son", "daughter"],
    "has_elderly": ["elderly", "senior", "grandparent", "grandma", "grandpa", "old"],
    "dietary": ["vegetarian", "vegan", "halal", "kosher", "gluten", "allergy",
                "allergic", "dietary"],
    "medical": ["wheelchair", "disability", "medical condition", "chronic",
                "heart", "diabetic", "asthma", "pregnant"],
    "international": [],  # derived from destination region
    "domestic": [],       # derived from destination region
    "large_group": [],    # derived from group_size >= 10
    "single_day": ["day trip", "day out", "one day", "1 day", "afternoon",
                   "half day", "few hours"]
}


# ─── Utility Functions ──────────────────────────────────────────────────────────

def normalize(text: str) -> str:
    return text.lower().strip()


def score_signals(text: str, signal_dict: dict) -> tuple[str, int, list[str]]:
    """Return (best_match_key, score, matched_signals)."""
    normalized = normalize(text)
    scores = {}
    matched = {}

    for key, signals in signal_dict.items():
        keywords = signals if isinstance(signals, list) else signals.get("keywords", [])
        weight = signals.get("weight", 1.0) if isinstance(signals, dict) else 1.0
        score = 0
        found = []
        for kw in keywords:
            if kw in normalized:
                score += weight
                found.append(kw)
        scores[key] = score
        matched[key] = found

    if not scores:
        return "unknown", 0, []

    best = max(scores, key=lambda k: scores[k])
    return best, scores[best], matched[best]


def extract_number(text: str, patterns: list[str]) -> int | None:
    """Extract first number matching any of the given regex patterns."""
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except (IndexError, ValueError):
                pass
    return None


def extract_days(text: str) -> int | None:
    patterns = [
        r"(\d+)\s*days?",
        r"(\d+)\s*nights?",
        r"(\d+)-day",
        r"(\d+)-night",
        r"day\s+(\d+)",
    ]
    return extract_number(text, patterns)


def extract_group_size(text: str) -> int | None:
    patterns = [
        r"(\d+)\s*(?:people|persons?|travelers?|pax|adults?|friends?|of us)",
        r"group\s+of\s+(\d+)",
        r"(\d+)\s+(?:of us|going)",
        r"party\s+of\s+(\d+)",
    ]
    return extract_number(text, patterns)


def detect_destination(text: str) -> tuple[str, str]:
    """Returns (destination_text, region_key)."""
    normalized = normalize(text)
    for region, keywords in DESTINATION_REGIONS.items():
        for kw in keywords:
            if kw in normalized:
                return kw, region
    return "unknown", "unknown"


def estimate_season(region: str, month: int | None) -> str:
    if month is None:
        return "shoulder"  # default assumption

    region_seasons = SEASON_BY_REGION_MONTH.get(region)
    if not region_seasons:
        return "shoulder"

    for month_tuple, season in region_seasons.items():
        if isinstance(month_tuple, tuple) and month in month_tuple:
            return season

    return "shoulder"


def extract_travel_month(text: str) -> int | None:
    """Try to find a month from the text."""
    months = {
        "january": 1, "jan": 1, "february": 2, "feb": 2,
        "march": 3, "mar": 3, "april": 4, "apr": 4,
        "may": 5, "june": 6, "jun": 6,
        "july": 7, "jul": 7, "august": 8, "aug": 8,
        "september": 9, "sep": 9, "october": 10, "oct": 10,
        "november": 11, "nov": 11, "december": 12, "dec": 12,
    }
    normalized = normalize(text)
    for name, num in months.items():
        if name in normalized:
            return num

    # Also check MM/DD or YYYY-MM-DD patterns
    m = re.search(r"\b(\d{4})-(\d{2})-", text)
    if m:
        try:
            return int(m.group(2))
        except ValueError:
            pass

    return None


def classify(text: str) -> dict:
    assumptions = []

    # Trip type
    trip_type, trip_score, trip_signals = score_signals(text, TRIP_TYPE_SIGNALS)
    if trip_score == 0:
        trip_type = "city"  # default
        assumptions.append("trip type assumed 'city break' (no clear signals)")

    # Group profile
    group_key, group_score, group_signals = score_signals(text, GROUP_PROFILE_SIGNALS)
    group_size = extract_group_size(text)

    if group_size is not None and group_size >= 16 and group_key not in ("corporate",):
        group_key = "large_group"
    elif group_size == 1:
        group_key = "solo"
    elif group_size == 2 and group_key not in ("family_young", "family_teens"):
        group_key = "couple"
    elif group_score == 0:
        group_key = "friends"
        assumptions.append("group profile assumed 'friends' (no clear signals)")

    # Budget
    budget_key, budget_score, _ = score_signals(text, BUDGET_SIGNALS)
    if budget_score == 0:
        budget_key = "mid"
        assumptions.append("budget assumed 'mid-range' (not stated)")

    # Destination + region
    destination, region = detect_destination(text)
    if destination == "unknown":
        assumptions.append("destination not recognized — using general regional defaults")

    # Season
    month = extract_travel_month(text)
    if month is None:
        month = datetime.now().month
        assumptions.append(f"travel month assumed current month ({datetime.now().strftime('%B')})")
    season = estimate_season(region, month)

    # Days
    days = extract_days(text)
    if days is None:
        days = 4
        assumptions.append("trip duration assumed 4 days (not stated)")

    # Special flags
    normalized = normalize(text)
    special_flags = []
    for flag, signals in SPECIAL_FLAG_SIGNALS.items():
        if signals and any(s in normalized for s in signals):
            special_flags.append(flag)

    if group_size is not None and group_size >= 10:
        special_flags.append("large_group")
    if region not in ("unknown",) and region != "domestic":
        special_flags.append("international")
    if days == 1 or "day trip" in normalized or "day out" in normalized:
        special_flags.append("single_day")

    # Confidence
    has_destination = destination != "unknown"
    has_days = extract_days(text) is not None
    has_group = extract_group_size(text) is not None
    data_points = sum([has_destination, has_days, has_group, trip_score > 0, budget_score > 0])
    confidence = "high" if data_points >= 4 else "medium" if data_points >= 2 else "low"

    return {
        "trip_type": trip_type,
        "season": season,
        "group_profile": group_key,
        "budget_tier": budget_key,
        "destination": destination,
        "destination_region": region,
        "travel_month": month,
        "days": days,
        "group_size": group_size,
        "special_flags": list(set(special_flags)),
        "confidence": confidence,
        "assumptions": assumptions,
        "signals": {
            "trip_type": trip_signals,
            "group": group_signals
        }
    }


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Classify a travel request into structured trip attributes.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str)
    group.add_argument("--json", type=str, help="Pre-structured JSON with destination, days, group_size etc.")
    group.add_argument("--stdin", action="store_true")
    parser.add_argument("--pretty", action="store_true")

    args = parser.parse_args()

    if args.text:
        text = args.text
    elif args.json:
        # If given structured JSON, convert to text for uniform processing
        try:
            data = json.loads(args.json)
            parts = []
            if "destination" in data:
                parts.append(data["destination"])
            if "days" in data:
                parts.append(f"{data['days']} days")
            if "group_size" in data:
                parts.append(f"{data['group_size']} people")
            if "trip_type" in data:
                parts.append(data["trip_type"])
            if "budget" in data:
                parts.append(data["budget"])
            if "group_composition" in data:
                parts.append(data["group_composition"])
            text = " ".join(parts)
            # Merge structured data back in
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON input"}))
            sys.exit(1)
    else:
        text = sys.stdin.read()

    if not text.strip():
        print(json.dumps({"error": "Empty input"}))
        sys.exit(1)

    result = classify(text)
    indent = 2 if args.pretty else None
    print(json.dumps(result, indent=indent))


if __name__ == "__main__":
    main()
