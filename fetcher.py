import os
import requests
import zipfile
import subprocess
from tqdm import tqdm

ZIP_URL = "https://charts.noaa.gov/ENCs/All_ENCs.zip"
DOWNLOAD_DIR = "noaa_data"
OUTPUT_DIR = "geojson_data"
OGR2OGR_PATH = r"C:\OSGeo4W\bin\ogr2ogr.exe"
OGRINFO_PATH = r"C:\OSGeo4W\bin\ogrinfo.exe"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_zip(url, save_path):
    print(f"Downloading data from {url}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    
    with open(save_path, "wb") as file, tqdm(
        desc=save_path,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as progress_bar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            progress_bar.update(size)
    print(f"Downloaded to {save_path}")

def extract_zip(zip_path, extract_to):
    print(f"Extracting {zip_path}...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"Extracted to {extract_to}")

def run_ogrinfo(input_file):
    try:
        result = subprocess.run(
            [OGRINFO_PATH, "-so", input_file],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running ogrinfo: {e}")
        return None

def parse_ogrinfo_output(ogrinfo_output):
    layers = []
    for line in ogrinfo_output.split('\n'):
        if ':' in line:
            layer_name = line.split(':')[0].strip()
            if layer_name.isdigit():
                layer_info = line.split(':')[1].strip()
                layer_name = layer_info.split('(')[0].strip()
                if layer_name not in ['DSID', 'Meta']:
                    layers.append(layer_name)
    return layers

def convert_to_geojson(input_dir, output_dir):
    print("Converting S-57 files to GeoJSON...")
    
    if not os.path.exists(OGR2OGR_PATH):
        raise Exception(f"ogr2ogr not found at {OGR2OGR_PATH}. Please check your installation.")

    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".000"):
                s57_path = os.path.join(root, file)
                if not os.path.exists(s57_path):
                    print(f"File not found: {s57_path}")
                    continue

                print(f"Processing {s57_path}")
                ogrinfo_output = run_ogrinfo(s57_path)
                if ogrinfo_output is None:
                    continue

                layers = parse_ogrinfo_output(ogrinfo_output)
                if not layers:
                    print(f"No valid layers found in {s57_path}")
                    continue

                for layer in layers:
                    geojson_path = os.path.join(output_dir, f"{os.path.splitext(file)[0]}_{layer.lower()}.geojson")
                    print(f"Converting {layer} layer to {geojson_path}")
                    try:
                        result = subprocess.run(
                            [
                                OGR2OGR_PATH,
                                "-f", "GeoJSON",
                                "-skipfailures",
                                geojson_path,
                                s57_path,
                                layer
                            ],
                            check=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True
                        )
                        print(f"Converted {layer} layer to {geojson_path}")
                    except subprocess.CalledProcessError as e:
                        print(f"Failed to convert {layer} layer: {e}")
                    except Exception as e:
                        print(f"An unexpected error occurred while converting {layer} layer: {e}")

def main():
    zip_path = os.path.join(DOWNLOAD_DIR, "All_ENCs.zip")
    download_zip(ZIP_URL, zip_path)
    extract_zip(zip_path, DOWNLOAD_DIR)
    convert_to_geojson(DOWNLOAD_DIR, OUTPUT_DIR)
    print("All done!")

if __name__ == "__main__":
    main()