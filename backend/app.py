# Main Flask application.

# Importing the required libraries.
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from PIL import Image
import io, base64
from remove_bg import remove_background
from clip_model import extract_visual_signals
from color_extractor import extract_colors
from derive import derive_metadata
from validation import validate_metadata, generate_validation_report
from database import init_db, insert_garment, get_all_garments

# Calling the frontend files to access the Flask application.
app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
CORS(app)
init_db()

# Setting the route file.
@app.route("/")
def index():
    return render_template("index.html")

# The main process begins by uploading an image.
@app.route("/upload", methods=["POST"])
def upload_images():
    files = request.files.getlist("images")
    results = []
    errors = []

    for idx, file in enumerate(files):
        try:
            raw = file.read()
            image = Image.open(io.BytesIO(raw)).convert("RGB")

            # Removing background
            bg_removed_bytes = remove_background(raw)
            image_no_bg = Image.open(bg_removed_bytes).convert("RGBA")
            
            # Extracting visual signals
            clip_signals = extract_visual_signals(image)
            
            # Extracting color
            color_data = extract_colors(image_no_bg)
            
            # Getting the metadata
            metadata = derive_metadata(clip_signals, color_data)
            
            # Validating the metadata
            validation_result = validate_metadata(metadata)
            validated_meta = validation_result["validated_metadata"]
            
            # Adding validation info to debug metadata.
            validated_meta["debug_metadata"]["validation_flags"] = validation_result["validation_flags"]
            validated_meta["debug_metadata"]["confidence_adjustment"] = validation_result["confidence_adjustment"]
            
            # Log validation issues
            if validation_result["validation_flags"]:
                print(f"[{idx+1}] Validation flags:")
                for flag in validation_result["validation_flags"]:
                    print(f"  - {flag}")
            
            # Converting image to base64 for storage.
            encoded_image = base64.b64encode(bg_removed_bytes.getvalue()).decode()
            validated_meta["image_data"] = encoded_image
            
            # Storing the data
            garment_id = insert_garment(validated_meta)
            
            if garment_id:
                print(f"[{idx+1}] Saved as ID {garment_id}: {validated_meta['primary_category']} "
                      f"({validated_meta['confidence_band']} confidence)")
                results.append({"image": f"data:image/png;base64,{encoded_image}", "metadata": validated_meta, "validation_report": generate_validation_report(validated_meta)})
            else:
                errors.append(f"Failed to save garment {idx + 1}")
        
        # Error message
        except Exception as e:
            print(f"Error processing image {idx + 1}")
            import traceback
            traceback.print_exc()
            errors.append(f"Error processing image {idx + 1}")

    response = {"results": results}
    if errors:
        response["errors"] = errors
    
    return jsonify(response)

# Function to get the garments.
@app.route("/wardrobe", methods=["GET"])
def get_wardrobe():
    # Getting all the garments.
    garments = get_all_garments()
    # Setting the confidence level.
    summary = {
        "total": len(garments),
        "by_category": {},
        "by_confidence": {"High": 0, "Medium": 0, "Low": 0},
        "needs_review": 0,
    }
    
    for g in garments:
        # Counting by category
        cat = g.get("primary_category", "Unknown")
        summary["by_category"][cat] = summary["by_category"].get(cat, 0) + 1
        
        # Counting by confidence
        band = g.get("confidence_band", "Low")
        if band in summary["by_confidence"]:
            summary["by_confidence"][band] += 1
        
        # Counting review flags
        if g.get("needs_review"):
            summary["needs_review"] += 1
    
    return jsonify({
        "garments": garments,
        "summary": summary
    })


# Function to get the full stats.
@app.route("/stats", methods=["GET"])
def get_stats():
    # Calling all the garments.
    garments = get_all_garments()
    
    # Error message.
    if not garments:
        return jsonify({"error": "No garments in wardrobe"})
    
    # Final stats.
    stats = {
        "total_items": len(garments),
        "by_category": {},
        "by_formality": {},
        "by_seasonality": {},
        "by_confidence_band": {},
        "avg_confidence": 0.0,
        "needs_review_count": 0,
    }
    
    total_confidence = 0.0
    
    for g in garments:
        # Categorization
        cat = g.get("primary_category", "Unknown")
        stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1
        
        # Formality
        form = g.get("formality_level", "Casual")
        stats["by_formality"][form] = stats["by_formality"].get(form, 0) + 1
        
        # Seasonality
        seasons = g.get("seasonality", [])
        for season in seasons:
            stats["by_seasonality"][season] = stats["by_seasonality"].get(season, 0) + 1
        
        # Confidence levels
        band = g.get("confidence_band", "Low")
        stats["by_confidence_band"][band] = stats["by_confidence_band"].get(band, 0) + 1
        
        total_confidence += g.get("confidence_score", 0.0)
        
        if g.get("needs_review"):
            stats["needs_review_count"] += 1
    
    stats["avg_confidence"] = round(total_confidence / len(garments), 2)
    
    return jsonify(stats)


# Function to get the validation report for the garments.
@app.route("/validate/<int:garment_id>", methods=["GET"])
def validate_garment(garment_id):
    # Getting all the ids
    from database import get_garment_by_id
    
    garment = get_garment_by_id(garment_id)
    
    # Error message.
    if not garment:
        return jsonify({"error": "Garment not found"}), 404
    
    report = generate_validation_report(garment)
    return jsonify(report)

# Formatting the data stats.
def _format_garment(garment):
    if not garment:
        return None
    return {
        "id": garment.get("id"),
        "name": garment.get("name"),
        "primary_category": garment.get("primary_category"),
        "color_family": garment.get("color_family"),
        "sleeve": garment.get("sleeve"),
        "type": garment.get("type"),
        "formality_level": garment.get("formality_level"),
        "seasonality": garment.get("seasonality", []),
        "image": f"data:image/png;base64,{garment.get('image_data')}" if garment.get("image_data") else None
    }

# Function to get the outfit recommendations.
@app.route("/recommend", methods=["POST"])
def get_outfit_recommendation():
    # Calling the bext outfit from another file based on it's safety.
    from outfit_safety import select_best_outfit_separate

    data = request.get_json()
    temp = data.get("temperature", 20)
    weather = data.get("weather", "sunny")
    formality = data.get("event_formality", "casual")

    # Geting garments
    all_garments = get_all_garments()
    tops = [g for g in all_garments if g["primary_category"] == "Top"]
    bottoms = [g for g in all_garments if g["primary_category"] == "Bottom"]
    outerwear = [g for g in all_garments if g["primary_category"] == "Outerwear"]

    # Selecting outfit with independent randomization
    outfit = select_best_outfit_separate(tops, bottoms, outerwear, temp, formality, weather)

    # Error message.
    if not outfit:
        return jsonify({"error": "No suitable outfit found."}), 400

    return jsonify({
        "outfit": {"top": _format_garment(outfit["top"]), "bottom": _format_garment(outfit["bottom"]), "outerwear": _format_garment(outfit["outerwear"]) if outfit["outerwear"] else None },
        "score": outfit["score"],
        "reasoning": outfit["reasoning"]
    })

# Function to generate another outfit.
@app.route("/recommend/alternatives", methods=["POST"])
def get_outfit_alternatives():
    # Getting the alternatives.
    from recommend_outfit import get_outfit_alternatives as get_alts
    
    data = request.get_json() or {}
    # Setting the conditions if no imports.
    temperature = data.get("temperature", 20)
    weather = data.get("weather", "sunny")
    formality = data.get("event_formality", "casual")
    count = data.get("count", 3)
    
    alternatives = get_alts(
        temperature_celsius=temperature,
        weather_condition=weather,
        event_formality=formality,
        count=count
    )
    # Getting the alternative.
    return jsonify({"alternatives": alternatives})

# A function to remove the item from user's wardrobe.
@app.route("/delete/<int:garment_id>", methods=["DELETE"])
def delete_garment_endpoint(garment_id):
    # Calling the data.
    from database import delete_garment, get_garment_by_id
    
    # Checking if garment exists
    garment = get_garment_by_id(garment_id)
    if not garment:
        return jsonify({"error": "Garment not found"}), 404
    
    # Deleting the garment
    delete_garment(garment_id)
    
    return jsonify({"success": True, "message": f"Garment {garment_id} deleted successfully"})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)