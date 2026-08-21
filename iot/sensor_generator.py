import random

# Common waste classes and their expected moisture ranges (for realistic simulations)
MOISTURE_PROFILES = {
    'Plastic': (5.0, 15.0),
    'Paper': (8.0, 20.0),
    'Metal': (2.0, 10.0),
    'Organic': (45.0, 85.0),
    'Other': (10.0, 40.0)
}

# Average weight profiles in grams
WEIGHT_PROFILES = {
    'Plastic': (15.0, 80.0),    # Light bottles, packaging
    'Paper': (5.0, 50.0),      # Loose paper, cardboard
    'Metal': (20.0, 350.0),    # Aluminum cans, steel parts
    'Organic': (50.0, 500.0),  # Food scraps, heavy organic waste
    'Other': (10.0, 250.0)
}

def generate_telemetry_reading(pred_category=None):
    """
    Generates a set of realistic sensor telemetry data.
    If a category is provided, moisture/weight will align with that profile.
    """
    # Pick a random category if none provided
    category = pred_category or random.choices(
        ['Plastic', 'Paper', 'Metal', 'Organic', 'Other'],
        weights=[35, 20, 15, 20, 10],
        k=1
    )[0]
    
    # 1. Weight profile
    w_min, w_max = WEIGHT_PROFILES[category]
    weight = random.uniform(w_min, w_max)
    
    # 2. Moisture profile
    m_min, m_max = MOISTURE_PROFILES[category]
    moisture = random.uniform(m_min, m_max)
    
    # 3. Temperature profile (centered around standard room/machine temp)
    # Occasionally injects heat spikes (1% chance of anomaly > 45°C)
    if random.random() < 0.01:
        temperature = random.uniform(46.0, 52.0)
    else:
        temperature = random.uniform(23.0, 32.0)
        
    return {
        'category': category,
        'weight': weight,
        'moisture': moisture,
        'temperature': temperature
    }

def generate_detection_event():
    """Generates a random waste classification event (category, confidence, processing time)."""
    category = random.choices(
        ['Plastic', 'Paper', 'Metal', 'Organic', 'Other'],
        weights=[35, 20, 15, 20, 10],
        k=1
    )[0]
    
    # 92% chance of high confidence, 8% of low confidence (needs operator verification)
    if random.random() < 0.08:
        confidence = random.uniform(0.50, 0.69)
    else:
        confidence = random.uniform(0.72, 0.98)
        
    processing_time = random.uniform(0.009, 0.022)
    
    return {
        'material': category,
        'confidence': confidence,
        'processing_time': processing_time
    }
