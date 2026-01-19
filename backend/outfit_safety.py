#importing required library
import random

# Weather constants
EXTREME_COLD = 0
VERY_COLD = 10
COLD = 15
WARM = 25
HOT = 30

# Making a weather profile for more accuracy.
def create_weather_profile(temperature_celsius, weather_condition="sunny"):

    return {
        "is_extreme_cold": temperature_celsius < EXTREME_COLD,
        "is_very_cold": temperature_celsius < VERY_COLD,
        "is_cold": temperature_celsius < COLD,
        "is_warm": temperature_celsius > WARM,
        "is_hot": temperature_celsius > HOT,
        "is_wet": weather_condition.lower() in ["rain", "rainy", "snow", "snowy"],
        "is_windy": weather_condition.lower() in ["windy"],
        "is_dry": weather_condition.lower() in ["sunny", "clear"],
        "temperature": temperature_celsius,
        "condition": weather_condition.lower()
    }

# Aassigning color roles.
def assign_color_role(metadata):

    color_family = metadata.get("color_family", "Neutral")
    
    if color_family in ["Neutral", "Dark"]:
        return "base"
    
    if color_family in ["Light", "Earth", "Bright"]:
        return "accent"
    
    return "base"

# Calulating compatibility.
def calculate_compatibility_weight(metadata):

    weight = 1.0
    
    # Confidence levels.
    confidence_score = metadata.get("confidence_score", 0.0)
    confidence_band = metadata.get("confidence_band", "Low")
    
    if confidence_band == "High":
        weight *= 1.0
    elif confidence_band == "Medium":
        weight *= 0.90
    else:
        weight *= 0.75
    
    if confidence_score < 0.15:
        weight *= 0.85
    
    # Review concerns
    if metadata.get("needs_review", False):
        weight *= 0.75
    
    # Outerwear as primary.
    primary_category = metadata.get("primary_category")
    
    if primary_category == "Outerwear":
        insulation = metadata.get("insulation_score", 50)
        weather_protection = metadata.get("weather_protection_score", 30)
        
        # Incrementing for high insulation
        if insulation >= 70:
            weight *= 1.15
        elif insulation <= 30:
            weight *= 0.85
        
        # Incrementing for weather protection
        if weather_protection >= 60:
            weight *= 1.10
        elif weather_protection <= 30:
            weight *= 0.90
    
    # Checking color combination.
    color_family = metadata.get("color_family", "Neutral")
    
    if color_family in ["Neutral", "Dark"]:
        weight *= 1.02
    
    if primary_category == "Bottom" and color_family == "Bright":
        weight *= 0.95
    
    return round(max(0.0, min(1.0, weight)), 3)

# Validating correct color combination.
def validate_color_rules(pieces):

    pieces = [p for p in pieces if p is not None]
    
    if not pieces:
        return False
    
    accent_count = sum(1 for p in pieces if p.get("color_role") == "accent")
    
    # Maximum accent piece
    if accent_count > 1:
        return False
    
    # No bright bottoms
    for piece in pieces:
        if piece.get("color_role") == "accent":
            category = piece.get("primary_category")
            if category == "Bottom" and piece.get("color_family") == "Bright":
                return False
    
    return True

# Validating formality combinations.
def validate_formality_match(pieces, event_formality="casual"):

    pieces = [p for p in pieces if p is not None]
    
    if not pieces:
        return False
    
    event_formality = event_formality.lower()
    formality_levels = {"casual": 0, "smart-casual": 1, "formal": 2}
    
    piece_formalities = []
    for p in pieces:
        f = p.get("formality_level", "Casual").lower()
        piece_formalities.append(formality_levels.get(f, 0))
    
    # Allowing max 1 level difference
    if max(piece_formalities) - min(piece_formalities) > 1:
        return False
    
    # For formal events
    if event_formality.lower() == "formal":
        colors = [p.get("color_family", "Neutral") for p in pieces if p]
        if len(set(colors)) > 1:
            return False
    
    return True

# Calculating weather scores for perfect outfit.
def calculate_weather_score(pieces, weather_profile):

    pieces = [p for p in pieces if p is not None]
    score = 0.0
    max_score = 0.0
    
    temperature = weather_profile["temperature"]
    is_extreme_cold = weather_profile["is_extreme_cold"]
    is_very_cold = weather_profile["is_very_cold"]
    is_hot = weather_profile["is_hot"]
    is_wet = weather_profile["is_wet"]
    
    # Category weight
    category_weights = {"Outerwear": 1.4, "Top": 1.0, "Bottom": 0.8, }
    
    for piece in pieces:
        category = piece.get("primary_category", "Top")
        weight_multiplier = category_weights.get(category, 1.0)
        
        # Matching temperature using insulation score
        insulation = piece.get("insulation_score", 50)
        temp_match_score = _score_temperature_match(insulation, temperature, category)
        
        # Applying category weight
        weighted_score = temp_match_score * weight_multiplier
        weighted_max = 15 * weight_multiplier
        
        score += weighted_score
        max_score += weighted_max
        
        # Setting for extreme weather conditions.
        if is_extreme_cold or is_very_cold:
            if category == "Outerwear":
                weather_protection = piece.get("weather_protection_score", 30)
                
                if insulation >= 70:
                    score += 12
                elif insulation >= 50:
                    score += 5
                
                if weather_protection >= 60:
                    score += 10
                elif weather_protection >= 40:
                    score += 4
        
        if is_wet:
            if category == "Outerwear":
                rain_safe = piece.get("rain_safe", "unknown")
                if rain_safe == "true":
                    score += 15
                elif rain_safe == "false":
                    score -= 8
    
    # Normalizing to 0-50 range
    if max_score > 0:
        normalized = (score / max_score) * 50
        return max(0, min(50, normalized))
    
    return max(0, min(50, score))

# Scoring garment with weather conditions.
def _score_temperature_match(insulation_score, temperature, category):
    # Setting ideal temperature conditions.
    ideal_insulation = max(0, min(100, 95 - (temperature * 2.5)))
    
    # Calculate distance from ideal
    distance = abs(insulation_score - ideal_insulation)
    
    # Score based on distance (closer = better)
    if distance <= 10:
        # Perfect match
        return 15
    elif distance <= 20:
        # Good match
        return 12
    elif distance <= 30:
        # Ok
        return 8
    elif distance <= 40:
        # Not good
        return 4
    else:
        # Very poor match
        if temperature < 0 and insulation_score < 50:
            return -10
        elif temperature > 30 and insulation_score > 70:
            return -10
        return 0

# Scoring final complete outfit.
def score_outfit(top, bottom, outerwear, temperature_celsius, event_formality="casual", weather_condition="sunny"):

    pieces = [top, bottom]
    if outerwear:
        pieces.append(outerwear)
    
    score = 0.0
    
    # Creating weather profile
    weather_profile = create_weather_profile(temperature_celsius, weather_condition)
    
    # Weather score
    weather_score = calculate_weather_score(pieces, weather_profile)
    score += weather_score
    
    # Average compatibility weight
    avg_weight = sum(p.get("compatibility_weight", 0.5) for p in pieces) / len(pieces)
    score += avg_weight * 30
    
    # Formality match
    if validate_formality_match(pieces, event_formality):
        score += 10
    
    # Color combination.
    accent_count = sum(1 for p in pieces if p.get("color_role") == "accent")
    if accent_count == 0:
        score += 10
    elif accent_count == 1:
        score += 7
    
    # Reducing score for wrong combinations.
    if (weather_profile["is_extreme_cold"] or weather_profile["is_hot"]) and weather_score < 20:
        score -= 20
    
    return max(0.0, round(score, 2))

# Best outfit with strict weather filtering and randomization
def select_best_outfit(tops, bottoms, outerwear_items, temperature_celsius, event_formality = "casual", weather_condition = "sunny"):
    weather_profile = create_weather_profile(temperature_celsius, weather_condition)
    
    # Filter by weather appropriateness first
    valid_tops = _filter_by_weather(tops, weather_profile)
    valid_bottoms = _filter_by_weather(bottoms, weather_profile)
    valid_outer = _filter_by_weather(outerwear_items, weather_profile)
    
    # Adding None for outerwear in mild weather
    if not weather_profile["is_extreme_cold"] and not weather_profile["is_very_cold"]:
        if temperature_celsius >= 18 and not weather_profile["is_wet"] and not weather_profile["is_windy"]:
            valid_outer.append(None)
    
    if not valid_tops or not valid_bottoms:
        return None
    
    # Require outerwear for extreme cold
    if (weather_profile["is_extreme_cold"] or weather_profile["is_very_cold"]) and not valid_outer:
        return None
    
    event_formality_lower = event_formality.lower()
    
    # CASUAL: Weather + color priority
    if event_formality_lower == "casual":
        # Use all weather-appropriate items
        filtered_tops = valid_tops
        filtered_bottoms = valid_bottoms
        filtered_outer = valid_outer
    
    # SMART CASUAL: Prioritizing smart-casual metadata tags
    elif event_formality_lower == "smart-casual" or event_formality_lower == "smart casual":
        # Filter tops with smart-casual tags first
        smart_casual_tops = [t for t in valid_tops 
                            if t.get("formality_level", "").lower() in ["smart-casual", "formal"]]
        
        # If no smart-casual tops then valid tops
        filtered_tops = smart_casual_tops if smart_casual_tops else valid_tops
        
        # For bottoms, prefering smart-casual/formal
        smart_casual_bottoms = [b for b in valid_bottoms 
                               if b.get("formality_level", "").lower() in ["smart-casual", "formal"]]
        filtered_bottoms = smart_casual_bottoms if smart_casual_bottoms else valid_bottoms
        
        # For outerwear, prefering smart-casual/formal
        smart_casual_outer = [o for o in valid_outer if o is not None 
                             and o.get("formality_level", "").lower() in ["smart-casual", "formal"]]
        filtered_outer = smart_casual_outer if smart_casual_outer else valid_outer
    
    # FORMAL: Formal metadata tags, strict color coordination
    elif event_formality_lower == "formal":
        # Filter
        formal_tops = [t for t in valid_tops 
                      if t.get("formality_level", "").lower() in ["formal", "smart-casual"]]
        formal_bottoms = [b for b in valid_bottoms 
                         if b.get("formality_level", "").lower() in ["formal", "smart-casual"]]
        formal_outer = [o for o in valid_outer if o is not None 
                       and o.get("formality_level", "").lower() in ["formal", "smart-casual"]]

        # No formal items
        if not formal_tops:
            print("❌ No formal tops available!")
            return None
        
        filtered_tops = formal_tops
        filtered_bottoms = formal_bottoms if formal_bottoms else valid_bottoms
        filtered_outer = formal_outer if formal_outer else [o for o in valid_outer if o is not None]
    
    else:
        # Default logic
        filtered_tops = valid_tops
        filtered_bottoms = valid_bottoms
        filtered_outer = valid_outer

    max_attempts = 30 if event_formality_lower == "formal" else 20
    
    for attempt in range(max_attempts):
        chosen_top = random.choice(filtered_tops)
        
        # FORMAL: Strict color matching
        if event_formality_lower == "formal":
            top_color = chosen_top.get("color_family", "Neutral")
            
            # Finding bottoms with same color family
            matching_bottoms = [b for b in filtered_bottoms 
                               if b.get("color_family") == top_color]
            
            # If no exact match then neutrals
            if not matching_bottoms:
                if top_color in ["Neutral", "Dark"]:
                    matching_bottoms = [b for b in filtered_bottoms 
                                       if b.get("color_family") in ["Neutral", "Dark"]]
                else:
                    matching_bottoms = [b for b in filtered_bottoms 
                                       if b.get("color_family") == "Neutral"]
            
            if not matching_bottoms:
                continue
            
            chosen_bottom = random.choice(matching_bottoms)
            
            # Need outerwear for cold weather
            chosen_outer = None
            if weather_profile["is_extreme_cold"] or weather_profile["is_very_cold"] or temperature_celsius < 15:
                if filtered_outer:
                    valid_outer_only = [o for o in filtered_outer if o is not None]
                    if valid_outer_only:
                        # Matching outerwear color with top/bottom
                        matching_outer = [o for o in valid_outer_only 
                                         if o.get("color_family") in [top_color, "Neutral", "Dark"]]
                        chosen_outer = random.choice(matching_outer) if matching_outer else random.choice(valid_outer_only)
        
        # SMART CASUAL: Prioritizing smart-casual items, then color
        elif event_formality_lower == "smart-casual" or event_formality_lower == "smart casual":
            # Bottom
            chosen_bottom = random.choice(filtered_bottoms)
            
            # Choosing outerwear if needed
            chosen_outer = None
            if weather_profile["is_extreme_cold"] or weather_profile["is_very_cold"]:
                valid_outer_only = [o for o in filtered_outer if o is not None]
                if valid_outer_only:
                    chosen_outer = random.choice(valid_outer_only)
            else:
                chosen_outer = random.choice(filtered_outer) if filtered_outer else None
            
            # Colour rules
            pieces = [chosen_top, chosen_bottom]
            if chosen_outer:
                pieces.append(chosen_outer)
            
            if not validate_color_rules(pieces):
                continue
        
        # CASUAL: Weather + color focus
        else:
            chosen_bottom = random.choice(filtered_bottoms)
            
            if weather_profile["is_extreme_cold"] or weather_profile["is_very_cold"]:
                valid_outer_only = [o for o in filtered_outer if o is not None]
                if valid_outer_only:
                    chosen_outer = random.choice(valid_outer_only)
                else:
                    continue
            else:
                chosen_outer = random.choice(filtered_outer) if filtered_outer else None
            
            pieces = [chosen_top, chosen_bottom]
            if chosen_outer:
                pieces.append(chosen_outer)
            
            if not validate_color_rules(pieces):
                continue
        
        # Final score and return
        final_score = score_outfit(chosen_top, chosen_bottom, chosen_outer, 
                                   temperature_celsius, event_formality, weather_condition)
        
        reasoning = _generate_reasoning(
            {"top": chosen_top, "bottom": chosen_bottom, "outerwear": chosen_outer},
            weather_profile,
            event_formality
        )
        
        return {
            "top": chosen_top,
            "bottom": chosen_bottom,
            "outerwear": chosen_outer,
            "score": final_score,
            "reasoning": reasoning
        }
    
    return None

# Best outfit compatibility
def select_best_outfit_separate(tops, bottoms, outerwear_items, temperature_celsius, event_formality, weather_condition):
    return select_best_outfit(tops, bottoms, outerwear_items, temperature_celsius, event_formality, weather_condition)

# Filtering garments by weather condition.
def _filter_by_weather(garments, weather_profile):

    temp = weather_profile["temperature"]
    is_extreme_cold = weather_profile["is_extreme_cold"]
    is_very_cold = weather_profile["is_very_cold"]
    is_hot = weather_profile["is_hot"]
    
    valid = []
    
    for g in garments:
        insulation = g.get("insulation_score", 50)
        category = g.get("primary_category", "Top")
        sleeve_length = g.get("sleeve_length", "unknown")
        
        # For extreme cold.
        if is_extreme_cold and category == "Outerwear":
            if insulation < 45:
                continue
        
        # Removing sleeveless tops
        if is_very_cold and category == "Top":
            if sleeve_length == "sleeveless":
                continue
        
        # Removing high insulation
        if is_hot:
            if insulation > 60:
                continue
        
        # Checking temperature using insulation
        if category == "Outerwear" and (is_extreme_cold or is_very_cold):
            valid.append(g)
        else:
            # Checking temperature match with outfit.
            match_score = _score_temperature_match(insulation, temp, category)
            if match_score < 0:
                continue
            valid.append(g)
    
    return valid

# Reason of outfit selctions.
def _generate_reasoning(outfit, weather_profile, event_formality):

    reasons = []
    
    temp = weather_profile["temperature"]
    pieces = [outfit["top"], outfit["bottom"]]
    if outfit["outerwear"]:
        pieces.append(outfit["outerwear"])
    
    # Weather conditions
    if weather_profile["is_extreme_cold"]:
        reasons.append(f"Extreme cold protection for {temp}°C")
    elif weather_profile["is_very_cold"]:
        reasons.append(f"Cold weather appropriate for {temp}°C")
    elif weather_profile["is_hot"]:
        reasons.append(f"Hot weather appropriate for {temp}°C")
    else:
        reasons.append(f"Perfect for {temp}°C")
    
    # Outerwear notes
    if outfit["outerwear"]:
        outer = outfit["outerwear"]
        insulation = outer.get("insulation_score", 50)
        weather_protection = outer.get("weather_protection_score", 30)
        
        if insulation >= 70 and weather_protection >= 60:
            reasons.append("Maximum insulation & weather protection")
        elif insulation >= 70:
            reasons.append("High thermal insulation")
        elif weather_protection >= 60:
            reasons.append("Excellent weather protection")
    
    # Rain protection
    if weather_profile["is_wet"]:
        if outfit["outerwear"] and outfit["outerwear"].get("rain_safe") == "true":
            reasons.append("Waterproof protection")
        else:
            reasons.append("⚠ Limited rain protection")
    
    # Formality
    if event_formality != "casual":
        reasons.append(f"Matches {event_formality} dress code")
    
    # Color combination.
    accent_count = sum(1 for p in pieces if p and p.get("color_role") == "accent")
    if accent_count == 0:
        reasons.append("Classic neutral palette")
    elif accent_count == 1:
        reasons.append("Subtle accent styling")
    
    # Confidence score
    avg_conf = sum(p.get("confidence_score", 0) for p in pieces if p) / len(pieces)
    if avg_conf < 0.3:
        reasons.append("⚠ Low confidence - please verify fit")
    
    return " | ".join(reasons)