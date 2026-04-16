// Clear Filters Button Logic
const clearBtn = document.getElementById("clearFilters");

clearBtn.addEventListener("click", () => {
  document.querySelectorAll('#filters input[type="checkbox"]').forEach(cb => {
    cb.checked = false;
  });
  applyFilters();
});


// Builds a map of filter keys → checked state.
// Key format: "${portalClean}${programClean}" to match the applyFilters() lookup.
function check_filter_status() {
  const filterCheckBoxStatuses = {};

  document.querySelectorAll('#filters input.program').forEach(programCb => {
    const campus = programCb.dataset.campus ?? "";
    const campusClean = campus.replace(/\s+/g, '');
    const programClean = programCb.value.replace(/\s+/g, '');
    const key = `${campusClean}${programClean}`;
    filterCheckBoxStatuses[key] = programCb.checked;
  });

  return filterCheckBoxStatuses;
}


// Fetches schools.geojson, filters entities by selected programs, and re-renders markers.
function applyFilters() {
  const filter_status = check_filter_status();
  console.log("Current Filter Status:", filter_status);
  fetch("site_data/schools.geojson")
    .then(res => res.json())
    .then(geo_json_data => {
      const filtered_geo_json_data = {
        type: "FeatureCollection",
        features: geo_json_data.features
          .map(feature => {
            const entities = feature.properties?.entity ?? [];

            // Keep only entities that match at least one selected program
            const filteredEntities = entities.filter(entity => {
              const portal = entity?.portal_name ?? "";
              const programs = entity?.programs ?? [];

              return Array.isArray(programs) && programs.some(p => {
                const programClean = String(p).replace(/\s+/g, "");
                const portalClean = String(portal).replace(/\s+/g, "");
                const key = `${portalClean}${programClean}`;
                return filter_status[key] === true;
              });
            });

            // Return a new feature with the filtered entity array
            return {
              ...feature,
              properties: {
                ...feature.properties,
                entity: filteredEntities
              }
            };
          })
          // Drop features that have no entities left after filtering
          .filter(feature => (feature.properties?.entity ?? []).length > 0)
      };
      apply_markers(filtered_geo_json_data);
    })
    .catch(err => console.error("Error loading schools.geojson:", err));
}


// Re-apply filters whenever any checkbox changes
document.querySelectorAll('#filters input[type="checkbox"]').forEach(checkbox => {
  checkbox.addEventListener('change', () => applyFilters());
});

applyFilters(); // Initial load of markers based on default filter states
