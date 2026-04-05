from collections import defaultdict

def build_summary(cleaned_classified_items):
    total_spent = 0

    category_map = defaultdict(int)

    mandatory_spend = 0
    optional_spend = 0
    avoidable_spend = 0

    healthy_count = 0
    unhealthy_count = 0

    for item in cleaned_classified_items:
        amount = item.get("amount", 0)
        category = item.get("category", "Unknown")

        total_spent += amount
        category_map[category] += amount

        # mandatory vs optional
        if item.get("is_mandatory", False):
            mandatory_spend += amount
        else:
            optional_spend += amount

        # avoidable
        if item.get("can_be_avoided", False):
            avoidable_spend += amount

        # health
        if item.get("is_healthy", False):
            healthy_count += 1
        else:
            unhealthy_count += 1

    # top category
    top_category = max(category_map, key=category_map.get) if category_map else None

    # risk flags
    high_avoidable_spend = avoidable_spend > (0.5 * total_spent)
    high_optional_spend = optional_spend > (0.5 * total_spent)

    summary = {
        "total_spent": total_spent,
        "categories": dict(category_map),
        "mandatory_spend": mandatory_spend,
        "optional_spend": optional_spend,
        "avoidable_spend": avoidable_spend,
        "healthy_count": healthy_count,
        "unhealthy_count": unhealthy_count,
        "top_category": top_category,
        "insights": {
            "high_avoidable_spend": high_avoidable_spend,
            "high_optional_spend": high_optional_spend
        }
    }

    return summary