# Outfit recommending system.
# Importing required files.
from database import get_all_garments
from outfit_safety import (select_best_outfit, validate_color_rules, validate_formality_match, create_weather_profile, score_outfit)

# Recommending a daily outfit.
def recommend_daily_outfit(temperature_celsius, weather_condition="sunny", event_formality="casual"):
    # Getting all the garments.
    all_garments = get_all_garments()
    
    if not all_garments:
        return {
            "error": "No garments in wardrobe. Please upload some clothes first."
        }
    
    # Separating by category.
    tops = [g for g in all_garments if g.get("primary_category") == "Top"]
    bottoms = [g for g in all_garments if g.get("primary_category") == "Bottom"]
    outerwear = [g for g in all_garments if g.get("primary_category") == "Outerwear"]
    
    if not tops or not bottoms:
        return {
            "error": "Insufficient wardrobe. Need at least one top and one bottom."
        }
    
    # Weather profile
    weather_profile = create_weather_profile(temperature_celsius, weather_condition)
    
    # Filtering by insulation scores.
    tops_filtered, tops_fallback = _filter_by_insulation_smart(tops, weather_profile)
    bottoms_filtered, bottoms_fallback = _filter_by_insulation_smart(bottoms, weather_profile)
    outerwear_filtered, outerwear_fallback = _filter_by_insulation_smart(outerwear, weather_profile)
    
    # Use filtered results.
    tops = tops_filtered if tops_filtered else tops_fallback
    bottoms = bottoms_filtered if bottoms_filtered else bottoms_fallback
    outerwear = outerwear_filtered if outerwear_filtered else outerwear_fallback
    
    # Weather condition filtering
    if weather_profile["is_wet"]:
        # Choosing rain-safe outerwear
        rain_safe_outer = [o for o in outerwear if o.get("rain_safe") == "true"]
        if rain_safe_outer:
            outerwear = rain_safe_outer
        else:
            maybe_safe = [o for o in outerwear if o.get("rain_safe") != "false"]
            if maybe_safe:
                outerwear = maybe_safe
    
    # Outerwear for cold conditions.
    need_outerwear = (
        temperature_celsius < 18 or 
        weather_profile["is_wet"] or
        weather_profile["is_windy"]
    )
    
    # Extreme cold conditions.
    if weather_profile["is_extreme_cold"]:
        if not outerwear:
            return {
                "error": f"No suitable outerwear for {temperature_celsius}°C. This is dangerously cold!",
                "suggestion": "Please add warm jackets/coats to your wardrobe."
            }
        need_outerwear = True
    
    if weather_profile["is_very_cold"]:
        if not outerwear:
            return {
                "error": f"No suitable outerwear for {temperature_celsius}°C. This is too cold without a jacket!",
                "suggestion": "Please add jackets or coats to your wardrobe."
            }
        need_outerwear = True
    
    # Removing condition.
    if not need_outerwear:
        outerwear = []
    
    # Recommending basedd on confidence.
    tops = _sort_by_priority(tops, weather_profile, "Top")
    bottoms = _sort_by_priority(bottoms, weather_profile, "Bottom")
    outerwear = _sort_by_priority(outerwear, weather_profile, "Outerwear")
    
    # Selecting best outfit
    best_outfit = select_best_outfit(
        tops = tops,
        bottoms = bottoms,
        outerwear_items = outerwear,
        temperature_celsius = temperature_celsius,
        event_formality = event_formality,
        weather_condition = weather_condition
    )
    
    if not best_outfit:
        return {"error": "No suitable outfit found for these conditions.",
            "suggestion": "Try adding more versatile clothing items to your wardrobe."
        }
    
    # Formatting response
    return {
        "outfit": {
            "top": _format_garment(best_outfit["top"]),
            "bottom": _format_garment(best_outfit["bottom"]),
            "outerwear": _format_garment(best_outfit["outerwear"]) if best_outfit["outerwear"] else None
        },

        "score": best_outfit["score"],
        "reasoning": best_outfit["reasoning"],
        "weather": {
            "temperature": temperature_celsius,
            "condition": weather_condition,
            "profile": weather_profile
        },

        "event": {
            "formality": event_formality
        },

        "safety_checks": {
            "color_rules_passed": validate_color_rules([
                best_outfit["top"], 
                best_outfit["bottom"], 
                best_outfit["outerwear"]
            ]),

            "formality_matched": validate_formality_match([
                best_outfit["top"], 
                best_outfit["bottom"], 
                best_outfit["outerwear"]
            ], event_formality),

            "avg_confidence": round(sum(
                g.get("confidence_score", 0) 
                for g in [best_outfit["top"], best_outfit["bottom"], best_outfit["outerwear"]] 
                if g
            ) / 3, 2),

            "temperature_appropriate": _check_temp_appropriateness(
                [best_outfit["top"], best_outfit["bottom"], best_outfit["outerwear"]],
                weather_profile
            )
        }
    }

# Filtering by insulation scores.
def _filter_by_insulation_smart(garments, weather_profile):

    if not garments:
        return [], []
    
    temp = weather_profile["temperature"]
    
    # Calculating ideal insulation for different temperature
    ideal_insulation = max(0, min(100, 95 - (temp * 2.5)))
    
    strict_matches = []
    close_matches = []
    acceptable_matches = []
    all_sorted = []
    
    for g in garments:
        insulation = g.get("insulation_score", 50)
        distance = abs(insulation - ideal_insulation)
        
        if distance <= 15:
            # Perfect
            strict_matches.append((g, distance))
        elif distance <= 25:
            # Close
            close_matches.append((g, distance))
        elif distance <= 35:
            # ok
            acceptable_matches.append((g, distance))
        else:
            # Not good.
            all_sorted.append((g, distance))
    
    # Sorting each tier
    strict_matches.sort(key=lambda x: x[1])
    close_matches.sort(key=lambda x: x[1])
    acceptable_matches.sort(key=lambda x: x[1])
    all_sorted.sort(key=lambda x: x[1])
    
    # Returning strict matches.
    if strict_matches:
        strict_result = [g for g, dist in strict_matches]
    elif close_matches:
        strict_result = [g for g, dist in close_matches]
    elif acceptable_matches:
        strict_result = [g for g, dist in acceptable_matches]
    else:
        strict_result = []
    
    # Returning closest items.
    num_fallback = max(2, len(garments) // 2)
    fallback_result = [g for g, dist in all_sorted[:num_fallback]]
    
    return strict_result, fallback_result

# Soriting by priority.
def _sort_by_priority(garments, weather_profile, category):
    if not garments:
        return []
    
    temp = weather_profile["temperature"]
    is_extreme_cold = weather_profile["is_extreme_cold"]
    is_very_cold = weather_profile["is_very_cold"]
    is_wet = weather_profile["is_wet"]
    
    # Calculating ideal insulation
    ideal_insulation = max(0, min(100, 95 - (temp * 2.5)))

    def base_layer_type_multiplier(g):
        if g.get("primary_category") != "Top":
            return 1.0
        
        garment_type = g.get("sub_type", "").lower()
        multiplier = 1.0

        # Cold weather preferable system.
        if is_extreme_cold:
            if "hoodie" in garment_type or "sweatshirt" in garment_type:
                multiplier += 0.5
            elif "shirt" in garment_type or "tshirt" in garment_type:
                multiplier -= 0.3
        elif is_very_cold:
            if "hoodie" in garment_type or "sweatshirt" in garment_type:
                multiplier +=0.3
                
        return multiplier
    
    # Calculating priority measuers.
    def priority_score(g):
        score = 0.0
        
        # Confidence level.
        confidence = g.get("confidence_score", 0.0)
        score += confidence * 100
        
        # Insulation scores.
        insulation = g.get("insulation_score", 50)
        insulation_distance = abs(insulation - ideal_insulation)
        
        # Scoring.
        if insulation_distance <= 10:
            score += 50 if (is_extreme_cold or is_very_cold) else 30
        elif insulation_distance <= 20:
            score += 30 if (is_extreme_cold or is_very_cold) else 20
        elif insulation_distance <= 30:
            score += 15 if (is_extreme_cold or is_very_cold) else 10
        
        # Weather protection.
        if category == "Outerwear" and (is_extreme_cold or is_very_cold or is_wet):
            weather_protection = g.get("weather_protection_score", 30)
            
            if weather_protection >= 70:
                score += 40 if is_extreme_cold else 25
            elif weather_protection >= 50:
                score += 25 if is_extreme_cold else 15
            elif weather_protection >= 30:
                score += 10
            if is_wet and g.get("rain_safe") == "true":
                score += 30

        # Base layer multiplier
        score *= base_layer_type_multiplier(g)
            
        # Color safety.
        if g.get("color_role") == "base":
            score += 5
        
        return score
    
    garments_sorted = sorted(garments, key = priority_score, reverse = True)
    return garments_sorted

# Checking temperature condition with outfit.
def _check_temp_appropriateness(pieces, weather_profile):

    pieces = [p for p in pieces if p is not None]
    temp = weather_profile["temperature"]
    
    # Calculating ideal insulation
    ideal_insulation = max(0, min(100, 95 - (temp * 2.5)))
    
    for piece in pieces:
        insulation = piece.get("insulation_score", 50)
        distance = abs(insulation - ideal_insulation)
        if distance > 40:
            return False
    
    return True

# Formatting the garment.
def _format_garment(garment):
    if not garment:
        return None
    
    return {
        "id": garment.get("db_id"),
        "category": garment.get("primary_category"),
        "layering": garment.get("layering_role"),
        "thermal_level": garment.get("thermal_level"),
        "insulation_score": garment.get("insulation_score"),
        "breathability_score": garment.get("breathability_score"),
        "weather_protection_score": garment.get("weather_protection_score"),
        "color_family": garment.get("color_family"),
        "color_role": garment.get("color_role"),
        "formality": garment.get("formality_level"),
        "temp_range": garment.get("temp_range"),
        "sleeve_length": garment.get("sleeve_length"),
        "confidence": {
            "score": garment.get("confidence_score"),
            "band": garment.get("confidence_band"),
            "needs_review": garment.get("needs_review")
        },
        "compatibility_weight": garment.get("compatibility_weight"),
        "wind_resistance": garment.get("wind_resistance"),
        "rain_safe": garment.get("rain_safe"),
        "image": f"data:image/png;base64,{garment.get('image_data')}" if garment.get("image_data") else None
    }

# Getting different suggestions.
def get_outfit_alternatives(temperature_celsius, weather_condition="sunny", event_formality="casual", count=3):

    all_garments = get_all_garments()
    
    if not all_garments:
        return []
    
    tops = [g for g in all_garments if g.get("primary_category") == "Top"]
    bottoms = [g for g in all_garments if g.get("primary_category") == "Bottom"]
    outerwear = [g for g in all_garments if g.get("primary_category") == "Outerwear"]
    
    # Weather profile
    weather_profile = create_weather_profile(temperature_celsius, weather_condition)
    
    # Filtering by insulation
    tops_filtered, tops_fallback = _filter_by_insulation_smart(tops, weather_profile)
    bottoms_filtered, bottoms_fallback = _filter_by_insulation_smart(bottoms, weather_profile)
    outerwear_filtered, outerwear_fallback = _filter_by_insulation_smart(outerwear, weather_profile)
    
    tops = tops_filtered if tops_filtered else tops_fallback
    bottoms = bottoms_filtered if bottoms_filtered else bottoms_fallback
    outerwear = outerwear_filtered if outerwear_filtered else outerwear_fallback
    
    # Sorting by priority
    tops = _sort_by_priority(tops, weather_profile, "Top")
    bottoms = _sort_by_priority(bottoms, weather_profile, "Bottom")
    outerwear = _sort_by_priority(outerwear, weather_profile, "Outerwear")
    
    # Generating multiple valid outfits
    candidates = []
    
    # Avoiding some clash.
    for top in tops[:8]:
        for bottom in bottoms[:8]:
            for outer in [None] + outerwear[:5]:
                pieces = [top, bottom, outer]
                
                # Valid matches.
                if not validate_color_rules(pieces):
                    continue
                if not validate_formality_match(pieces, event_formality):
                    continue
                
                # Score
                outfit_score = score_outfit(top, bottom, outer, temperature_celsius, event_formality, weather_condition)
                
                # Removing low scores.
                if outfit_score < 30:
                    continue
                
                candidates.append({"top": top, "bottom": bottom, "outerwear": outer, "score": outfit_score })
    
    # Scoring
    candidates.sort(key=lambda x: x["score"], reverse=True)
    
    return [{
        "outfit": {"top": _format_garment(c["top"]), "bottom": _format_garment(c["bottom"]), "outerwear": _format_garment(c["outerwear"])},
        "score": c["score"]
    } for c in candidates[:count]]