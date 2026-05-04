import requests
import json
import re
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

ACTIVITIES_QUERY = """mutation GetActivitiesCoursesFunc($input: GetActivitiesCoursesFuncInput!) {
  getActivitiesCoursesFunc(input: $input) {
    results {
      id name description url focuses startTime endTime
      contactFirstname contactLastname contactEmail contactOffice
      units courses
    }
  }
}"""


# ── Query 3: Units connected to programs ─────────────────────────────────────

UNITS_QUERY = """mutation GetUnitDatasetFunc($input: GetUnitDatasetFuncInput!) {
  getUnitDatasetFunc(input: $input) {
    results {
      id name url activityName
    }
  }
}"""


def _program_file_stem(program_name):
    """'IUI 2030 Strategic Plan Pillar 3, Goal 1: Workforce Development' → 'iui_pillar_3_goal_1'"""
    pillar = re.search(r'Pillar\s+(\d+)', program_name, re.IGNORECASE)
    goal   = re.search(r'Goal\s+(\d+)',   program_name, re.IGNORECASE)
    p = pillar.group(1) if pillar else 'x'
    g = goal.group(1)   if goal   else 'x'
    return f"iui_pillar_{p}_goal_{g}"


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
    out_file = out_dir / f"{_program_file_stem(program_name)}.csv"
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
    rows = _post(ACTIVITIES_QUERY, {
        "input": {
            "pPortalId": portal_id,
            "pToken": TOKEN,
            "pProgramId": [program_id],
            "pLimit": 2000
        }
    })

    # Tag each activity with the program it was fetched under so transform
    # can map activities to the correct goal tab without re-querying.
    return [{**r, 'goal_names': [program_name]} for r in rows]


def get_units_by_portal(portal_id, portal_name, program_ids):
    """Fetch units connected to any of the given program IDs (no pLimit)."""
    rows = _post(UNITS_QUERY, {
        "input": {
            "pPortalId": portal_id,
            "pToken": TOKEN,
            "pProgramId": program_ids
        }
    })
    out_dir = DATA_DIR / "raw" / portal_name
    os.makedirs(out_dir, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "units.csv", index=False)
    return df


def run_fetch():
    portals = config['portals']
    for portal in portals:
        portal_name = portals[portal]['portal_name']
        portal_id   = portals[portal]['portal_id']
        programs    = portals[portal]['program_ids']
        all_activities = []

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
            all_activities.extend(acts)
            print(f"Fetched {len(acts)} activities for {portal_name} : {program_name}")

        # Fetch units connected to any of this portal's Goals
        valid_program_ids = [
            pid for pid in programs.values()
            if pid and pid != "None"
        ]
        if valid_program_ids:
            units_df = get_units_by_portal(portal_id, portal_name, valid_program_ids)
            print(f"Fetched {len(units_df)} units for {portal_name}")

        # Save all activities for this portal as a single CSV.
        # List columns (focuses, goal_names) are pipe-joined so they survive CSV round-trips.
        if all_activities:
            out_dir = DATA_DIR / "raw" / portal_name
            os.makedirs(out_dir, exist_ok=True)
            acts_df = pd.DataFrame(all_activities)
            for col in ('focuses', 'goal_names'):  # courses is a plain string, no pipe-join needed
                if col in acts_df.columns:
                    acts_df[col] = acts_df[col].apply(
                        lambda v: '|'.join(v) if isinstance(v, list) else (v or '')
                    )
            acts_df.to_csv(out_dir / "activities.csv", index=False)
            print(f"Saved {len(all_activities)} total activities for {portal_name}")
