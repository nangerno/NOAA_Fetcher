import os
import json
import sqlite3
from typing import List
from shapely.geometry import shape

CHARTS_DIR = "./geojson_data"
DATABASE_PATH = "charts_metadata.db"

def create_database():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS charts_metadata (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            bbox TEXT NOT NULL,
            file TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def calculate_bbox_from_geojson(file_path: str):
    with open(file_path, 'r') as f:
        data = json.load(f)
    combined_bounds = None
    for feature in data.get("features", []):
        geom = shape(feature["geometry"])
        if combined_bounds is None:
            combined_bounds = geom.bounds
        else:
            combined_bounds = (
                min(combined_bounds[0], geom.bounds[0]),
                min(combined_bounds[1], geom.bounds[1]),
                max(combined_bounds[2], geom.bounds[2]),
                max(combined_bounds[3], geom.bounds[3]),
            )
    if combined_bounds:
        return list(combined_bounds)
    else:
        raise ValueError("No valid geometry found in the GeoJSON file")

def get_metadata_from_filesystem():
    metadata = []
    for file_name in os.listdir(CHARTS_DIR):
        if file_name.endswith(".geojson"):
            file_path = os.path.join(CHARTS_DIR, file_name)
            try:
                bbox = calculate_bbox_from_geojson(file_path)
                metadata.append({
                    "id": os.path.splitext(file_name)[0],
                    "name": file_name,
                    "bbox": bbox,
                    "file": file_name
                })
            except ValueError as e:
                print(f"Error processing {file_name}: {e}")
    return metadata

def save_metadata_to_database(metadata: List[dict]):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    for chart in metadata:
        bbox_str = ",".join(map(str, chart["bbox"]))
        cursor.execute("""
            INSERT OR REPLACE INTO charts_metadata (id, name, bbox, file)
            VALUES (?, ?, ?, ?)
        """, (chart["id"], chart["name"], bbox_str, chart["file"]))
    
    conn.commit()
    conn.close()

def get_metadata_from_database():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, bbox, file FROM charts_metadata")
    rows = cursor.fetchall()
    conn.close()
    metadata = []
    for row in rows:
        metadata.append({
            "id": row[0],
            "name": row[1],
            "bbox": list(map(float, row[2].split(","))),
            "file": row[3]
        })
    return metadata

if __name__ == "__main__":
    create_database()
    metadata = get_metadata_from_filesystem()
    save_metadata_to_database(metadata)
    print("Metadata saved to database.")
