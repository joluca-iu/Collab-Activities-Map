import json
import os
from create_campus_borders import *
from utils.paths import SITE_DIR

def export_campus_border_geojson(out_path):
    # Define the campuses and their corresponding functions
    campuses = {
        'east': create_east_border_geojson,
        'fort_wayne': create_fort_wayne_border_geojson,
        'indianapolis': create_indianapolis_border_geojson,
        'kokomo': create_kokomo_border_geojson,
        'south_bend': create_south_bend_border_geojson,
        'southeast': create_southeast_border_geojson,
        'bloomington': create_bloomington_border_geojson,
        'columbus': create_columbus_border_geojson,
        'northwest': create_northwest_border_geojson,
    }
        
    
    # Ensure the directory exists
    os.makedirs(out_path, exist_ok=True)
    
    # Export each campus border
    for campus, func in campuses.items():
        geojson = func()
        file_path = out_path / f'{campus}_border.geojson'
        with open(file_path, 'w') as f:
            json.dump(geojson, f, indent=2)
