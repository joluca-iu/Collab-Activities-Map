// Syncs the campus checkbox state based on its programs' states
function syncCampusFromPrograms(detailsEl) {
  const campusCheckBox = detailsEl.querySelector('summary input.campus');     //Campus Checkbox Variable
  const programCheckBoxs = Array.from(detailsEl.querySelectorAll('.nested input.program')); //Program Checkbox Variables

  if (!campusCheckBox || programCheckBoxs.length === 0) return;

  const checkedCount = programCheckBoxs.filter(CheckBox => CheckBox.checked).length;

  if (checkedCount === 0) {                         // No programs checked -> uncheck campus
    campusCheckBox.checked = false;
    campusCheckBox.indeterminate = false;
  } else if (checkedCount === programCheckBoxs.length) {  // All programs checked -> check campus
    campusCheckBox.checked = true;
    campusCheckBox.indeterminate = false;
  } else {                                          // Some programs checked -> indeterminate campus
    campusCheckBox.checked = false;          
    campusCheckBox.indeterminate = true;     
  }
}
// Sets all program checkboxes under a campus to the specified checked state
function setPrograms(detailsEl, checked) {
  const programCheckBoxs = detailsEl.querySelectorAll('.nested input.program');
  programCheckBoxs.forEach(CheckBox => (CheckBox.checked = checked));
}

// Event Listeners Setup
// 1) Parent -> children
document.querySelectorAll('.campus-details').forEach(detailsEl => {
  const campusCheckBox = detailsEl.querySelector('summary input.campus');
  if (!campusCheckBox) return;

  campusCheckBox.addEventListener('change', () => {
    setPrograms(detailsEl, campusCheckBox.checked);
    campusCheckBox.indeterminate = false; // parent action resolves partial state
  });

  // 2) Children -> parent
  detailsEl.querySelectorAll('.nested input.program').forEach(programCheckBox => {
    programCheckBox.addEventListener('change', () => {
      syncCampusFromPrograms(detailsEl);
    });
  });

  // Initialize state on page load (in case some are pre-checked)
  syncCampusFromPrograms(detailsEl);
});


// Clear Filters Button Logic
const clearBtn = document.getElementById("clearFilters");

clearBtn.addEventListener("click", () => {
  // Uncheck everything
  document.querySelectorAll('#filters input[type="checkbox"]').forEach(CheckBox => {
    CheckBox.checked = false;
    CheckBox.indeterminate = false; // important for campus checkboxes
  });

  //all menus collapsed after clearing
  document.querySelectorAll('#filters details.campus-details').forEach(d => d.open = false);

  applyFilters();
});



  //Need to reload markers. Maybe wrapping the reading  and writing  in map.js in function and calling it on any eventListener
  //Reload order will be a eventlistener on each button that triggers check_filter_status() which will return which check boxes are selected.
function check_filter_status() {
  const filterCheckBoxStatuses = {};

  // loop over each campus <details>
  document.querySelectorAll('.campus-details').forEach(detailsEl => {
    const campusCb = detailsEl.querySelector('input.campus');
    if (!campusCb) return;

    const campusName = campusCb.value.replace(/\s+/g, '');

    // loop over program checkboxes under this campus
    const programs = detailsEl.querySelectorAll('.nested input.program');
    programs.forEach(programCb => {
      const programName = programCb.value.replace(/\s+/g, '');
      const key = `${campusName}${programName}`;

      filterCheckBoxStatuses[key] = programCb.checked;
    });
  });

  return filterCheckBoxStatuses;
}


//applyFilters(); Will filter the geojson and will call add_markers from map.js 
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

            // Keep only entities that match at least one selected campus+program
            const filteredEntities = entities.filter(entity => {
              const portal = entity?.portal_name ?? "";     // campus
              const programs = entity?.programs ?? [];      // array like ["CCG"]

              // entity matches if ANY of its programs are checked for its portal
              return Array.isArray(programs) && programs.some(p => {
                const programClean = String(p).replace(/\s+/g, "");
                const portalClean = String(portal).replace(/\s+/g, "");
                const key = `${portalClean}${programClean}`; // e.g., "BloomingtonCCG"
                return filter_status[key] === true;
              });
            });

              // Return a new feature with entity array replaced
              return {
                ...feature,
                properties: {
                  ...feature.properties,
                  entity: filteredEntities
                }
              };
          })
          //drop features that have no entities left after filtering
          .filter(feature => (feature.properties?.entity ?? []).length > 0)
      };
      apply_markers(filtered_geo_json_data);
    })
    .catch(err => console.error("Error loading schools.geojson:", err));
}



//EventListeners for each filter checkbox to update map on change
document.querySelectorAll('#filters input[type="checkbox"]').forEach(checkbox => {
  checkbox.addEventListener('change', (e) => {
    applyFilters();
  });
});

applyFilters(); // Initial load of markers based on default filter states





