from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[2]


CONFIGS_DIR = PROJECT_ROOT / "configs"
DATA_DIR = PROJECT_ROOT / "data"
PUBLIC_DIR = PROJECT_ROOT / "public"
ENV_FILE = PROJECT_ROOT / ".env"

COUNTY_GEOJSON_PATH = DATA_DIR / "map_features" / "County_Boundaries_of_Indiana_Current.geojson"