import requests
import json
from dotenv import load_dotenv
import yaml
import os
import pandas as pd
from utils.paths import ENV_FILE, CONFIGS_DIR, DATA_DIR

load_dotenv(ENV_FILE)
API_KEY = os.getenv("COLAB_API_KEY")
TOKEN = os.getenv("COLAB_TOKEN")

config = yaml.safe_load(open(CONFIGS_DIR / "sources.yml"))

url = config['collaboratory']['base_url']
content_type = config['collaboratory']['headers']['Content-Type']
user_agent = config['collaboratory']['headers']['User-Agent']

HEADERS = {
    'x-api-key': API_KEY,
    'Content-Type': content_type,
    'User-Agent': user_agent,
    'Authorization': TOKEN
}

# ── Query 1: Community partners per program ───────────────────────────────────

COMMUNITY_PARTNERS_QUERY = """mutation GetCommunityOrgFullFunc($input: GetCommunityOrgFullFuncInput!) {
  getCommunityOrgFullFunc(input: $input) {
    results {
      id name street street2 zipcode city state county country latitude longitude
      type description url phone email archived status
      activityCnt activityName role contactNames contactEmails
      sectionCnt courses unitCnt unitNames externalId
    }
  }
}"""

# ── Query 2: Activities per program ──────────────────────────────────────────
# NOTE: Update the mutation name below if the API uses a different name.

ACTIVITIES_QUERY = """mutation GetActivitiesFunc($input: GetActivitiesFuncInput!) {
  getActivitiesFunc(input: $input) {
    results {
      id name description url focuses
      contactFirstname contactLastname contactEmail contactOffice
      units goal_names
    }
  }
}"""


def _post(query, variables):
    """POST a GraphQL query and return the parsed results list."""
    payload = json.dumps({"query": query, "variables": variables})
    response = requests.request("POST", url, headers=HEADERS, data=payload)
    response.raise_for_status()
    json_data = response.json()

    if json_data.get("errors"):
        msgs = [err.get("message", str(err)) for err in json_data["errors"]]
        raise RuntimeError("GraphQL errors: " + " | ".join(msgs))

    data = json_data.get("data")
    if data is None:
        raise KeyError("Response has no 'data' key or data is null")

    # Return whichever top-level key contains the results
    for key, value in data.items():
        if isinstance(value, dict) and "results" in value:
            rows = value["results"]
            if not isinstance(rows, list):
                raise TypeError(f"'results' expected list, got {type(rows).__name__}")
            return rows

    raise KeyError("No 'results' key found in response data")


def get_community_partners_by_program(portal_id, portal_name, program_id, program_name):
    out_dir = DATA_DIR / "raw" / portal_name
    out_file_program_name = program_name.replace(" ", "_").replace("-", "").lower()
    out_file = out_dir / f"{out_file_program_name}_community_partners.csv"
    os.makedirs(out_dir, exist_ok=True)

    rows = _post(COMMUNITY_PARTNERS_QUERY, {
        "input": {
            "pPortalId": portal_id,
            "pToken": TOKEN,
            "pProgramId": program_id,
            "pLimit": 2000
        }
    })

    df = pd.DataFrame(rows)
    df["portal_name"] = portal_name
    df["programs"] = program_name
    df.to_csv(out_file, index=False)
    return df


def get_activities_by_program(portal_id, portal_name, program_id, program_name):
    out_dir = DATA_DIR / "raw" / portal_name
    out_file_program_name = program_name.replace(" ", "_").replace("-", "").lower()
    out_file = out_dir / f"{out_file_program_name}_activities.json"
    os.makedirs(out_dir, exist_ok=True)

    rows = _post(ACTIVITIES_QUERY, {
        "input": {
            "pPortalId": portal_id,
            "pToken": TOKEN,
            "pProgramId": program_id,
            "pLimit": 2000
        }
    })

    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=2)

    return rows


def run_fetch():
    portals = config['portals']
    for portal in portals:
        portal_name = portals[portal]['portal_name']
        portal_id   = portals[portal]['portal_id']
        programs    = portals[portal]['program_ids']
        for program_name, program_id in programs.items():
            if not program_id or program_id == "None":
                print(f"Data not available for {portal_name} : {program_name}")
                continue

            df = get_community_partners_by_program(
                portal_id, portal_name, program_id, program_name
            )
            print(f"Fetched {len(df)} community partners for {portal_name} : {program_name}")

            acts = get_activities_by_program(
                portal_id, portal_name, program_id, program_name
            )
            print(f"Fetched {len(acts)} activities for {portal_name} : {program_name}")
