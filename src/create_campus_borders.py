import yaml
import json
from utils.paths import CONFIGS_DIR, COUNTY_GEOJSON_PATH
## ------------------- Campus border geojson ------------------ ###
COUNTY_CONFIG_PATH = CONFIGS_DIR / "campus_counties.yml"

def create_east_border_geojson():
    county_config = yaml.safe_load(open(COUNTY_CONFIG_PATH))
    east = set(county_config["campuses"]["East"]["counties"])

    with open(COUNTY_GEOJSON_PATH, "r") as f:
        all_counties = json.load(f)

    return {
        "type": "FeatureCollection",
        "features": [
            feat for feat in all_counties["features"]
            if feat["properties"].get("name") in east
        ],
    }

def create_fort_wayne_border_geojson():
    county_config = yaml.safe_load(open(COUNTY_CONFIG_PATH))
    fort_wayne = set(county_config["campuses"]["Fort Wayne"]["counties"])

    with open(COUNTY_GEOJSON_PATH, "r") as f:
        all_counties = json.load(f)

    return {
        "type": "FeatureCollection",
        "features": [
            feat for feat in all_counties["features"]
            if feat["properties"].get("name") in fort_wayne
        ],
    }
    
def create_indianapolis_border_geojson():
    county_config = yaml.safe_load(open(COUNTY_CONFIG_PATH))
    indianapolis = set(county_config["campuses"]["Indianapolis"]["counties"])
    with open(COUNTY_GEOJSON_PATH, "r") as f:
        all_counties = json.load(f)
    return {
        "type": "FeatureCollection",
        "features": [
            feat for feat in all_counties["features"]
            if feat["properties"].get("name") in indianapolis
        ],
    }

def create_kokomo_border_geojson():
    county_config = yaml.safe_load(open(COUNTY_CONFIG_PATH))
    kokomo = set(county_config["campuses"]["Kokomo"]["counties"])
    with open(COUNTY_GEOJSON_PATH, "r") as f:
        all_counties = json.load(f)
    return {
        "type": "FeatureCollection",
        "features": [
            feat for feat in all_counties["features"]
            if feat["properties"].get("name") in kokomo
        ],
    }

def create_south_bend_border_geojson():
    county_config = yaml.safe_load(open(COUNTY_CONFIG_PATH))
    south_bend = set(county_config["campuses"]["South Bend"]["counties"])
    with open(COUNTY_GEOJSON_PATH, "r") as f:
        all_counties = json.load(f)
    return {
        "type": "FeatureCollection",
        "features": [
            feat for feat in all_counties["features"]
            if feat["properties"].get("name") in south_bend
        ],
    }

def create_southeast_border_geojson():
    county_config = yaml.safe_load(open(COUNTY_CONFIG_PATH))
    southeast = set(county_config["campuses"]["South East"]["counties"])
    with open(COUNTY_GEOJSON_PATH, "r") as f:
        all_counties = json.load(f)
    return {
        "type": "FeatureCollection",
        "features": [
            feat for feat in all_counties["features"]
            if feat["properties"].get("name") in southeast
        ],
    }

def create_bloomington_border_geojson():
    county_config = yaml.safe_load(open(COUNTY_CONFIG_PATH))
    bloomington = set(county_config["campuses"]["Bloomington"]["counties"])
    with open(COUNTY_GEOJSON_PATH, "r") as f:
        all_counties = json.load(f)
    return {
        "type": "FeatureCollection",
        "features": [
            feat for feat in all_counties["features"]
            if feat["properties"].get("name") in bloomington
        ],
    }

def create_columbus_border_geojson():
    county_config = yaml.safe_load(open(COUNTY_CONFIG_PATH))
    columbus = set(county_config["campuses"]["Columbus"]["counties"])
    with open(COUNTY_GEOJSON_PATH, "r") as f:
        all_counties = json.load(f)
    return {
        "type": "FeatureCollection",
        "features": [
            feat for feat in all_counties["features"]
            if feat["properties"].get("name") in columbus
        ],
    }

def create_northwest_border_geojson():
    county_config = yaml.safe_load(open(COUNTY_CONFIG_PATH))
    northwest = set(county_config["campuses"]["Northwest"]["counties"])
    with open(COUNTY_GEOJSON_PATH, "r") as f:
        all_counties = json.load(f)
    return {
        "type": "FeatureCollection",
        "features": [
            feat for feat in all_counties["features"]
            if feat["properties"].get("name") in northwest
        ],
    }



