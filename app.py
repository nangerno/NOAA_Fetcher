from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import sqlite3
from shapely.geometry import Point, shape
import os
import logging

logging.basicConfig(level=logging.DEBUG)

app = FastAPI()

DATABASE_PATH = "charts_metadata.db"
CHARTS_DIR = "./geojson_data"

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

@app.get("/charts")
async def get_charts():
    charts_metadata = get_metadata_from_database()
    return charts_metadata

@app.get("/charts/{chart_id}/file")
async def get_chart_file(chart_id: str):
    charts_metadata = get_metadata_from_database()
    chart = next((c for c in charts_metadata if c["id"] == chart_id), None)
    if not chart:
        raise HTTPException(status_code=404, detail="Chart not found")
    file_name = chart["file"]
    chart_path = os.path.join(CHARTS_DIR, file_name)

    if not os.path.exists(chart_path):
        raise HTTPException(status_code=404, detail="Chart file not found")
    
    return FileResponse(chart_path)

@app.post("/charts/by-location")
async def download_chart_by_location(latitude: float, longitude: float):
    charts_metadata = get_metadata_from_database()
    
    point = Point(longitude, latitude)
    matching_chart = None

    for chart in charts_metadata:
        bbox_str = chart["bbox"]
        if isinstance(bbox_str, str):
            bbox = list(map(float, bbox_str.split(',')))
        else:
            bbox = bbox_str
        
        minx, miny, maxx, maxy = bbox
        chart_bbox = shape({
            "type": "Polygon",
            "coordinates": [[
                [minx, miny],
                [maxx, miny],
                [maxx, maxy],
                [minx, maxy],
                [minx, miny]
            ]]
        })

        if chart_bbox.contains(point):
            matching_chart = chart
            break

    if not matching_chart:
        raise HTTPException(status_code=404, detail="No charts found for the given location")

    chart_file_path = os.path.join(CHARTS_DIR, matching_chart["file"])
    if not os.path.exists(chart_file_path):
        raise HTTPException(status_code=404, detail="Chart file not found")
    return FileResponse(chart_file_path)