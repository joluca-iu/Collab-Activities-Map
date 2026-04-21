import pandas as pd
import os
from utils.paths import DATA_DIR
import json
import re
def transform_community_partners():
    ##Read data in from raw
    raw_data_dir = DATA_DIR / "raw"

    all_data = []
    # activities_by_name: activity name -> activity dict (deduplicated across programs)
    activities_by_name = {}

    for campus in os.listdir(raw_data_dir):
        campus_dir = raw_data_dir / campus
        if not os.path.isdir(campus_dir):
            continue
        for file in os.listdir(campus_dir):
            if file.endswith("_community_partners.csv"):
                all_data.append(pd.read_csv(campus_dir / file))
            elif file.endswith("_activities.json"):
                with open(campus_dir / file, encoding='utf-8') as f:
                    acts = json.load(f)
                for act in acts:
                    name = act.get('name')
                    if name and name not in activities_by_name:
                        activities_by_name[name] = act

    ##Join all csv together
    combined_df = pd.concat(all_data, ignore_index=True)

    #Combine schools in same campus and aggregate their programs
    combined_df = combined_df.groupby(
        ['name', 'id', 'portal_name'], as_index=False
    ).agg({
        'street': 'first',
        'street2': 'first',
        'zipcode': 'first',
        'city': 'first',
        'state': 'first',
        'county': 'first',
        'country': 'first',
        'latitude': 'first',
        'longitude': 'first',
        'type': 'first',
        'description': 'first',
        'url': 'first',
        'phone': 'first',
        'email': 'first',
        'archived': 'first',
        'status': 'first',
        # Activities
        'activityName': lambda x: (re.sub(r"[\[\]']", "",', '.join(sorted(x.dropna().astype(str).unique()))).split(', ')),
        'activityCnt':  lambda x: x.dropna().astype(str).nunique(),
        # Roles / contacts
        'role': lambda x: ', '.join(sorted(x.dropna().astype(str).unique())),
        'contactNames': lambda x: ', '.join(sorted(x.dropna().astype(str).unique())),
        'contactEmails': lambda x: ', '.join(sorted(x.dropna().astype(str).unique())),
        # Courses / sections
        'courses': lambda x: ', '.join(sorted(x.dropna().astype(str).unique())),
        'sectionCnt': lambda x: x.dropna().astype(str).nunique(),
        # Units
        'unitNames': lambda x: ', '.join(sorted(x.dropna().astype(str).unique())),
        'unitCnt':  lambda x: x.dropna().astype(str).nunique(),
        'externalId': 'first',
        # Provenance
        'portal_name': lambda x: ', '.join(sorted(x.dropna().astype(str).unique())),
        'programs': lambda x: ', '.join(sorted(x.dropna().astype(str).unique())).split(', ')
    })

    #Fix externalId formatting
    combined_df['externalId'] = (
        combined_df['externalId']
        .astype(str)
        .str.replace(r'\.0$', '', regex=True)
        .str.pad(width=4, side='right', fillchar='0')
    )

    #Drop rows with critical missing values
    combined_df = combined_df.dropna(subset=['latitude', 'longitude', 'portal_name', 'name'])
    #Replace remaining NaNs with None for JSON compatibility
    combined_df = combined_df.where(pd.notnull(combined_df), None)
    
    combined_df = combined_df.rename(columns={"latitude": "lat", "longitude": "lon"})

    ###Combine entites with same lat/lon into single entry###
    #In the future once IDOE codes are imported to Colab, we can use those to distinguish public schools vs corporations vs charters
    
    def row_to_entity(row):
        entity = {k: row[k] for k in combined_df.columns.drop(['lat', 'lon'])}
        # Resolve activityName strings to full activity objects via name lookup
        act_names = row.get('activityName') or []
        if isinstance(act_names, str):
            act_names = [a.strip() for a in act_names.split(',') if a.strip()]
        entity['activities'] = [
            activities_by_name[n] for n in act_names if n in activities_by_name
        ]
        return entity
    
    # minimal columns for the map
    cols = ["externalId", "portal_name", "name", "lat", "lon", "programs", "activityName"]
    temp_df = combined_df[cols].copy() #Temp df to create grouped_df
    temp_df['entity'] = combined_df.apply(row_to_entity, axis=1)

    #Group by lat/lon
    grouped_df = temp_df.groupby(['lat', 'lon'])['entity'].apply(list).reset_index()
    #Convert to json
    grouped_json = grouped_df.to_dict(orient='records')

    ##Write combined data to cleaned folder
    cleaned_data_dir = DATA_DIR / "cleaned"

    os.makedirs(cleaned_data_dir, exist_ok=True)
    #Community partners where duplicate schools on same campus are combined
    combined_df.to_csv(cleaned_data_dir / "combined_community_partners_by_campus.csv", index=False)
    #Combined_Community_partners grouped by lat/lon so we only have unique map points
    with open(cleaned_data_dir / "community_partners_groupedby_location.json", 'w', encoding='utf-8') as f:
        json.dump(grouped_json, f, indent=2)

    return grouped_json