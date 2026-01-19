// Global variables
let weatherData = null;
let selectedFiles = [];
const emojiList = ['👕', '👔', '👖', '🧥', '👗', '🎽', '👚', '🩳', '🧤', '🧣', '👟', '👠'];
let emojiIndex = 0;
let mainRecommendation = null;
let currentAlternativeIndex = 0;

// Initialize
window.addEventListener('load', () => {
    getLocationAndWeather();
    loadWardrobe();
    initTheme();
    
    // Syncing formality selectors between screens
    const formalityHome = document.getElementById('formalitySelect');
    const formalityResults = document.getElementById('formalitySelectResults');
    
    // Home screen
    if (formalityHome) {
        formalityHome.addEventListener('change', (e) => {
            if (formalityResults) {
                formalityResults.value = e.target.value;
            }
            if (weatherData) {
                fetch('/wardrobe')
                    .then(res => res.json())
                    .then(data => {
                        if (data.garments && data.garments.length > 0) {
                            getRecommendation();
                        }
                    });
            }
        });
    }
    
    // Result screen
    if (formalityResults) {
        formalityResults.addEventListener('change', (e) => {
            if (formalityHome) {
                formalityHome.value = e.target.value;
            }
            if (weatherData) {
                fetch('/wardrobe')
                    .then(res => res.json())
                    .then(data => {
                        if (data.garments && data.garments.length > 0) {
                            getRecommendation();
                        }
                    });
            }
        });
    }
});

// Theme Toggle
function initTheme() {
    const theme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', theme);
    updateThemeIcon(theme);
}

// Dark or light theme
function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const newTheme = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

// Updating the icon
function updateThemeIcon(theme) {
    document.querySelectorAll('.theme-toggle').forEach(btn => {
        btn.textContent = theme === 'dark' ? '☀️' : '🌙';
    });
}

// Location & Weather Detection
async function getLocationAndWeather() {
    document.getElementById('weatherLocation').textContent = 'Fetching weather...';
    
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async (position) => {
            const lat = position.coords.latitude.toFixed(4);
            const lon = position.coords.longitude.toFixed(4);
            // Calling the weather API
            try {
                const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,weather_code,wind_speed_10m,precipitation,rain,showers,snowfall&timezone=auto`;
                const weatherResponse = await fetch(weatherUrl);
                const weatherJson = await weatherResponse.json();
                
                let locationName = 'Your Location';
                try {
                    const locationResponse = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`);
                    const locationJson = await locationResponse.json();
                    locationName = locationJson.address?.city || locationJson.address?.town || locationJson.address?.village || locationJson.address?.county || 'Your Location';
                } catch (locError) {
                    console.log('Location name fetch failed');
                }
                
                const precipitation = weatherJson.current.precipitation || 0;
                const rain = weatherJson.current.rain || 0;
                const showers = weatherJson.current.showers || 0;
                const snowfall = weatherJson.current.snowfall || 0;
                
                let precipitationType = 'None';
                let precipitationAmount = 0;
                
                // Precipitation conditions.
                if (snowfall > 0) {
                    precipitationType = snowfall > 5 ? 'Heavy Snow' : snowfall > 1 ? 'Snow' : 'Light Snow';
                    precipitationAmount = snowfall;
                } else if (showers > 0) {
                    precipitationType = showers > 5 ? 'Heavy Showers' : 'Showers';
                    precipitationAmount = showers;
                } else if (rain > 0) {
                    precipitationType = rain > 7.6 ? 'Heavy Rain' : rain > 2.5 ? 'Moderate Rain' : 'Light Rain';
                    precipitationAmount = rain;
                } else if (precipitation > 0) {
                    precipitationType = 'Drizzle';
                    precipitationAmount = precipitation;
                }
                
                // Data
                weatherData = {
                    temperature: Math.round(weatherJson.current.temperature_2m),
                    condition: getWeatherCondition(weatherJson.current.weather_code),
                    location: locationName,
                    windSpeed: Math.round(weatherJson.current.wind_speed_10m),
                    precipitationType: precipitationType,
                    precipitationAmount: precipitationAmount.toFixed(1)
                };
                
                updateWeatherDisplay();
            } catch (error) {
                console.error('Weather fetch error:', error);
                weatherData = { temperature: 20, condition: 'sunny', location: 'Default Location', windSpeed: 0, precipitationType: 'None', precipitationAmount: 0 };
                updateWeatherDisplay();
            }
        }, (error) => {
            console.error('Geolocation error:', error);
            weatherData = { temperature: 20, condition: 'sunny', location: 'Default Location', windSpeed: 0, precipitationType: 'None', precipitationAmount: 0 };
            updateWeatherDisplay();
        });
    } else {
        weatherData = { temperature: 20, condition: 'sunny', location: 'Default Location', windSpeed: 0, precipitationType: 'None', precipitationAmount: 0 };
        updateWeatherDisplay();
    }
}

// Different weather conditions.
function getWeatherCondition(code) {
    if (code === 0) return 'sunny';
    if ([1, 2, 3].includes(code)) return 'cloudy';
    if ([45, 48].includes(code)) return 'cloudy';
    if ([51, 53, 55, 61, 63, 65, 80, 81, 82].includes(code)) return 'rainy';
    if ([71, 73, 75, 77, 85, 86].includes(code)) return 'snowy';
    if ([95, 96, 99].includes(code)) return 'rainy';
    return 'sunny';
}

// Display
function updateWeatherDisplay() {
    const emojis = { sunny: '☀️', cloudy: '☁️', rainy: '🌧️', snowy: '❄️', windy: '💨' };
    
    document.getElementById('weatherEmoji').textContent = emojis[weatherData.condition] || '🌤️';
    document.getElementById('weatherTemp').textContent = `${weatherData.temperature}°C`;
    document.getElementById('weatherLocation').textContent = weatherData.location;
    document.getElementById('weatherCondition').textContent = weatherData.condition.charAt(0).toUpperCase() + weatherData.condition.slice(1);
    
    const precipText = weatherData.precipitationType === 'None' ? 'None' : `${weatherData.precipitationType} (${weatherData.precipitationAmount} mm)`;
    document.getElementById('weatherPrecipitation').textContent = precipText;
    
    const windText = weatherData.windSpeed === 0 ? 'Calm' : `${weatherData.windSpeed} km/h`;
    document.getElementById('weatherWind').textContent = windText;
    
    document.getElementById('resultWeatherEmoji').textContent = emojis[weatherData.condition] || '🌤️';
    document.getElementById('resultWeatherTemp').textContent = `${weatherData.temperature}°C`;
    document.getElementById('resultWeatherLocation').textContent = weatherData.location;
    document.getElementById('resultWeatherPrecipitation').textContent = precipText;
    document.getElementById('resultWeatherWind').textContent = windText;
}

// Screen Navigation
function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(screenId).classList.add('active');
}

function goToLocation() { showScreen('locationScreen'); }
function goToUpload() { showScreen('uploadScreen'); }
function goToResults() { 
    showScreen('resultsScreen');
    loadWardrobe();
}

// File Uploader
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const filePreview = document.getElementById('filePreview');
const uploadBtn = document.getElementById('uploadBtn');

uploadZone.addEventListener('click', () => fileInput.click());
uploadZone.addEventListener('dragover', (e) => { e.preventDefault(); uploadZone.classList.add('dragover'); });
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragover'));
uploadZone.addEventListener('drop', (e) => { e.preventDefault(); uploadZone.classList.remove('dragover'); handleFiles(e.dataTransfer.files); });
fileInput.addEventListener('change', (e) => handleFiles(e.target.files));

function handleFiles(files) {
    selectedFiles = Array.from(files);
    displayFilePreviews();
    uploadBtn.disabled = selectedFiles.length === 0;
}

function displayFilePreviews() {
    filePreview.innerHTML = '';
    selectedFiles.forEach(file => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const div = document.createElement('div');
            div.className = 'file-item';
            div.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
            filePreview.appendChild(div);
        };
        reader.readAsDataURL(file);
    });
}

// Image uploader
async function uploadImages() {
    if (selectedFiles.length === 0) return;
    
    const formData = new FormData();
    selectedFiles.forEach(file => formData.append('images', file));
    
    document.getElementById('loadingOverlay').classList.add('active');
    startEmojiCarousel();
    
    try {
        const response = await fetch('/upload', { method: 'POST', body: formData });
        const result = await response.json();
        
        document.getElementById('loadingOverlay').classList.remove('active');
        
        if (result.results) {
            selectedFiles = [];
            filePreview.innerHTML = '';
            fileInput.value = '';
            uploadBtn.disabled = true;
            goToResults();
        }
    } catch (error) {
        console.error('Upload error:', error);
        document.getElementById('loadingOverlay').classList.remove('active');
        alert('Upload failed. Please try again.');
    }
}

// Buffer
function startEmojiCarousel() {
    const emojiEl = document.getElementById('processingEmoji');
    const statusTexts = ['Processing your wardrobe...', 'Analyzing fabrics...', 'Detecting colors...', 'Building your collection...'];
    let statusIndex = 0;
    
    const interval = setInterval(() => {
        emojiIndex = (emojiIndex + 1) % emojiList.length;
        emojiEl.textContent = emojiList[emojiIndex];
        statusIndex = (statusIndex + 1) % statusTexts.length;
        document.getElementById('statusText').textContent = statusTexts[statusIndex];
    }, 800);
    
    window.processingInterval = interval;
}

// Load Wardrobe
async function loadWardrobe() {
    try {
        const response = await fetch('/wardrobe');
        const data = await response.json();
        
        displayStats(data.summary);
        displayGarments(data.garments);
        
        if (weatherData) await getRecommendation();
    } catch (error) {
        console.error('Failed to load wardrobe:', error);
    }
}

// Generating the outfit recommendation.
async function regenerateOutfit() {
    try {
        let formality = document.getElementById('formalitySelectResults')?.value || document.getElementById('formalitySelect')?.value || 'casual';
        
        document.getElementById('alternativeBtn').disabled = true;
        
        const response = await fetch('/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                temperature: weatherData.temperature, 
                weather: weatherData.condition, 
                event_formality: formality 
            })
        });
        
        const data = await response.json();
        
        if (data.outfit) {
            currentAlternativeIndex = (currentAlternativeIndex + 1) % 5;
            displayRecommendation(data, true);
        } else if (data.error) {
            alert(data.error);
        }
        
        document.getElementById('alternativeBtn').disabled = false;

    } catch (error) {
        console.error(error);
        alert('Failed to generate another outfit.');
        document.getElementById('alternativeBtn').disabled = false;
    }
}

// Final stats of the wardrobe
function displayStats(summary) {
    const statsContainer = document.getElementById('wardrobeStats');
    statsContainer.innerHTML = `
        <div class="stat-item"><div class="stat-value">${summary.total}</div><div class="stat-label">Total Items</div></div>
        <div class="stat-item"><div class="stat-value">${summary.by_category?.Top || 0}</div><div class="stat-label">Tops</div></div>
        <div class="stat-item"><div class="stat-value">${summary.by_category?.Bottom || 0}</div><div class="stat-label">Bottoms</div></div>
        <div class="stat-item"><div class="stat-value">${summary.by_category?.Outerwear || 0}</div><div class="stat-label">Outerwear</div></div>
    `;
}

// Removing garment from the wardrobe.
async function deleteGarment(garmentId) {
    if (!confirm('Are you sure you want to remove this item from your wardrobe?')) return;
    
    try {
        const response = await fetch(`/delete/${garmentId}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            const card = document.getElementById(`garment-${garmentId}`);
            if (card) {
                card.style.animation = 'fadeOut 0.3s ease-out';
                setTimeout(() => { card.remove(); loadWardrobe(); }, 300);
            }
        } else {
            alert('Failed to delete garment: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Delete error:', error);
        alert('Failed to delete garment. Please try again.');
    }
}

// Displaying all the garments
function displayGarments(garments) {
    const grid = document.getElementById('garmentGrid');
    grid.innerHTML = '';
    
    garments.forEach((garment, index) => {
        const card = document.createElement('div');
        card.className = 'garment-card';
        card.style.animationDelay = `${index * 0.05}s`;
        card.id = `garment-${garment.db_id || index}`;
        
        const imgSrc = garment.image_data ? `data:image/png;base64,${garment.image_data}` : '';
        const tempRange = garment.temp_range || {};
        const seasons = Array.isArray(garment.seasonality) ? garment.seasonality.join(', ') : 'All';
        
        // Wardrobe garment design chart.
        card.innerHTML = `
            <div class="garment-header">
                <button class="delete-btn" onclick="deleteGarment(${garment.db_id})" title="Remove">🗑️</button>
            </div>
            <img class="garment-image" src="${imgSrc}" alt="${garment.primary_category}">
            <div class="garment-info">
                <div class="garment-category">${garment.primary_category || 'Unknown'}</div>
                <div class="metadata-summary">
                    <div><strong>Color:</strong> ${garment.color_family || 'N/A'}</div>
                    <div><strong>Formality:</strong> ${garment.formality_level || 'N/A'}</div>
                    <div><strong>Thermal:</strong> ${garment.thermal_level || 'N/A'}</div>
                    <div><strong>Temp:</strong> ${tempRange.min || '--'}°C - ${tempRange.max || '--'}°C</div>
                    <div><strong>Layering:</strong> ${garment.layering_role || 'N/A'}</div>
                    <div><strong>Seasons:</strong> ${seasons}</div>
                    <div><strong>Rain Safe:</strong> ${garment.rain_safe || 'unknown'}</div>
                    <div><strong>Wind:</strong> ${garment.wind_resistance || 'N/A'}</div>
                    <div><strong>Match:</strong> ${Math.round((garment.compatibility_weight || 0) * 100)}%</div>
                </div>
            </div>
        `;
        grid.appendChild(card);
    });
}

// Analytics board
function showAnalytics() {
    const dashboard = document.getElementById('analyticsDashboard');
    dashboard.style.display = 'block';
    dashboard.scrollIntoView({ behavior: 'smooth' });
    generateAnalytics();
}

function closeDashboard() {
    document.getElementById('analyticsDashboard').style.display = 'none';
}

// Generating the analytics.
async function generateAnalytics() {
    try {
        const response = await fetch('/wardrobe');
        const data = await response.json();
        const garments = data.garments;
        
        if (!garments || garments.length === 0) {
            document.getElementById('dashboardContent').innerHTML = '<div style="text-align: center; padding: 3rem;"><p>No data available. Add some clothes to see analytics!</p></div>';
            return;
        }
        
        const analytics = calculateAnalytics(garments);
        renderDashboard(analytics);
    } catch (error) {
        console.error('Analytics error:', error);
    }
}

// Calculating characteristics.
function calculateAnalytics(garments) {
    const analytics = {
        total: garments.length,
        byCategory: {},
        byColor: {},
        byFormality: {},
        byThermal: {},
        bySeason: {},
        byConfidence: {},
        avgCompatibility: 0,
        tempRangeDistribution: { cold: 0, cool: 0, moderate: 0, warm: 0 },
        weatherReady: { rain: 0, wind: 0 }
    };
    
    let totalCompatibility = 0;
    
    // Differnt category
    garments.forEach(g => {
        const cat = g.primary_category || 'Unknown';
        analytics.byCategory[cat] = (analytics.byCategory[cat] || 0) + 1;
        
        const color = g.color_family || 'Unknown';
        analytics.byColor[color] = (analytics.byColor[color] || 0) + 1;
        
        const formality = g.formality_level || 'Casual';
        analytics.byFormality[formality] = (analytics.byFormality[formality] || 0) + 1;
        
        const thermal = g.thermal_level || 'Medium';
        analytics.byThermal[thermal] = (analytics.byThermal[thermal] || 0) + 1;
        
        const seasons = g.seasonality || [];
        seasons.forEach(s => { analytics.bySeason[s] = (analytics.bySeason[s] || 0) + 1; });
        
        const conf = g.confidence_band || 'Low';
        analytics.byConfidence[conf] = (analytics.byConfidence[conf] || 0) + 1;
        
        totalCompatibility += (g.compatibility_weight || 0);
        
        const tempRange = g.temp_range || {};
        const avgTemp = ((tempRange.min || 0) + (tempRange.max || 0)) / 2;

        if (avgTemp < 10) analytics.tempRangeDistribution.cold++;
        else if (avgTemp < 18) analytics.tempRangeDistribution.cool++;
        else if (avgTemp < 25) analytics.tempRangeDistribution.moderate++;
        else analytics.tempRangeDistribution.warm++;
        
        if (g.rain_safe === 'true') analytics.weatherReady.rain++;
        if (g.wind_resistance === 'High' || g.wind_resistance === 'Medium') analytics.weatherReady.wind++;
    });
    
    analytics.avgCompatibility = (totalCompatibility / garments.length * 100).toFixed(1);
    return analytics;
}

// Dashboard
function renderDashboard(analytics) {
    const content = document.getElementById('dashboardContent');

    // Dashboard code.
    content.innerHTML = `
        <div class="analytics-grid">
            <div class="analytics-card"><div class="card-icon">👕</div><div class="card-value">${analytics.total}</div><div class="card-label">Total Items</div></div>
            <div class="analytics-card"><div class="card-icon">⭐</div><div class="card-value">${analytics.avgCompatibility}%</div><div class="card-label">Avg Compatibility</div></div>
            <div class="analytics-card"><div class="card-icon">🌧️</div><div class="card-value">${analytics.weatherReady.rain}</div><div class="card-label">Rain-Safe Items</div></div>
            <div class="analytics-card"><div class="card-icon">💨</div><div class="card-value">${analytics.weatherReady.wind}</div><div class="card-label">Wind-Resistant</div></div>
        </div>

        <div class="charts-section">
            <div class="chart-container"><h3>📦 By Category</h3>${renderBarChart(analytics.byCategory, 'category')}</div>
            <div class="chart-container"><h3>🎨 By Color Family</h3>${renderBarChart(analytics.byColor, 'color')}</div>
            <div class="chart-container"><h3>👔 By Formality</h3>${renderBarChart(analytics.byFormality, 'formality')}</div>
            <div class="chart-container"><h3>🌡️ By Thermal Level</h3>${renderBarChart(analytics.byThermal, 'thermal')}</div>
            <div class="chart-container"><h3>🍂 By Season</h3>${renderBarChart(analytics.bySeason, 'season')}</div>

            <div class="chart-container"><h3>🌡️ Temperature Suitability</h3>${renderBarChart({
                'Cold (<10°C)': analytics.tempRangeDistribution.cold,
                'Cool (10-18°C)': analytics.tempRangeDistribution.cool,
                'Moderate (18-25°C)': analytics.tempRangeDistribution.moderate,
                'Warm (>25°C)': analytics.tempRangeDistribution.warm
            }, 'temp')}</div>

            <div class="chart-container"><h3>✅ Data Confidence</h3>${renderBarChart(analytics.byConfidence, 'confidence')}</div>
        </div>
        <div class="insights-section"><h3>💡 Wardrobe Insights</h3>${generateInsights(analytics)}</div>
    `;
}

// Displaying the barchart.
function renderBarChart(data, type) {
    const maxValue = Math.max(...Object.values(data));
    const total = Object.values(data).reduce((a, b) => a + b, 0);
    
    let html = '<div class="bar-chart">';
    
    for (const [label, value] of Object.entries(data)) {
        const percentage = ((value / total) * 100).toFixed(1);
        const barWidth = (value / maxValue) * 100;
        
        let barColor = '#919191ff';
        
        // Barchard code.
        html += `
            <div class="bar-item">
                <div class="bar-label">${label}</div>
                <div class="bar-wrapper">
                    <div class="bar-fill" style="width: ${barWidth}%; background: ${barColor};"></div>
                    <div class="bar-value">${value} (${percentage}%)</div>
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    return html;
}

// Outfit insights.
function generateInsights(analytics) {
    const insights = [];
    
    const topCategory = Object.entries(analytics.byCategory).sort((a, b) => b[1] - a[1])[0];
    if (topCategory) insights.push(`Your wardrobe is <strong>${topCategory[0]}</strong>-heavy with ${topCategory[1]} items`);
    
    const formalCount = (analytics.byFormality['Formal'] || 0) + (analytics.byFormality['Smart-Casual'] || 0);
    const casualCount = analytics.byFormality['Casual'] || 0;
    if (casualCount > formalCount * 2) insights.push(`You have a <strong>casual-focused</strong> wardrobe (${casualCount} casual vs ${formalCount} formal/smart-casual)`);
    
    if (analytics.weatherReady.rain < 3) insights.push(`⚠️ Limited rain protection - consider adding waterproof items`);
    
    const seasons = ['Winter', 'Spring', 'Summer', 'Fall'];
    const missingSeason = seasons.find(s => !analytics.bySeason[s] || analytics.bySeason[s] < 5);

    if (missingSeason) insights.push(`⚠️ Low coverage for <strong>${missingSeason}</strong> season`);
    
    const lowConfidence = analytics.byConfidence['Low'] || 0;
    if (lowConfidence > analytics.total * 0.3) insights.push(`⚠️ ${lowConfidence} items have low confidence - metadata may need review`);
    
    const colorCount = Object.keys(analytics.byColor).length;
    if (colorCount >= 4) insights.push(`🎨 Great color diversity with ${colorCount} different color families`);
    
    return insights.length > 0 ? insights.map(i => `<div class="insight-item">• ${i}</div>`).join('') : '<div class="insight-item">• Your wardrobe looks well-balanced!</div>';
}

// Outfit recommendations.
async function getRecommendation() {
    try {
        const formality = document.getElementById('formalitySelect').value;
        const response = await fetch('/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ temperature: weatherData.temperature, weather: weatherData.condition, event_formality: formality })
        });
        
        const data = await response.json();
        
        if (data.outfit) {
            mainRecommendation = data;
            displayRecommendation(data, false);
            updateHomePreview(data);
        }
    } catch (error) {
        console.error('Failed to get recommendation:', error);
    }
}

// Updating the preview.
function updateHomePreview(data) {
    const preview = document.getElementById('recommendationPreview');
    if (!preview) return;

    // Outfit display code.
    preview.innerHTML = `
        <h2>✨ Today's Outfit ✨</h2>
        <div class="outfit-collage">
            ${data.outfit.top && data.outfit.top.image ? `<div class="outfit-item"><img src="${data.outfit.top.image}" alt="top"></div>` : ''}
            ${data.outfit.bottom && data.outfit.bottom.image ? `<div class="outfit-item"><img src="${data.outfit.bottom.image}" alt="bottom"></div>` : ''}
            ${data.outfit.outerwear && data.outfit.outerwear.image ? `<div class="outfit-item"><img src="${data.outfit.outerwear.image}" alt="outerwear"></div>` : ''}
        </div>
        <div class="outfit-reasoning">${data.reasoning || 'Perfect outfit for today!'}</div>
    `;
}

// Main default
function resetToMainOutfit() {
    if (mainRecommendation) {
        currentAlternativeIndex = 0;
        displayRecommendation(mainRecommendation, false);
    }
}

// Recommendations.
function displayRecommendation(data, isAlternative) {
    const section = document.getElementById('recommendationSection');
    const collage = document.getElementById('outfitCollage');
    const reasoning = document.getElementById('outfitReasoning');
    const indicator = document.getElementById('alternativeIndicator');
    
    section.style.display = 'block';
    collage.innerHTML = '';
    
    if (isAlternative) {
        indicator.style.display = 'block';
        indicator.textContent = `Alternative Outfit #${currentAlternativeIndex + 1}`;
    } else {
        indicator.style.display = 'none';
    }
    
    const pieces = ['top', 'bottom', 'outerwear'];
    let delay = 0;
    
    pieces.forEach(piece => {
        if (data.outfit[piece] && data.outfit[piece].image) {
            const div = document.createElement('div');
            div.className = 'outfit-item';
            div.style.animationDelay = `${delay}s`;
            div.innerHTML = `<img src="${data.outfit[piece].image}" alt="${piece}">`;
            collage.appendChild(div);
            delay += 0.2;
        }
    });
    
    // Default reasoning.
    reasoning.textContent = data.reasoning || 'Perfect outfit for today!';
}