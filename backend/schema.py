# Getting the garment's metadata schema.
# Categorizations
CORE_SCHEMA = {
    # Category classification
    # Top | Bottom | Outerwear | Footwear | Accessory
    "primary_category": str,
    
    # Layering and thermal
    # Base | Mid | Outer
    "layering_role": str,
    
    # Low | Medium | High
    "thermal_level": str,
    
    # Garment scors.
    "insulation_score": float,
    "breathability_score": float,
    "weather_protection_score": float,
    
    # Temperature range
    "temp_range": dict,
    
    # Seasonal appropriateness
    # Summer, Spring, Fall, Winter, All
    "seasonality": list,
    
    # Social context
    # Casual | Smart-Casual | Formal
    "formality_level": str,
    
    # Weather resistance
    # true | false | unknown
    "rain_safe": str,

    # Low | Medium | High
    "wind_resistance": str,
    
    # Visual appearance
    # Neutral | Dark | Light | Bright | Earth
    "color_family": str,
    
    # Outfit safety checks
    # base | accent
    "color_role": str,
    "compatibility_weight": float,
    
    # Metadata about sleeves
    # sleeveless | short | long | unknown
    "sleeve_length": str,
    
    # minimal | moderate | full
    "coverage_level": str,
}

# Confidence and quality metadata
CONFIDENCE_SCHEMA = { "confidence_score": float, "confidence_band": str, "needs_review": bool, }

# Debug metadata
DEBUG_SCHEMA = { "debug_metadata": dict, }

# Returning a garment with safe defaults.
def get_empty_garment():
    return {
        "primary_category": "Unknown",
        "layering_role": "Base",
        "thermal_level": "Medium",
        
        # Scoring.
        "insulation_score": 50.0,
        "breathability_score": 50.0,
        "weather_protection_score": 30.0,
        
        "temp_range": {"min": 10, "max": 25},
        "seasonality": ["All"],
        "formality_level": "Casual",
        "rain_safe": "unknown",
        "wind_resistance": "Low",
        "color_family": "Neutral",
        "color_role": "base",
        "compatibility_weight": 0.5,
        
        "sleeve_length": "unknown",
        "coverage_level": "moderate",
        
        "confidence_score": 0.0,
        "confidence_band": "Low",
        "needs_review": True,
        
        "debug_metadata": {}
    }


# Validations
VALID_CATEGORIES = ["Top", "Bottom", "Outerwear", "Footwear", "Accessory", "Unknown"]
VALID_LAYERING = ["Base", "Mid", "Outer"]
VALID_THERMAL = ["Low", "Medium", "High"]
VALID_SEASONS = ["Summer", "Spring", "Fall", "Winter", "All"]
VALID_FORMALITY = ["Casual", "Smart-Casual", "Formal"]
VALID_RAIN_SAFE = ["true", "false", "unknown"]
VALID_WIND = ["Low", "Medium", "High"]
VALID_COLOR_FAMILY = ["Neutral", "Dark", "Light", "Bright", "Earth"]
VALID_CONFIDENCE_BAND = ["High", "Medium", "Low"]
VALID_SLEEVE_LENGTH = ["sleeveless", "short", "long", "unknown"]
VALID_COVERAGE = ["minimal", "moderate", "full"]