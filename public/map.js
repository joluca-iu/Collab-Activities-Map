// Initialize the map, centered on Indianapolis
const map = L.map("map").setView([39.7684, -86.1581], 10);

// Add a base tile layer
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors"
}).addTo(map);

// Load and render Indianapolis campus border
fetch("site_data/indianapolis.geojson")
  .then(res => res.json())
  .then(borderData => {
    L.geoJSON(borderData, {
      style: {
        color: "#9b111e",
        weight: 2,
        fillOpacity: 0.05,
        fillColor: "#9b111e"
      }
    }).addTo(map);
  })
  .catch(err => console.warn("Could not load campus border:", err));


// Switch visible tab inside a popup. Exposed on window so inline onclick handlers can call it.
window.switchPopupTab = function(popupId, index) {
  try {
    const container = document.getElementById(popupId);
    if (!container) return;
    const panels = Array.from(container.querySelectorAll('.popup-entity'));
    const buttons = Array.from(container.querySelectorAll('.popup-tab-btn'));
    panels.forEach(p => p.style.display = 'none');
    buttons.forEach(b => b.classList.remove('active'));
    const target = panels.find(p => p.getAttribute('data-index') === String(index));
    const btn = buttons.find(b => b.getAttribute('data-index') === String(index));
    if (target) target.style.display = 'block';
    if (btn) btn.classList.add('active');
  } catch (e) {
    console.error('switchPopupTab error', e);
  }
};


// Load schools data and add markers
function apply_markers(schools_geojson) {
  if (!schools_geojson?.features) return;
  // Clear existing markers
  map.eachLayer(layer => {
    if (layer instanceof L.Marker) {
      map.removeLayer(layer);
    }
  });

  schools_geojson.features.forEach(feature => {
    const coords = feature.geometry?.coordinates;
    if (!Array.isArray(coords) || coords.length < 2) return;

    const [lon, lat] = coords;
    const entities = feature.properties?.entity ?? [];
    // Build a tabbed popup HTML where each entity becomes a tab
    let popup_html = "";
    const popupId = `popup-${Math.random().toString(36).substr(2, 9)}`;

    // Top menu (tabs)
    const tabButtons = entities.map((entity, i) => {
      const label = entity?.name ?? `Entity ${i + 1}`;
      return `<button class="popup-tab-btn" data-index="${i}" onclick="switchPopupTab('${popupId}', ${i}); return false;">${label}</button>`;
    }).join(' | ');

    // Entity panels
    const panels = entities.map((entity, i) => {
      const name = entity?.name ?? 'Unknown';
      const portal = entity?.portal_name ?? '';
      const programs = Array.isArray(entity?.programs) ? entity.programs : (entity?.programs ? [entity.programs] : []);
      const activities = Array.isArray(entity?.activityName) ? entity.activityName : (Array.isArray(entity?.activities) ? entity.activities : []);

      const programsHtml = programs.length ? programs.map(p => `<div class="rect-item">${p}</div>`).join('') : `<div class="rect-item">No programs</div>`;
      const activitiesHtml = activities.length ? activities.map(a => `<div class="rect-item">${a}</div>`).join('') : `<div class="rect-item">No activities</div>`;
      const campusesHtml = portal ? `<div class="rect-item">${portal}</div>` : `<div class="rect-item">None</div>`;

      return `
        <div class="popup-entity" data-index="${i}" style="display: ${i === 0 ? 'block' : 'none'};">
          <h2 class="entity-name">${name}</h2>
          <div class="section-label">Campus</div>
          <div class="red-rect campuses">${campusesHtml}</div>

          <div class="section-label">Programs</div>
          <div class="red-rect programs">${programsHtml}</div>

          <div class="section-label">Activities</div>
          <div class="red-rect activities">${activitiesHtml}</div>
        </div>
      `;
    }).join('');

    if (!entities.length) {
      popup_html = `<div id="${popupId}" class="popup-container"><p>No details available.</p></div>`;
    } else {
      popup_html = `
        <div id="${popupId}" class="popup-container">
          <div class="popup-top-menu">${tabButtons}</div>
          <div class="iu-crimson-line"></div>
          <div class="popup-entities">${panels}</div>
        </div>
      `;
    }

    // Create marker and bind popup
    L.marker([lat, lon])
      .addTo(map)
      .bindPopup(popup_html);
  });
}
