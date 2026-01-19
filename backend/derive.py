# Imprting functions from shema
from schema import get_empty_garment

# Deriving metadata from raw signals.
def derive_metadata(clip_signals, color_data):

    meta = get_empty_garment()
    
    # Extracting raw scores
    cat_scores = clip_signals.get("category_scores", {})
    subtype_scores = clip_signals.get("subtype_scores", {})
    weight_scores = clip_signals.get("weight_scores", {})
    formality_scores = clip_signals.get("formality_scores", {})
    sleeve_scores = clip_signals.get("sleeve_scores", {})
    weather_scores = clip_signals.get("weather_scores", {})
    color_scores = clip_signals.get("color_scores", {})
    
    # Primary category
    meta["primary_category"] = _derive_category(cat_scores)
    
    # Sleeves length
    meta["sleeve_length"] = _derive_sleeve_length(sleeve_scores)

    # Sub type for _sort_by_priority
    meta["sub_type"] = _derive_sub_type(cat_scores, weight_scores, subtype_scores)
    
    # Layering role
    meta["layering_role"] = _derive_layering(cat_scores, weight_scores)
    
    # Score
    scores = _derive_continuous_scores(weight_scores, sleeve_scores, weather_scores, meta["layering_role"], meta["primary_category"], meta["sleeve_length"])
    meta["insulation_score"] = scores["insulation"]
    meta["breathability_score"] = scores["breathability"]
    meta["weather_protection_score"] = scores["weather_protection"]
    
    # Thermal level
    meta["thermal_level"] = _score_to_thermal_level(meta["insulation_score"])
    
    # Temperature range
    meta["temp_range"] = _compute_adaptive_temp_range(
        insulation_score = meta["insulation_score"],
        breathability_score = meta["breathability_score"],
        layering_role = meta["layering_role"],
        category = meta["primary_category"]
    )
    
    # Seasonality
    meta["seasonality"] = _derive_seasonality(meta["temp_range"])
    
    # Formality levels
    meta["formality_level"] = _derive_formality(formality_scores, meta["sub_type"])
    
    # Weather proof
    meta["rain_safe"] = _derive_rain_safety(weather_scores, meta["layering_role"], meta["weather_protection_score"])
    meta["wind_resistance"] = _derive_wind_resistance(weather_scores, meta["layering_role"], meta["thermal_level"], meta["weather_protection_score"])
    
    # Coverage
    meta["coverage_level"] = _derive_coverage(meta["sleeve_length"], meta["layering_role"])
    
    # Colour family
    meta["color_family"] = color_data.get("color_family", "Neutral")
    
    # Confidence level
    confidence = _calculate_confidence(clip_signals, meta, cat_scores, weight_scores, formality_scores)
    meta["confidence_score"] = confidence["score"]
    meta["confidence_band"] = confidence["band"]
    meta["needs_review"] = confidence["needs_review"]
    
    # Colour role
    from outfit_safety import assign_color_role
    meta["color_role"] = assign_color_role(meta)
    
    # Compatability check
    from outfit_safety import calculate_compatibility_weight
    meta["compatibility_weight"] = calculate_compatibility_weight(meta)
    
    # Debugging
    meta["debug_metadata"] = {
        "raw_clip_scores": clip_signals,
        "primary_rgb": color_data.get("primary_rgb"),
        "derived_scores": scores,
    }
    
    return meta

# Getting primary categories.
def _derive_category(scores):

    if not scores:
        return "Unknown"
    
    label, conf = max(scores.items(), key=lambda x: x[1])
    
    if conf < 0.22:
        return "Unknown"
    
    if "upper body" in label:
        return "Top"
    elif "lower body" in label:
        return "Bottom"
    elif "outerwear" in label or "heavy jacket" in label:
        return "Outerwear"
    elif "footwear" in label:
        return "Footwear"
    
    return "Unknown"

# Getting the length of sleeves.
def _derive_sleeve_length(scores):

    if not scores:
        return "unknown"
    
    sleeveless_score = max(
        (v for k, v in scores.items() if "sleeveless" in k or "no sleeves" in k),
        default=0
    )
    short_score = max(
        (v for k, v in scores.items() if "short sleeves" in k),
        default=0
    )
    long_score = max(
        (v for k, v in scores.items() if "long sleeves" in k or "full coverage" in k),
        default=0
    )
    
    max_score = max(sleeveless_score, short_score, long_score)
    
    if max_score < 0.20:
        return "unknown"
    
    if sleeveless_score == max_score:
        return "sleeveless"
    elif short_score == max_score:
        return "short"
    elif long_score == max_score:
        return "long"
    
    return "unknown"

# Deriving subtypes based on clip_model
def _derive_sub_type(cat_scores, weight_scores, subtype_scores):
    
    if not subtype_scores:
        return "unknown"
    
    # Getting the highest scoring subtype
    label, conf = max(subtype_scores.items(), key=lambda x: x[1])
    
    # Only if reasonable
    if conf < 0.20:
        return "unknown"
    
    # Map CLIP labels to sub_types
    if "hoodie" in label:
        return "hoodie"
    elif "sweatshirt" in label or "pullover" in label or "sweater" in label:
        return "sweatshirt"
    elif "dress shirt" in label or "button-up" in label:
        return "dress_shirt"
    elif "t-shirt" in label or "tee" in label:
        return "tshirt"
    elif "tank top" in label or "sleeveless" in label:
        return "tank"
    
    return "unknown"


# Getting layering data.
def _derive_layering(cat_scores, weight_scores):

    outerwear_score = max(
        (v for k, v in cat_scores.items() if "outerwear" in k or "heavy jacket" in k),
        default=0
    )
    
    if outerwear_score > 0.25:
        return "Outer"
    
    heavy_score = max(
        (v for k, v in weight_scores.items() if "thick heavy" in k),
        default=0
    )
    
    if heavy_score > 0.28:
        return "Mid"
    
    return "Base"

# Deriving main scores for weather proof.
def _derive_continuous_scores(weight_scores, sleeve_scores, weather_scores, layering_role, category, sleeve_length):

    # insulation score
    insulation = _compute_insulation_score(weight_scores, sleeve_length, layering_role)
    
    # Breathable score
    breathability = _compute_breathability_score(weight_scores, sleeve_length, layering_role)
    
    # Protective score
    weather_protection = _compute_weather_protection_score(weather_scores, layering_role)
    
    return {"insulation": insulation, "breathability": breathability, "weather_protection": weather_protection}

# Calculating insulation score.
def _compute_insulation_score(weight_scores, sleeve_length, layering_role):

    base_score = 50.0
    
    # Weight signals
    heavy_score = max(
        (v for k, v in weight_scores.items() if "thick heavy" in k or "insulated" in k or "winter" in k),
        default=0
    )
    light_score = max(
        (v for k, v in weight_scores.items() if "thin lightweight" in k or "summer" in k),
        default=0
    )
    medium_score = max(
        (v for k, v in weight_scores.items() if "medium weight" in k),
        default=0
    )
    
    # Mapping CLIP scores
    if heavy_score > 0.28:
        base_score += 30
    elif heavy_score > 0.22:
        base_score += 20
    
    if light_score > 0.28:
        base_score -= 30
    elif light_score > 0.22:
        base_score -= 20
    
    if medium_score > 0.25:
        base_score += 5
    
    # Sleeve length
    if sleeve_length == "sleeveless":
        base_score -= 15
    elif sleeve_length == "short":
        base_score -= 8
    elif sleeve_length == "long":
        base_score += 8
    
    # Layering
    # Outerwear is warm
    if layering_role == "Outer":
        base_score += 15
    elif layering_role == "Mid":
        base_score += 8
    
    return max(0, min(100, round(base_score, 1)))

# Calculating breathability score
def _compute_breathability_score(weight_scores, sleeve_length, layering_role):

    base_score = 50.0
    
    # Lightweight = breathable
    light_score = max(
        (v for k, v in weight_scores.items() if "thin lightweight" in k or "breathable" in k),
        default=0
    )
    heavy_score = max(
        (v for k, v in weight_scores.items() if "thick heavy" in k or "padded" in k),
        default=0
    )
    
    if light_score > 0.28:
        base_score += 25
    elif light_score > 0.22:
        base_score += 15
    
    if heavy_score > 0.28:
        base_score -= 25
    elif heavy_score > 0.22:
        base_score -= 15
    
    # Sleeve length
    if sleeve_length == "sleeveless":
        base_score += 15
    elif sleeve_length == "short":
        base_score += 8
    elif sleeve_length == "long":
        base_score -= 5
    
    # Base layers usually more breathable
    if layering_role == "Base":
        base_score += 10
    elif layering_role == "Outer":
        base_score -= 10
    
    return max(0, min(100, round(base_score, 1)))

# Calculating weather protection score.
def _compute_weather_protection_score(weather_scores, layering_role):

    base_score = 20.0
    
    # Outer layer more protection.
    if layering_role != "Outer":
        return min(40, base_score)
    
    # Check for weather resistance.
    rain_score = max(
        (v for k, v in weather_scores.items() if "rain" in k or "waterproof" in k),
        default=0
    )
    wind_score = max(
        (v for k, v in weather_scores.items() if "windbreaker" in k or "wind resistant" in k),
        default=0
    )
    regular_score = max(
        (v for k, v in weather_scores.items() if "regular fabric" in k),
        default=0
    )
    
    if rain_score > 0.30:
        base_score += 40
    elif rain_score > 0.22:
        base_score += 25
    
    if wind_score > 0.30:
        base_score += 30
    elif wind_score > 0.22:
        base_score += 15
    
    if regular_score > 0.28:
        base_score -= 10
    
    return max(0, min(100, round(base_score, 1)))

# Converting insulation score to thermal levels.
def _score_to_thermal_level(insulation_score):

    if insulation_score >= 70:
        return "High"
    elif insulation_score >= 40:
        return "Medium"
    else:
        return "Low"

# Calculating adaptive temperature range based on continuous scores.
def _compute_adaptive_temp_range(insulation_score, breathability_score, layering_role, category):
    
    # 0 = 25-40°C (very light)
    # 50 = 10-25°C (medium)
    # 100 = -10-10°C (very warm)
    
    # Calculate base min/max
    base_min = 25 - (insulation_score * 0.35)
    base_max = 40 - (insulation_score * 0.30)
    
    # Adjusting breathability
    breathability_bonus = (breathability_score - 50) * 0.15
    base_max += breathability_bonus
    
    # Layering role adjustments
    if layering_role == "Outer":
        # Outer layers for cold weather
        base_min -= 5
        base_max -= 3
    elif layering_role == "Base":
        # Base layers
        base_min += 3
        base_max += 3
    
    # Category basis.
    if category == "Outerwear":
        base_min -= 3
    elif category == "Bottom":
        # Bottoms less score.
        base_min += 2
        base_max += 2
    
    # Temperature setting.
    t_min = max(-15, min(25, round(base_min)))
    t_max = max(10, min(45, round(base_max)))
    
    if t_max <= t_min:
        t_max = t_min + 8
    
    # Minimum span of 8°C
    if t_max - t_min < 8:
        t_max = t_min + 8
    
    return {"min": int(t_min), "max": int(t_max)}

# Assigning temperature range to seasons.
def _derive_seasonality(temp_range):

    t_min = temp_range["min"]
    t_max = temp_range["max"]
    
    seasons = []
    
    if t_min < 10:
        seasons.append("Winter")
    
    if (t_min < 20 and t_max > 8):
        if "Spring" not in seasons:
            seasons.append("Spring")
        if "Fall" not in seasons:
            seasons.append("Fall")
    
    if t_max > 18:
        seasons.append("Summer")
    
    if t_max - t_min > 25:
        return ["All"]
    
    return seasons if seasons else ["All"]

# Deriving formality scores.
def _derive_formality(formality_scores, sub_type=None):
    if not formality_scores:
        return "Casual"
    
    # Get the highest scoring formality
    label, conf = max(formality_scores.items(), key=lambda x: x[1])
    
    # Need minimum confidence for formality detection
    if conf < 0.18:
        return "Casual"
    
    # Check for formal indicators FIRST (before sub_type override)
    if "formal coat" in label or "peacoat" in label or "trench coat" in label:
        return "Formal"
    if "formal" in label or "professional" in label or "suit" in label:
        return "Formal"
    elif "smart casual" in label or "business casual" in label or "blazer" in label:
        return "Smart-Casual"

    if sub_type in ["hoodie", "sweatshirt", "tshirt", "tank"]:
        # If CLIP detected formal/smart-casual then considering subtype.
        formal_score = max(
            (v for k, v in formality_scores.items() if "formal" in k.lower()),
            default=0
        )
        smart_casual_score = max(
            (v for k, v in formality_scores.items() if "smart casual" in k.lower() or "business casual" in k.lower()),
            default=0
        )
        
        # Otherwise considering clip.
        if formal_score > 0.22 or smart_casual_score > 0.22:
            if formal_score > smart_casual_score:
                return "Formal"
            else:
                return "Smart-Casual"
        else:
            return "Casual"
    
    # Default based on label
    return "Casual"

# Rain resistance using both CLIP signals.
def _derive_rain_safety(scores, layering_role, weather_protection_score):
    
    if layering_role != "Outer":
        return "false"
    
    # Weather protection score as primary signal
    if weather_protection_score >= 60:
        return "true"
    elif weather_protection_score <= 30:
        return "false"
    
    rain_score = max(
        (v for k, v in scores.items() if "rain" in k or "waterproof" in k),
        default=0
    )
    regular_score = max(
        (v for k, v in scores.items() if "regular fabric" in k),
        default=0
    )
    
    if rain_score > 0.32:
        return "true"
    if regular_score > 0.28:
        return "false"
    
    return "unknown"

# Getting wind resistance score.
def _derive_wind_resistance(scores, layering_role, thermal_level, weather_protection_score):

    # Using weather protection score
    if weather_protection_score >= 60:
        return "High"
    elif weather_protection_score >= 40:
        return "Medium"
    elif weather_protection_score < 30:
        return "Low"
    
    # Layering
    if layering_role == "Outer":
        if thermal_level == "High":
            return "Medium"
        return "Medium"
    
    if layering_role == "Mid":
        return "Medium"
    
    return "Low"

# Sleve length usage.
def _derive_coverage(sleeve_length, layering_role):

    if sleeve_length == "sleeveless":
        return "minimal"
    elif sleeve_length == "long" and layering_role == "Outer":
        return "full"
    else:
        return "moderate"

# Calculating total confidence.
def _calculate_confidence(signals, metadata, cat_scores, weight_scores, formality_scores):

    base_conf = signals.get("detection_confidence", 0.0)
    
    # Reduing for unknown category
    if metadata["primary_category"] == "Unknown":
        base_conf *= 0.5
    
    # Reducing for broad temp range.
    temp_range = metadata["temp_range"]
    range_width = temp_range["max"] - temp_range["min"]
    if range_width > 25:
        base_conf *= 0.85
    elif range_width < 8:
        base_conf *= 0.90
    
    # Consistency check: outer layer without decent weather protection
    if metadata["layering_role"] == "Outer":
        if metadata["weather_protection_score"] < 30:
            base_conf *= 0.95
    
    # Clamp to 0-1
    score = max(0.0, min(1.0, base_conf))
    
    # Determining band scores.
    if score >= 0.5:
        band = "High"
        needs_review = False
    elif score >= 0.25:
        band = "Medium"
        needs_review = False
    else:
        band = "Low"
        needs_review = True
    
    return {"score": round(score, 2), "band": band, "needs_review": needs_review, }