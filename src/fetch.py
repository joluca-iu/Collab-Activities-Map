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

# Extended query: org-level fields + nested per-activity details
QUERY = """mutation GetCommunityOrgFullFunc($input: GetCommunityOrgFullFuncInput!) {
  getCommunityOrgFullFunc(input: $input) {
    results {
      id name street street2 zipcode city state county country latitude longitude
      type description url phone email archived status
      activityCnt activityName role contactNames contactEmails
      sectionCnt courses unitCnt unitNames externalId
      activities {
        id name description url focuses
        contactFirstname contactLastname contactEmail contactOffice
        units goal_names
      }
    }
  }
}"""


def get_community_partners_by_program(portal_id, portal_name, program_id, program_name):
    out_dir = DATA_DIR / "raw" / portal_name
    out_file_program_name = program_name.replace(" ", "_").replace("-", "").lower()
    out_file     = out_dir / f"{out_file_program_name}_community_partners.csv"
    act_out_file = out_dir / f"{out_file_program_name}_activities.json"

    os.makedirs(out_dir, exist_ok=True)

    payload = json.dumps({
        "query": QUERY,
        "variables": {
            "input": {
                "pPortalId": portal_id,
                "pToken": TOKEN,
                "pProgramId": program_id,
                "pLimit": 2000
            }
        }
    })
    headers = {
        'x-api-key': API_KEY,
        'Content-Type': content_type,
        'User-Agent': user_agent,
        'Authorization': TOKEN
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    response.raise_for_status()
    json_data = response.json()

    if json_data.get("errors"):
        msgs = [err.get("message", str(err)) for err in json_data["errors"]]
        raise RuntimeError("GraphQL errors: " + " | ".join(msgs))
    data = json_data.get('data')
    if data is None:
        raise KeyError("Response has no 'data' key or data is null")
    func = data.get("getCommunityOrgFullFunc")
    if func is None:
        raise KeyError("'getCommunityOrgFullFunc' is missing or null (auth/variables mismatch?)")
    rows = func.get('results')
    if rows is None:
        raise KeyError("'results' is missing")
    if not isinstance(rows, list):
        raise TypeError(f"'results' expected list, got {type(rows).__name__}")

    df = pd.DataFrame(rows)
    df["portal_name"] = portal_name
    df["programs"] = program_name

    # Save per-activity details as a JSON sidecar keyed by org id.
    # This preserves the nested structure that CSV cannot represent.
    activities_map = {}
    for row in rows:
        org_id = row.get('id')
        acts = row.get('activities') or []
        if org_id and acts:
            activities_map[org_id] = acts

    with open(act_out_file, 'w', encoding='utf-8') as f:
        json.dump(activities_map, f, indent=2)

    # Drop the nested activities column before writing the flat CSV
    csv_df = df.drop(columns=['activities'], errors='ignore')
    csv_df.to_csv(out_file, index=False)

    return df


def run_fetch():
    portals = config['portals']
    for portal in portals:
        portal_name = portals[portal]['portal_name']
        portal_id   = portals[portal]['portal_id']
        programs    = portals[portal]['program_ids']
        for program_name, program_id in programs.items():
            if program_id and program_id != "None":
                df = get_community_partners_by_program(
                    portal_id, portal_name, program_id, program_name
                )
                print(f"Fetched data for {portal_name} : {program_name}, {len(df)} records")
            else:
                print(f"Data not available for {portal_name} : {program_name}")
