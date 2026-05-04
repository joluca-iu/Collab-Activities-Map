import json
import os
from create_campus_borders import create_indianapolis_border_geojson

def export_campus_border_geojson(out_path):
    # Ensure the directory exists
    os.makedirs(out_path, exist_ok=True)

    # Export Indianapolis border directly into site_data/ (no subfolder)
    geojson = create_indianapolis_border_geojson()
    file_path = out_path / 'indianapolis.geojson'
    with open(file_path, 'w') as f:
        json.dump(geojson, f, indent=2)
