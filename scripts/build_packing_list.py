#!/usr/bin/env python3
"""
build_packing_list.py — Personalized Packing List Generator
Part of the travel-planner skill.

Takes trip classification JSON and builds a filtered, categorized packing list.

Usage:
    python build_packing_list.py --classify '{"trip_type":"beach","season":"peak",...}'
    python build_packing_list.py --file classification.json
    python build_packing_list.py --stdin
    python build_packing_list.py --quick --trip beach --season hot --group family_young --days 7

Output (JSON):
    {
        "categories": {
            "Documents & Money": [
                {"item": "Valid passport", "priority": "ESSENTIAL", "note": "6+ months validity required", "per": "person"},
                ...
            ],
            ...
        },
        "summary": {
            "essential_count": 24,
            "recommended_count": 18,
            "optional_count": 8,
            "shared_items": 3
        },
        "markdown": "## 📋 Packing List\n..."
    }
"""

import sys
import json
import argparse


# ─── Master Item Definitions ────────────────────────────────────────────────────

ITEMS = {
    # Format: "item_id": {"text", "priority", "note", "per", "tags": [...]}
    # tags control which trips/seasons/groups include this item

    # ── DOCUMENTS ──
    "passport": {
        "text": "Valid passport",
        "priority": "ESSENTIAL",
        "note": "Check validity — must be valid 6+ months beyond return date",
        "per": "person",
        "tags": ["international"]
    },
    "passport_copy": {
        "text": "Printed + digital copies of passport and visa",
        "priority": "ESSENTIAL",
        "note": "Store copies separately from originals; save to cloud",
        "per": "person",
        "tags": ["international"]
    },
    "bookings_printed": {
        "text": "All booking confirmations (flights, hotel, tours) — printed + offline digital",
        "priority": "ESSENTIAL",
        "note": "Don't rely on internet access at border or check-in",
        "per": "group",
        "tags": ["always"]
    },
    "travel_insurance": {
        "text": "Travel insurance policy document + 24h emergency hotline number",
        "priority": "ESSENTIAL",
        "note": "Photograph the policy and save the hotline offline",
        "per": "person",
        "tags": ["always"]
    },
    "local_currency": {
        "text": "Local currency cash (minimum equivalent of $50–100 per person)",
        "priority": "ESSENTIAL",
        "note": "Get from ATM at destination — better rates than airport exchange",
        "per": "person",
        "tags": ["always"]
    },
    "payment_card_primary": {
        "text": "Primary payment card (notify your bank of travel dates before leaving)",
        "priority": "ESSENTIAL",
        "note": "Visa/Mastercard most accepted internationally",
        "per": "person",
        "tags": ["always"]
    },
    "payment_card_backup": {
        "text": "Backup payment card (different bank/network from primary)",
        "priority": "RECOMMENDED",
        "note": "Keep in a separate bag from primary card",
        "per": "person",
        "tags": ["always"]
    },
    "travel_card_wise": {
        "text": "Wise or Revolut travel money card (loaded with local currency)",
        "priority": "RECOMMENDED",
        "note": "Best exchange rates, low fees — load before departure",
        "per": "person",
        "tags": ["international"]
    },
    "intl_driving_license": {
        "text": "International Driving License",
        "priority": "ESSENTIAL",
        "note": "Required for renting a vehicle in most countries",
        "per": "person",
        "tags": ["road_trip"]
    },
    "emergency_contacts_card": {
        "text": "Emergency contact card (printed, kept in wallet)",
        "priority": "RECOMMENDED",
        "note": "Include: home contact, travel insurance, embassy, blood type, medications",
        "per": "person",
        "tags": ["always"]
    },

    # ── CLOTHING BASE ──
    "underwear": {
        "text": "Underwear × (days + 2)",
        "priority": "ESSENTIAL",
        "note": "Quick-dry fabric if possible",
        "per": "person",
        "tags": ["always"]
    },
    "socks": {
        "text": "Socks × (days + 2) including appropriate type for activities",
        "priority": "ESSENTIAL",
        "per": "person",
        "tags": ["always"]
    },
    "tops": {
        "text": "T-shirts / tops × number of days",
        "priority": "ESSENTIAL",
        "per": "person",
        "tags": ["always"]
    },
    "walking_shoes": {
        "text": "Comfortable walking shoes (broken in before trip)",
        "priority": "ESSENTIAL",
        "note": "New shoes cause blisters — wear them 2–3 weeks before leaving",
        "per": "person",
        "tags": ["always"]
    },
    "light_jacket": {
        "text": "Light jacket or hoodie",
        "priority": "RECOMMENDED",
        "note": "Planes, hotels and malls are often very cold",
        "per": "person",
        "tags": ["always"]
    },
    "smart_casual_outfit": {
        "text": "Smart casual outfit × 1–2",
        "priority": "RECOMMENDED",
        "note": "For nicer dinners, rooftop bars, or dress-code venues",
        "per": "person",
        "tags": ["city", "cultural", "wellness", "cruise"]
    },

    # ── BEACH CLOTHING ──
    "swimwear": {
        "text": "Swimwear × 2",
        "priority": "ESSENTIAL",
        "note": "Two so one can dry while wearing the other",
        "per": "person",
        "tags": ["beach"]
    },
    "rashguard": {
        "text": "Rashguard or UV protective swimwear",
        "priority": "ESSENTIAL",
        "note": "Especially important for children — UV on water is intense",
        "per": "person",
        "tags": ["beach"]
    },
    "flipflops": {
        "text": "Flip-flops / beach sandals with non-slip grip sole",
        "priority": "ESSENTIAL",
        "note": "Reef shoes recommended if snorkeling (sea urchins and coral)",
        "per": "person",
        "tags": ["beach"]
    },
    "sun_hat_beach": {
        "text": "Wide-brim sun hat",
        "priority": "RECOMMENDED",
        "per": "person",
        "tags": ["beach"]
    },
    "sunglasses_beach": {
        "text": "Polarized sunglasses (UV400 minimum)",
        "priority": "RECOMMENDED",
        "per": "person",
        "tags": ["beach"]
    },
    "beach_bag": {
        "text": "Lightweight beach tote bag",
        "priority": "RECOMMENDED",
        "per": "person",
        "tags": ["beach"]
    },

    # ── MOUNTAIN / TREKKING ──
    "hiking_boots": {
        "text": "Waterproof hiking boots with ankle support (broken in before trip)",
        "priority": "ESSENTIAL",
        "note": "The single most important item for any trekking trip — do not wear new boots",
        "per": "person",
        "tags": ["mountain"]
    },
    "hiking_socks": {
        "text": "Moisture-wicking hiking socks × (days + 3)",
        "priority": "ESSENTIAL",
        "note": "Wool or synthetic — cotton causes blisters",
        "per": "person",
        "tags": ["mountain"]
    },
    "trekking_poles": {
        "text": "Trekking poles (collapsible)",
        "priority": "ESSENTIAL",
        "note": "Reduce knee impact by 25% on descents — worth every gram",
        "per": "person",
        "tags": ["mountain"]
    },
    "daypack": {
        "text": "Daypack / hiking backpack (30–50L)",
        "priority": "ESSENTIAL",
        "per": "person",
        "tags": ["mountain"]
    },
    "rain_poncho": {
        "text": "Waterproof rain jacket or poncho",
        "priority": "ESSENTIAL",
        "note": "Mountain weather changes fast — pack even if forecast is sunny",
        "per": "person",
        "tags": ["mountain"]
    },
    "headlamp": {
        "text": "Headlamp with spare batteries",
        "priority": "ESSENTIAL",
        "note": "For early summit starts and emergencies",
        "per": "person",
        "tags": ["mountain", "camping"]
    },
    "offline_maps_device": {
        "text": "Navigation: offline maps downloaded (maps.me, OSMand) + compass",
        "priority": "ESSENTIAL",
        "note": "GPS works without data signal — download maps before leaving WiFi",
        "per": "group",
        "tags": ["mountain"]
    },
    "water_purification": {
        "text": "Water purification tablets or filter (e.g. Sawyer Squeeze)",
        "priority": "RECOMMENDED",
        "note": "For streams and backcountry water sources",
        "per": "group",
        "tags": ["mountain"]
    },
    "emergency_whistle": {
        "text": "Emergency whistle (bright colored)",
        "priority": "ESSENTIAL",
        "note": "3 blasts = international distress signal",
        "per": "person",
        "tags": ["mountain"]
    },
    "altitude_meds": {
        "text": "Altitude sickness medication — Diamox (acetazolamide) — requires prescription",
        "priority": "RECOMMENDED",
        "note": "Discuss with doctor if going above 2500m",
        "per": "person",
        "tags": ["mountain"]
    },

    # ── CAMPING ──
    "sleeping_bag": {
        "text": "Sleeping bag rated to expected night temperature",
        "priority": "ESSENTIAL",
        "note": "Check temperature rating — underestimating is dangerous",
        "per": "person",
        "tags": ["camping"]
    },
    "tent": {
        "text": "Tent (practice setting up before departure)",
        "priority": "ESSENTIAL",
        "note": "Test ALL zips and poles at home — Murphy's Law",
        "per": "group",
        "tags": ["camping"]
    },
    "camp_stove": {
        "text": "Camp stove + fuel canisters + lightweight cookware",
        "priority": "ESSENTIAL",
        "per": "group",
        "tags": ["camping"]
    },
    "camping_knife": {
        "text": "Camping knife / multi-tool",
        "priority": "ESSENTIAL",
        "note": "Cannot fly in carry-on — pack in checked luggage",
        "per": "group",
        "tags": ["camping"]
    },

    # ── ROAD TRIP ──
    "roadside_kit": {
        "text": "Roadside emergency kit: jumper cables, reflective triangle, first aid",
        "priority": "ESSENTIAL",
        "per": "group",
        "tags": ["road_trip"]
    },
    "physical_map": {
        "text": "Physical or fully offline map backup (GPS can fail)",
        "priority": "ESSENTIAL",
        "note": "Download entire route offline on Google Maps or maps.me before leaving",
        "per": "group",
        "tags": ["road_trip"]
    },
    "car_phone_mount": {
        "text": "Car phone mount",
        "priority": "ESSENTIAL",
        "per": "group",
        "tags": ["road_trip"]
    },
    "cooler_snacks": {
        "text": "Cooler box with snacks and drinks",
        "priority": "RECOMMENDED",
        "note": "Saves significant money on motorway stops",
        "per": "group",
        "tags": ["road_trip"]
    },

    # ── TOILETRIES & MEDICATIONS ──
    "prescription_meds": {
        "text": "Prescription medications × (trip days + 3 days extra supply)",
        "priority": "ESSENTIAL",
        "note": "Carry in original labeled packaging; bring doctor's letter for controlled meds",
        "per": "person",
        "tags": ["always"]
    },
    "first_aid_basic": {
        "text": "Basic first aid: bandages, antiseptic wipes, blister plasters",
        "priority": "ESSENTIAL",
        "per": "group",
        "tags": ["always"]
    },
    "pain_relief": {
        "text": "Pain relief — ibuprofen and/or paracetamol",
        "priority": "ESSENTIAL",
        "per": "group",
        "tags": ["always"]
    },
    "anti_diarrhea": {
        "text": "Anti-diarrhea tablets (Imodium/loperamide)",
        "priority": "ESSENTIAL",
        "note": "Essential for any developing-world destination",
        "per": "group",
        "tags": ["always"]
    },
    "ors": {
        "text": "Oral rehydration salts (ORS sachets)",
        "priority": "ESSENTIAL",
        "note": "For traveler's diarrhea or heat exhaustion recovery",
        "per": "group",
        "tags": ["always"]
    },
    "antihistamine": {
        "text": "Antihistamines (for allergies and insect bite relief)",
        "priority": "RECOMMENDED",
        "per": "group",
        "tags": ["always"]
    },
    "motion_sickness": {
        "text": "Motion sickness tablets or patches",
        "priority": "RECOMMENDED",
        "note": "Take 30–60 min before travel to be effective",
        "per": "person",
        "tags": ["cruise", "road_trip", "mountain"]
    },

    # ── SUN & INSECT PROTECTION ──
    "sunscreen_50": {
        "text": "SPF 50+ reef-safe sunscreen (pack more than you think — expensive at beach resorts)",
        "priority": "ESSENTIAL",
        "per": "person",
        "tags": ["beach", "mountain"]
    },
    "sunscreen_general": {
        "text": "SPF 30–50 sunscreen",
        "priority": "RECOMMENDED",
        "per": "person",
        "tags": ["city", "cultural", "wellness"]
    },
    "after_sun": {
        "text": "After-sun lotion or aloe vera gel",
        "priority": "RECOMMENDED",
        "note": "Apply generously each evening to prevent peeling",
        "per": "group",
        "tags": ["beach"]
    },
    "insect_repellent_deet": {
        "text": "DEET 20%+ insect repellent spray or lotion",
        "priority": "ESSENTIAL",
        "note": "Dengue mosquitoes bite day AND night — apply every 3–4 hours",
        "per": "person",
        "tags": ["southeast_asia", "camping", "mountain", "adventure"]
    },

    # ── ELECTRONICS ──
    "phone_charger": {
        "text": "Phone charger + charging cable",
        "priority": "ESSENTIAL",
        "per": "person",
        "tags": ["always"]
    },
    "power_adapter": {
        "text": "Universal power adapter (check destination voltage: 110V vs 220V)",
        "priority": "ESSENTIAL",
        "note": "Some devices only work at one voltage — check before plugging in",
        "per": "person",
        "tags": ["international"]
    },
    "power_bank": {
        "text": "Portable power bank (10,000mAh minimum)",
        "priority": "RECOMMENDED",
        "note": "10,000mAh = ~2–3 full phone charges; 20,000mAh for multi-day trekking",
        "per": "person",
        "tags": ["always"]
    },
    "waterproof_phone_case": {
        "text": "Waterproof phone case or dry bag",
        "priority": "RECOMMENDED",
        "note": "For beach, boat trips, water sports, and rainy weather",
        "per": "person",
        "tags": ["beach", "adventure", "camping"]
    },
    "action_cam": {
        "text": "Action camera (GoPro or similar) with mounts + extra batteries",
        "priority": "OPTIONAL",
        "per": "group",
        "tags": ["beach", "mountain", "adventure"]
    },

    # ── SAFETY ──
    "passport_copies_separate": {
        "text": "Copies of passport/ID stored separately from originals",
        "priority": "ESSENTIAL",
        "per": "person",
        "tags": ["international"]
    },
    "personal_alarm": {
        "text": "Personal safety alarm or whistle",
        "priority": "RECOMMENDED",
        "note": "Especially for solo travelers and women",
        "per": "person",
        "tags": ["solo"]
    },
    "luggage_lock": {
        "text": "Small padlock (for hostel lockers or luggage security)",
        "priority": "RECOMMENDED",
        "per": "person",
        "tags": ["always"]
    },
    "door_stopper_alarm": {
        "text": "Door stopper alarm (for budget hotel / hostel room security)",
        "priority": "RECOMMENDED",
        "note": "Provides noise alert + physical resistance if door is forced",
        "per": "person",
        "tags": ["solo"]
    },
    "anti_theft_bag": {
        "text": "Anti-theft crossbody bag or daypack (with lockable zippers)",
        "priority": "RECOMMENDED",
        "note": "Pickpocketing risk in crowded tourist areas worldwide",
        "per": "person",
        "tags": ["city", "cultural"]
    },

    # ── FAMILY WITH KIDS ──
    "child_id_wristband": {
        "text": "Child ID wristbands with parent's phone number",
        "priority": "ESSENTIAL",
        "note": "Write phone number in permanent marker — for crowded places",
        "per": "child",
        "tags": ["family_young"]
    },
    "children_pain_relief": {
        "text": "Children's pain relief (correct weight-based dosage confirmed with pharmacist)",
        "priority": "ESSENTIAL",
        "per": "group",
        "tags": ["family_young"]
    },
    "children_sunscreen": {
        "text": "Children's SPF 50+ sunscreen (zinc-based, fragrance-free)",
        "priority": "ESSENTIAL",
        "note": "Children's skin is more UV-sensitive than adults",
        "per": "child",
        "tags": ["family_young"]
    },
    "wet_wipes": {
        "text": "Wet wipes × 3+ packs",
        "priority": "ESSENTIAL",
        "note": "Always bring more than you think",
        "per": "group",
        "tags": ["family_young"]
    },
    "child_entertainment": {
        "text": "Downloaded shows, games, audiobooks on tablet/phone for transport",
        "priority": "RECOMMENDED",
        "note": "Download BEFORE travel — no WiFi on planes",
        "per": "child",
        "tags": ["family_young", "family_teens"]
    },
    "familiar_snacks": {
        "text": "Familiar snacks from home for fussy eaters",
        "priority": "RECOMMENDED",
        "note": "Reassuring for young children in unfamiliar food environments",
        "per": "group",
        "tags": ["family_young"]
    },

    # ── LARGE GROUP ──
    "group_first_aid": {
        "text": "Full group first aid kit (larger than individual kit)",
        "priority": "RECOMMENDED",
        "per": "group",
        "tags": ["large_group"]
    },
    "power_strip": {
        "text": "Power strip with USB ports (shared group charging station)",
        "priority": "RECOMMENDED",
        "note": "One strip charges 6+ devices vs scrambling for sockets",
        "per": "group",
        "tags": ["large_group"]
    },
    "group_contact_list": {
        "text": "Printed group emergency contact list (every member's number + home contact)",
        "priority": "RECOMMENDED",
        "per": "group",
        "tags": ["large_group"]
    },

    # ── CULTURAL / RELIGIOUS SITES ──
    "modest_clothing": {
        "text": "Modest clothing: tops covering shoulders, bottoms covering knees",
        "priority": "ESSENTIAL",
        "note": "Required at temples, mosques, churches — enforceable at entrance",
        "per": "person",
        "tags": ["cultural", "middle_east"]
    },
    "scarf_sarong": {
        "text": "Lightweight scarf or sarong (for quick cover-up at religious sites)",
        "priority": "ESSENTIAL",
        "note": "Often available to borrow/buy at site entrances — but bring your own",
        "per": "person",
        "tags": ["cultural", "southeast_asia", "middle_east"]
    },
    "slip_on_shoes": {
        "text": "Slip-on shoes or sandals (easy removal at temples)",
        "priority": "RECOMMENDED",
        "note": "Shoes must be removed at most temples and mosques — laces slow you down",
        "per": "person",
        "tags": ["cultural", "southeast_asia"]
    },

    # ── SEASON: WET / RAINY ──
    "waterproof_jacket": {
        "text": "Waterproof jacket (actual rain protection — not just a light layer)",
        "priority": "ESSENTIAL",
        "per": "person",
        "tags": ["wet_season"]
    },
    "waterproof_bag_cover": {
        "text": "Waterproof backpack cover or dry bag for electronics",
        "priority": "ESSENTIAL",
        "per": "person",
        "tags": ["wet_season"]
    },

    # ── SEASON: COLD / WINTER ──
    "thermal_base_layer": {
        "text": "Thermal base layer — top and bottom",
        "priority": "ESSENTIAL",
        "per": "person",
        "tags": ["cold_season", "mountain"]
    },
    "insulated_jacket": {
        "text": "Insulated mid-layer (down or fleece jacket)",
        "priority": "ESSENTIAL",
        "per": "person",
        "tags": ["cold_season"]
    },
    "warm_accessories": {
        "text": "Warm hat, gloves, and scarf",
        "priority": "ESSENTIAL",
        "per": "person",
        "tags": ["cold_season"]
    },
    "winter_boots": {
        "text": "Waterproof insulated boots",
        "priority": "ESSENTIAL",
        "per": "person",
        "tags": ["cold_season"]
    },
}

# ─── Tag Resolution ─────────────────────────────────────────────────────────────

TAG_ALWAYS = "always"

def get_applicable_tags(classification: dict) -> set:
    """Build a set of tags that apply to this specific trip."""
    tags = {TAG_ALWAYS}
    tags.add(classification.get("trip_type", "city"))
    tags.add(classification.get("group_profile", "friends"))
    tags.add(classification.get("destination_region", ""))

    season = classification.get("season", "shoulder")
    if season == "off_peak":
        tags.add("wet_season")
    elif season == "peak" and classification.get("trip_type") in ("beach",):
        pass  # peak beach = hot, already covered by beach tag

    if "has_kids" in classification.get("special_flags", []):
        tags.add("family_young")
    if "has_elderly" in classification.get("special_flags", []):
        tags.add("mixed_ages")
    if "large_group" in classification.get("special_flags", []):
        tags.add("large_group")
    if "international" in classification.get("special_flags", []):
        tags.add("international")
    if "solo" in classification.get("group_profile", ""):
        tags.add("solo")

    return tags


# ─── Packing List Builder ───────────────────────────────────────────────────────

CATEGORY_ORDER = [
    "Documents & Money",
    "Clothing & Footwear",
    "Toiletries & Medication",
    "Sun & Insect Protection",
    "Electronics & Accessories",
    "Trip-Specific Gear",
    "Safety & Emergency",
    "Group / Family Specific",
]

ITEM_TO_CATEGORY = {
    "passport": "Documents & Money",
    "passport_copy": "Documents & Money",
    "bookings_printed": "Documents & Money",
    "travel_insurance": "Documents & Money",
    "local_currency": "Documents & Money",
    "payment_card_primary": "Documents & Money",
    "payment_card_backup": "Documents & Money",
    "travel_card_wise": "Documents & Money",
    "intl_driving_license": "Documents & Money",
    "emergency_contacts_card": "Documents & Money",
    "passport_copies_separate": "Documents & Money",

    "underwear": "Clothing & Footwear",
    "socks": "Clothing & Footwear",
    "tops": "Clothing & Footwear",
    "walking_shoes": "Clothing & Footwear",
    "light_jacket": "Clothing & Footwear",
    "smart_casual_outfit": "Clothing & Footwear",
    "swimwear": "Trip-Specific Gear",
    "rashguard": "Trip-Specific Gear",
    "flipflops": "Trip-Specific Gear",
    "sun_hat_beach": "Trip-Specific Gear",
    "sunglasses_beach": "Trip-Specific Gear",
    "beach_bag": "Trip-Specific Gear",
    "hiking_boots": "Trip-Specific Gear",
    "hiking_socks": "Clothing & Footwear",
    "trekking_poles": "Trip-Specific Gear",
    "daypack": "Trip-Specific Gear",
    "rain_poncho": "Clothing & Footwear",
    "headlamp": "Trip-Specific Gear",
    "offline_maps_device": "Trip-Specific Gear",
    "water_purification": "Trip-Specific Gear",
    "emergency_whistle": "Safety & Emergency",
    "altitude_meds": "Toiletries & Medication",
    "sleeping_bag": "Trip-Specific Gear",
    "tent": "Trip-Specific Gear",
    "camp_stove": "Trip-Specific Gear",
    "camping_knife": "Trip-Specific Gear",
    "roadside_kit": "Trip-Specific Gear",
    "physical_map": "Trip-Specific Gear",
    "car_phone_mount": "Electronics & Accessories",
    "cooler_snacks": "Trip-Specific Gear",
    "modest_clothing": "Clothing & Footwear",
    "scarf_sarong": "Clothing & Footwear",
    "slip_on_shoes": "Clothing & Footwear",
    "waterproof_jacket": "Clothing & Footwear",
    "waterproof_bag_cover": "Electronics & Accessories",
    "thermal_base_layer": "Clothing & Footwear",
    "insulated_jacket": "Clothing & Footwear",
    "warm_accessories": "Clothing & Footwear",
    "winter_boots": "Clothing & Footwear",

    "prescription_meds": "Toiletries & Medication",
    "first_aid_basic": "Toiletries & Medication",
    "pain_relief": "Toiletries & Medication",
    "anti_diarrhea": "Toiletries & Medication",
    "ors": "Toiletries & Medication",
    "antihistamine": "Toiletries & Medication",
    "motion_sickness": "Toiletries & Medication",

    "sunscreen_50": "Sun & Insect Protection",
    "sunscreen_general": "Sun & Insect Protection",
    "after_sun": "Sun & Insect Protection",
    "insect_repellent_deet": "Sun & Insect Protection",

    "phone_charger": "Electronics & Accessories",
    "power_adapter": "Electronics & Accessories",
    "power_bank": "Electronics & Accessories",
    "waterproof_phone_case": "Electronics & Accessories",
    "action_cam": "Electronics & Accessories",

    "personal_alarm": "Safety & Emergency",
    "luggage_lock": "Safety & Emergency",
    "door_stopper_alarm": "Safety & Emergency",
    "anti_theft_bag": "Safety & Emergency",

    "child_id_wristband": "Group / Family Specific",
    "children_pain_relief": "Group / Family Specific",
    "children_sunscreen": "Group / Family Specific",
    "wet_wipes": "Group / Family Specific",
    "child_entertainment": "Group / Family Specific",
    "familiar_snacks": "Group / Family Specific",
    "group_first_aid": "Group / Family Specific",
    "power_strip": "Group / Family Specific",
    "group_contact_list": "Group / Family Specific",
}


def build_list(classification: dict) -> dict:
    applicable_tags = get_applicable_tags(classification)
    categories: dict[str, list] = {cat: [] for cat in CATEGORY_ORDER}

    for item_id, item in ITEMS.items():
        item_tags = set(item.get("tags", []))
        if item_tags & applicable_tags:  # intersection
            category = ITEM_TO_CATEGORY.get(item_id, "Trip-Specific Gear")
            entry = {
                "item": item["text"],
                "priority": item["priority"],
                "per": item.get("per", "person"),
            }
            if item.get("note"):
                entry["note"] = item["note"]
            categories[category].append(entry)

    # Remove empty categories
    categories = {k: v for k, v in categories.items() if v}

    # Sort each category: ESSENTIAL first, then RECOMMENDED, then OPTIONAL
    priority_order = {"ESSENTIAL": 0, "RECOMMENDED": 1, "OPTIONAL": 2}
    for cat in categories:
        categories[cat].sort(key=lambda x: priority_order.get(x["priority"], 3))

    # Stats
    all_items = [i for lst in categories.values() for i in lst]
    essential = sum(1 for i in all_items if i["priority"] == "ESSENTIAL")
    recommended = sum(1 for i in all_items if i["priority"] == "RECOMMENDED")
    optional = sum(1 for i in all_items if i["priority"] == "OPTIONAL")
    shared = sum(1 for i in all_items if i.get("per") == "group")

    # Generate markdown
    md = generate_markdown(categories)

    return {
        "categories": categories,
        "summary": {
            "essential_count": essential,
            "recommended_count": recommended,
            "optional_count": optional,
            "shared_items": shared,
            "total_items": len(all_items),
        },
        "markdown": md
    }


def generate_markdown(categories: dict) -> str:
    priority_emoji = {"ESSENTIAL": "🔴", "RECOMMENDED": "🟡", "OPTIONAL": "🟢"}
    lines = ["## 📋 Packing List", ""]
    lines.append("| Priority | Item | Note |")
    lines.append("|---|---|---|")

    for cat, items in categories.items():
        if not items:
            continue
        lines.append(f"| **{cat}** | | |")
        for item in items:
            emoji = priority_emoji.get(item["priority"], "⚪")
            per = f" _{item['per']}_" if item.get("per") == "group" else ""
            note = item.get("note", "")
            text = f"{item['item']}{per}"
            lines.append(f"| {emoji} **{item['priority']}** | {text} | {note} |")

    return "\n".join(lines)


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate personalized packing list.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--classify", type=str, help="Classification JSON string")
    group.add_argument("--file", type=str, help="Path to classification JSON file")
    group.add_argument("--stdin", action="store_true")
    group.add_argument("--quick", action="store_true", help="Use --trip --season --group flags")

    parser.add_argument("--trip", type=str, default="city")
    parser.add_argument("--season", type=str, default="shoulder")
    parser.add_argument("--group", type=str, default="friends")
    parser.add_argument("--days", type=int, default=4)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--markdown-only", action="store_true")

    args = parser.parse_args()

    if args.quick:
        classification = {
            "trip_type": args.trip,
            "season": args.season,
            "group_profile": args.group,
            "days": args.days,
            "special_flags": ["international"],
            "destination_region": "southeast_asia"
        }
    elif args.classify:
        try:
            classification = json.loads(args.classify)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"Invalid JSON: {e}"}))
            sys.exit(1)
    elif args.file:
        import pathlib
        classification = json.loads(pathlib.Path(args.file).read_text())
    else:
        classification = json.loads(sys.stdin.read())

    result = build_list(classification)

    if args.markdown_only:
        print(result["markdown"])
    else:
        indent = 2 if args.pretty else None
        print(json.dumps(result, indent=indent))


if __name__ == "__main__":
    main()
