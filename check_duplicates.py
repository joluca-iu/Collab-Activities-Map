import json

# Load schools data
with open('ActivitiesMap/site/data/schools.json', 'r') as f:
    schools = json.load(f)

# Dictionary to track unique lat/lon
unique_coords = {}
duplicates = []

for school in schools:
    lat = school.get('lat')
    lon = school.get('lon')
    if lat is not None and lon is not None:
        coord = (lat, lon)
        if coord in unique_coords:
            duplicates.append((school, unique_coords[coord]))
        else:
            unique_coords[coord] = school

print(f"Total schools: {len(schools)}")
print(f"Unique coordinates: {len(unique_coords)}")
print(f"Duplicate coordinates: {len(duplicates)}")

if duplicates:
    print("\nDuplicate schools:")
    for dup in duplicates:
        print(f"School: {dup[0]['name']} at ({dup[0]['lat']}, {dup[0]['lon']})")
        print(f"Duplicate: {dup[1]['name']} at ({dup[1]['lat']}, {dup[1]['lon']})")
        print("---")
else:
    print("No duplicates found.")