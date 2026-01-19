# Storage for garment metadata.
# Importing required libraries.
import sqlite3
import json

# Initializing database with garments table
def init_db():
    conn = sqlite3.connect("outfits.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS garments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Function to insert the garments int the data base.
def insert_garment(metadata):
    conn = sqlite3.connect("outfits.db")
    c = conn.cursor()
    
    try:
        # Sanitize for JSON
        clean_data = _sanitize_for_json(metadata)
        json_data = json.dumps(clean_data, ensure_ascii=False)
        
        c.execute("INSERT INTO garments (data) VALUES (?)", (json_data,))
        conn.commit()
        garment_id = c.lastrowid
        
        return garment_id
        
    except Exception as e:
        print(f"Database insert error: {e}")
        conn.rollback()
        return None
        
    finally:
        conn.close()

# Getting all the garment details.
def get_all_garments():
    conn = sqlite3.connect("outfits.db")
    c = conn.cursor()
    
    c.execute("SELECT id, data, created_at FROM garments ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    
    garments = []
    for row in rows:
        try:
            garment = json.loads(row[1])
            garment['db_id'] = row[0]
            garment['created_at'] = row[2]
            garments.append(garment)
        except json.JSONDecodeError as e:
            print(f"Error decoding garment {row[0]}: {e}")
            continue
    
    return garments

# Getting garments by their id.
def get_garment_by_id(garment_id):
    conn = sqlite3.connect("outfits.db")
    c = conn.cursor()
    c.execute("SELECT id, data FROM garments WHERE id = ?", (garment_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        try:
            garment = json.loads(row[1])
            garment['db_id'] = row[0]
            return garment
        except json.JSONDecodeError:
            return None
    
    return None

# Deleting garments.
def delete_garment(garment_id):
    conn = sqlite3.connect("outfits.db")
    c = conn.cursor()
    c.execute("DELETE FROM garments WHERE id = ?", (garment_id,))
    conn.commit()
    conn.close()

# Final json.
def _sanitize_for_json(data):
    if isinstance(data, dict):
        return {k: _sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_sanitize_for_json(item) for item in data]
    elif isinstance(data, (str, int, float, bool)) or data is None:
        return data
    else:
        # Converting any other type to string
        return str(data)