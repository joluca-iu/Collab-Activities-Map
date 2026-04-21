import pandas as pd
import os
from utils.paths import DATA_DIR
import json
import re
def transform_community_partners():
    ##Read data in from raw
    raw_data_dir = DATA_DIR / "raw"

    all_data = []
    # activities_map: org_id -> deduplicated list of activity dicts
    activities_map = {}

    for campus in os.listdir(raw_data_dir):
        campus_dir = raw_data_dir / campus
        if not os.path.isdir(campus_dir):
            continue
        for file in os.listdir(campus_dir):
            if file.endswith("_community_partners.csv"):
                df = pd.read_csv(campus_dir / file)
                all_data.append(df)
            elif file.endswith("_activities.json"):
                with open(campus_dir / file, encoding='utf-8') as f:
                    sidecar = json.load(f)
                for org_id, acts in sidecar.items():
                    if org_id not in activities_map:
                        activities_map[org_id] = []
                    existing_ids = {a.get('id') for a in activities_map[org_id]}
                    for act in acts:
                        if act.get('id') not in existing_ids:
                            activities_map[org_id].append(act)
                            existing_ids.add(act.get('id'))

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
        entity['activities'] = activities_map.get(str(row['id']), [])
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