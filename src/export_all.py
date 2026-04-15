from export_schools_geojson import export_school_campus_geojson
from fetch import run_fetch
from transform import transform_community_partners
from export_campus_border_geojson import export_campus_border_geojson
import os
from utils.paths import SITE_DIR

def main():
    # Step 1: Fetch data from APIs and save raw CSVs
    run_fetch()

    # Step 2: Transform raw CSVs into a combined cleaned CSV
    grouped_df = transform_community_partners()

    # Step 3: Export the combined cleaned data to JSON for mapping
    out_path_schools = SITE_DIR / "site_data" / "schools.geojson"
    out_path_campus_borders = SITE_DIR / "site_data" / "campus_borders"
    export_school_campus_geojson(grouped_df, out_path_schools)
    export_campus_border_geojson(out_path_campus_borders)


if __name__ == "__main__":
    main()