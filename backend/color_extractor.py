# Importing required library.
import cv2
import numpy as np
from sklearn.cluster import KMeans
from PIL import Image

# A function to extract colours.
def extract_colors(image):
    img_array = np.array(image)
    
    # Handling transparency
    if img_array.shape[2] == 4:
        alpha = img_array[:, :, 3]
        mask = alpha > 128

        if mask.sum() < 100:
            return {"primary_rgb": [128, 128, 128], "color_family": "Neutral"}
        rgb_pixels = img_array[mask][:, :3]
        
    else:
        rgb_pixels = img_array.reshape(-1, 3)
    
    if len(rgb_pixels) < 100:
        return {"primary_rgb": [128, 128, 128], "color_family": "Neutral"}
    
    # Performance sample.
    if len(rgb_pixels) > 5000:
        indices = np.random.choice(len(rgb_pixels), 5000, replace = False)
        rgb_pixels = rgb_pixels[indices]
    
    # Finding dominant color
    kmeans = KMeans(n_clusters=3, random_state = 42, n_init=5)
    kmeans.fit(rgb_pixels.astype(np.float32))
    
    labels = kmeans.labels_
    counts = np.bincount(labels)
    dominant_idx = counts.argmax()
    primary_color = kmeans.cluster_centers_[dominant_idx].astype(int)
    
    # Mapping to color family
    color_family = _classify_color_family(primary_color)
    
    return {"primary_rgb": primary_color.tolist(), "color_family": color_family, }

# Mapping RGB to color family.
def _classify_color_family(rgb):
    r, g, b = rgb
    hsv = cv2.cvtColor(np.uint8([[rgb]]), cv2.COLOR_RGB2HSV)[0][0]
    h, s, v = hsv
    
    # Neutral colours
    if s < 25:
        if v > 200:
            # White-ish colurs
            return "Neutral"
        elif v < 60:
            # Black-ish colours
            return "Dark"
        else:
            # Gray colours
            return "Neutral"
    
    # Earth tones
    if s < 80 and (h < 40 or h > 150):
        return "Earth"
    
    # Dark colors
    if v < 90:
        return "Dark"
    
    # Light colors
    if v > 180 and s < 100:
        return "Light"
    
    # Bright colors
    if s > 100:
        return "Bright"
    
    # Default
    return "Neutral"