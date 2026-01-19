# Importing the required libraries.
import clip
import torch
from PIL import Image

# OPENAI clip model for basic cpu.
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# Extracting the visual signals.
def extract_visual_signals(image: Image.Image):

    try:
        # Category.
        category_scores = _score_image(image, [
            "upper body clothing shirt jacket sweater top",
            "lower body clothing pants jeans shorts skirt",
            "heavy jacket coat outerwear layering piece",
            "footwear shoes boots sneakers",
        ])

        # Subtype score
        subtype_scores = _score_image(image, [
            "hoodie hooded sweatshirt with hood",
            "sweatshirt pullover crewneck sweater",
            "casual t-shirt tee shirt short sleeves",
            "dress shirt button-up collared shirt long sleeves",
            "tank top sleeveless shirt",
        ])
        
        # Thermal conditions.
        weight_scores = _score_image(image, [
            "thin lightweight breathable summer clothing",
            "medium weight spring fall clothing",
            "thick heavy insulated winter clothing padded",
        ])
        
        # Styling.
        # A formal peacoat gets specific recognition
        formality_scores = _score_image(image, [
            "casual everyday relaxed clothing streetwear hoodie joggers",
            "smart casual business casual neat clothing blazer chinos",
            "formal business professional elegant clothing suit dress shirt",
            "formal coat peacoat trench coat wool overcoat tailored outerwear"
        ])
        
        # Sleves length.
        sleeve_scores = _score_image(image, [
            "sleeveless no sleeves",
            "short sleeves",
            "long sleeves full coverage",
        ])
        
        # Weather proof.
        weather_scores = _score_image(image, [
            "rain jacket waterproof water resistant",
            "windbreaker wind resistant shell",
            "regular fabric not weather resistant",
        ])
        
        # CColor combination.
        color_scores = _score_image(image, [
            "dark colored black navy charcoal",
            "light colored white cream beige",
            "bright vibrant colored",
            "neutral gray brown tan",
            "earth tone olive brown rust",
        ])
        
        # Confidence
        confidence = _calculate_detection_confidence(
            category_scores,
            weight_scores,
            formality_scores
        )
        
        return {
            "category_scores": category_scores,
            "subtype_scores": subtype_scores,
            "weight_scores": weight_scores,
            "formality_scores": formality_scores,
            "sleeve_scores": sleeve_scores,
            "weather_scores": weather_scores,
            "color_scores": color_scores,
            "detection_confidence": float(confidence),
        }
    
    except Exception as e:
        print(f"CLIP extraction error: {e}")
        # Returning safe defaults
        return {
            "category_scores": {},
            "subtype_scores": {},
            "weight_scores": {},
            "formality_scores": {},
            "sleeve_scores": {},
            "weather_scores": {},
            "color_scores": {},
            "detection_confidence": 0.0,
        }

# A function to score the right garments based on text labels.
def _score_image(image, labels):
    img = preprocess(image).unsqueeze(0).to(device)
    txt = clip.tokenize(labels).to(device)
    
    with torch.no_grad():
        img_f = model.encode_image(img)
        txt_f = model.encode_text(txt)
        img_f /= img_f.norm(dim = -1, keepdim = True)
        txt_f /= txt_f.norm(dim = -1, keepdim = True)
        scores = (img_f @ txt_f.T).squeeze(0)
    
    return {labels[i]: float(scores[i]) for i in range(len(labels))}

# Calculating overall detection confidence based on scores.
def _calculate_detection_confidence(category_scores, weight_scores, formality_scores):
    # Error message.
    if not category_scores or not weight_scores or not formality_scores:
        return 0.0
    
    # Top score strength.
    cat_top = max(category_scores.values())
    weight_top = max(weight_scores.values())
    form_top = max(formality_scores.values())
    
    # Normalizing
    def normalize_score(score):
        return max(0.0, min(1.0, (score - 0.15) / 0.20))
    
    # Calulating average score.
    avg_top_score = (normalize_score(cat_top) + normalize_score(weight_top) + normalize_score(form_top)) / 3.0
    
    # Function to separate scores.
    def get_separation(scores):
        sorted_scores = sorted(scores.values(), reverse=True)
        if len(sorted_scores) < 2:
            return 0.0
        separation = sorted_scores[0] - sorted_scores[1]

        # Normalizing
        return max(0.0, min(1.0, (separation - 0.02) / 0.08))
    
    cat_sep = get_separation(category_scores)
    weight_sep = get_separation(weight_scores)
    form_sep = get_separation(formality_scores)
    
    avg_separation = (cat_sep + weight_sep + form_sep) / 3.0
    
    # Finding the winner.
    consistency_bonus = 0.0
    if cat_sep > 0.5 and weight_sep > 0.5 and form_sep > 0.5:
        consistency_bonus = 0.1
    
    # Calculating total weightage score.
    confidence = (avg_top_score * 0.5 + avg_separation * 0.4 + consistency_bonus)
    
    # Rounding the confidence.
    return round(confidence, 3)

# Picking high score garments based on scenarios.
def _pick_top(scores, threshold = 0.20):
    if not scores:
        return None
    
    label, val = max(scores.items(), key = lambda x: x[1])
    return label if val >= threshold else None