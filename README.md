# Smart Wardrobe AI 👕✨

> Your intelligent outfit companion.

Smart Wardrobe AI is a full-stack web application that digitizes your closet and uses Computer Vision to act as your personal stylist.
It analyzes your clothes to understand their warmth, formality, and style, then generates daily outfit recommendations based on live weather.

---

## 🚀 Features

### 🧠 AI-Powered Analysis
Uses OpenAI's CLIP model to automatically detect garment category, insulation, formality, and seasonality, all from a single photo.

### 🌤 Weather-Aware Engine
Fetches real-time weather data via Open-Meteo so you never freeze in a t-shirt or sweat in a parka.

### 🎨 Smart Styling Rules
Applies color theory, limits accent colors, and ensures proper formality matching between garments.

### 📊 Wardrobe Analytics
Visualize your closet breakdown by season, color family, and formality level.

### 🔄 Outfit Randomizer
Instantly generate alternative valid outfits if you don't like the suggestion.

---

## 🛠 Tech Stack

**Backend**  
Python (Flask), SQLite, PyTorch (CLIP model), scikit-learn (color clustering), rembg (background removal)

**Frontend**  
Vanilla JavaScript (SPA), HTML5, CSS3

**APIs**  
Open-Meteo for weather data and OpenStreetMap for geolocation

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.9 or higher
- Git

### Clone the repository
```bash
git clone https://github.com/Varund884/Smart-AI-Wardrobe.git
cd Smart-AI-Wardrobe
```

### Create a virtual environment
```bash
python -m venv venv
```

### Activate the virtual environment

**Windows**
```bash
venv\Scripts\activate
```

**macOS / Linux**
```bash
source venv/bin/activate
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run the application
```bash
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 📖 Usage Guide

### 👕 Digitize Your Closet
Navigate to the Upload screen and drag and drop images of your clothes.
Backgrounds are removed automatically and garments are analyzed.

### 🗂 Review Your Wardrobe
Visit the Wardrobe section to view all analyzed items.
Each item includes an AI confidence score

### 🧥 Get Dressed
Live weather data is fetched automatically and a complete outfit is generated.

### 🎯 Customize Style
Choose between Casual, Smart-Casual, or Formal

---

⭐ Star this repo if you find it helpful!
