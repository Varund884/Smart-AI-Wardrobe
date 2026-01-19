# Validation of the outfit.
from schema import (
    VALID_CATEGORIES, VALID_LAYERING, VALID_THERMAL, 
    VALID_SEASONS, VALID_FORMALITY, VALID_RAIN_SAFE,
    VALID_WIND, VALID_COLOR_FAMILY, VALID_CONFIDENCE_BAND,
    VALID_SLEEVE_LENGTH, VALID_COVERAGE
)

# Validating metadata structure.
def validate_metadata(metadata):

    flags = []
    confidence_penalty = 0.0
    meta = metadata.copy()
    
    # Schema validation.
    schema_issues = _validate_schema(meta)
    flags.extend(schema_issues)
    confidence_penalty += len(schema_issues) * 0.05
    
    # CChecking the consistency.
    consistency_issues = _check_cross_field_consistency(meta)
    flags.extend(consistency_issues)
    
    # Reducing scores for invalid validation.
    for issue in consistency_issues:
        if "CRITICAL" in issue:
            confidence_penalty += 0.20
        elif "WARNING" in issue:
            confidence_penalty += 0.10
        else:
            confidence_penalty += 0.05
    
    # Range.
    range_issues = _validate_ranges(meta)
    flags.extend(range_issues)
    confidence_penalty += len(range_issues) * 0.08
    
    # Scores
    score_issues = _validate_continuous_scores(meta)
    flags.extend(score_issues)
    confidence_penalty += len(score_issues) * 0.06
    
    # Adjusting the confidence level.
    original_confidence = meta.get("confidence_score", 0.5)
    adjusted_confidence = max(0.0, original_confidence - confidence_penalty)
    meta["confidence_score"] = round(adjusted_confidence, 2)
    
    # Updating the confidence.
    if adjusted_confidence >= 0.5:
        meta["confidence_band"] = "High"
        meta["needs_review"] = False
    elif adjusted_confidence >= 0.25:
        meta["confidence_band"] = "Medium"
        meta["needs_review"] = False
    else:
        meta["confidence_band"] = "Low"
        meta["needs_review"] = True
    
    return {"validated_metadata": meta, "validation_flags": flags, "confidence_adjustment": round(confidence_penalty, 2),}

# Validating scheme metadata
def _validate_schema(meta):
    issues = []
    
    if meta.get("primary_category") not in VALID_CATEGORIES:
        issues.append(f"Invalid category: {meta.get('primary_category')}")
    
    if meta.get("layering_role") not in VALID_LAYERING:
        issues.append(f"Invalid layering: {meta.get('layering_role')}")
    
    if meta.get("thermal_level") not in VALID_THERMAL:
        issues.append(f"Invalid thermal level: {meta.get('thermal_level')}")
    
    if meta.get("formality_level") not in VALID_FORMALITY:
        issues.append(f"Invalid formality: {meta.get('formality_level')}")
    
    if meta.get("rain_safe") not in VALID_RAIN_SAFE:
        issues.append(f"Invalid rain_safe: {meta.get('rain_safe')}")
    
    if meta.get("wind_resistance") not in VALID_WIND:
        issues.append(f"Invalid wind_resistance: {meta.get('wind_resistance')}")
    
    if meta.get("color_family") not in VALID_COLOR_FAMILY:
        issues.append(f"Invalid color_family: {meta.get('color_family')}")
    
    if meta.get("sleeve_length") not in VALID_SLEEVE_LENGTH:
        issues.append(f"Invalid sleeve_length: {meta.get('sleeve_length')}")
    
    if meta.get("coverage_level") not in VALID_COVERAGE:
        issues.append(f"Invalid coverage_level: {meta.get('coverage_level')}")
    
    seasons = meta.get("seasonality", [])
    if not isinstance(seasons, list):
        issues.append("seasonality must be a list")
    else:
        for s in seasons:
            if s not in VALID_SEASONS:
                issues.append(f"Invalid season: {s}")
    
    return issues

# Checking consistency.
def _check_cross_field_consistency(meta):
    issues = []
    
    # Comparing insulation with sleeves.
    insulation = meta.get("insulation_score", 50)
    sleeve_length = meta.get("sleeve_length", "unknown")
    
    if insulation >= 70 and sleeve_length == "sleeveless":
        issues.append("CRITICAL: High insulation with sleeveless design is wrong.")
    
    if insulation <= 30 and sleeve_length == "long":
        issues.append("WARNING: Low insulation with long sleeves is unusual.")
    
    # Layering for extreme weather conditions.
    layering_role = meta.get("layering_role", "Base")
    weather_protection = meta.get("weather_protection_score", 30)
    wind_resistance = meta.get("wind_resistance", "Low")
    
    if layering_role == "Outer" and weather_protection < 30:
        issues.append("WARNING: Outer layer with low weather protection")
    
    if layering_role == "Outer" and wind_resistance == "Low":
        issues.append("Outer layer with Low wind resistance is unusual")
    
    if layering_role != "Outer" and weather_protection > 60:
        issues.append("WARNING: High weather protection on non-outer layer is unusual")
    
    # Thermal and insulation categoriation.
    thermal_level = meta.get("thermal_level", "Medium")

    if thermal_level == "High" and insulation < 60:
        issues.append("WARNING: High thermal level but low insulation score")
    
    if thermal_level == "Low" and insulation > 50:
        issues.append("WARNING: Low thermal level but high insulation score")
    
    # Weather and rain conditons.
    rain_safe = meta.get("rain_safe", "unknown")
    
    if rain_safe == "true" and weather_protection < 50:
        issues.append("WARNING: Rain-safe marked but low weather protection score")
    
    if rain_safe == "false" and weather_protection > 60:
        issues.append("WARNING: Not rain-safe but high weather protection score")
    
    # Checkinf if recommending outerwear for cold conditions.
    temp_range = meta.get("temp_range", {})
    t_min = temp_range.get("min", 10)
    category = meta.get("primary_category", "Unknown")
    
    if t_min < 0 and category != "Outerwear" and insulation < 70:
        issues.append("CRITICAL: Extreme cold rating without outerwear/high insulation")
    
    # Seasonal condition.
    seasonality = meta.get("seasonality", [])
    t_max = temp_range.get("max", 25)
    
    if "Winter" in seasonality and t_min > 15:
        issues.append("WARNING: Winter season but warm minimum temperature")
    
    if "Summer" in seasonality and t_max < 20:
        issues.append("WARNING: Summer season but cool maximum temperature")
    
    # Coverage.
    coverage = meta.get("coverage_level", "moderate")
    
    if category == "Outerwear" and coverage == "minimal":
        issues.append("WARNING: Outerwear with minimal coverage is unusual")
    
    # Insulation and breathable.
    breathability = meta.get("breathability_score", 50)
    
    if insulation > 70 and breathability > 60:
        issues.append("WARNING: High insulation with high breathability is contradictory")
    
    if insulation < 30 and breathability < 40:
        issues.append("WARNING: Low insulation with low breathability is unusual")
    
    return issues

# Valid temperature range.
def _validate_ranges(meta):
    issues = []
    
    temp_range = meta.get("temp_range", {})
    t_min = temp_range.get("min")
    t_max = temp_range.get("max")
    
    if t_min is None or t_max is None:
        issues.append("Missing temperature range")
        return issues
    
    # Minimium more extreme.
    if t_min > t_max:
        issues.append(f"CRITICAL: Invalid temp range: min ({t_min}) > max ({t_max})")
    
    # No narrow range.
    if t_max - t_min < 5:
        issues.append(f"WARNING: Suspiciously narrow temp range: {t_min}-{t_max}°C")
    
    # No broad range.
    if t_max - t_min > 30:
        issues.append(f"Very broad temp range: {t_min}-{t_max}°C")
    
    # Absolute conditions.
    if t_min < -30 or t_max > 50:
        issues.append(f"CRITICAL: Extreme temperature values: {t_min}-{t_max}°C")
    
    return issues

# Continue scores.
def _validate_continuous_scores(meta):
    issues = []
    
    insulation = meta.get("insulation_score")
    breathability = meta.get("breathability_score")
    weather_protection = meta.get("weather_protection_score")
    
    # Checking range from 0 to 100.
    if insulation is not None:
        if not (0 <= insulation <= 100):
            issues.append(f"CRITICAL: Insulation score out of range: {insulation}")
    
    if breathability is not None:
        if not (0 <= breathability <= 100):
            issues.append(f"CRITICAL: Breathability score out of range: {breathability}")
    
    if weather_protection is not None:
        if not (0 <= weather_protection <= 100):
            issues.append(f"CRITICAL: Weather protection score out of range: {weather_protection}")
    
    return issues

# Summary.
def generate_validation_report(metadata):
    return {
        "confidence_score": metadata.get("confidence_score", 0.0),
        "confidence_band": metadata.get("confidence_band", "Low"),
        "needs_review": metadata.get("needs_review", True),
        "validation_flags": metadata.get("debug_metadata", {}).get("validation_flags", []),
        "primary_category": metadata.get("primary_category", "Unknown"),
        "status": "PASS" if not metadata.get("needs_review") else "REVIEW",
        "continuous_scores": {
            "insulation": metadata.get("insulation_score", 0),
            "breathability": metadata.get("breathability_score", 0),
            "weather_protection": metadata.get("weather_protection_score", 0),
        }
    }