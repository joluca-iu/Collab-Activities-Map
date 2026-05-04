// Initialize the map, centered on Indianapolis
const map = L.map("map").setView([39.7684, -86.1581], 10);

// Add a base tile layer
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors"
}).addTo(map);


// ── Marker icons ─────────────────────────────────────────────────────────────

const defaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
});



// ── Helpers ──────────────────────────────────────────────────────────────────

// "IUI 2030 Strategic Plan Pillar 3, Goal 1: Workforce Development"
//   → "Goal 1: Workforce Development"
function shortGoalLabel(program) {
  const parts = program.split(', ');
  return parts.length > 1 ? parts.slice(1).join(', ') : program;
}


// ── Tab switching ─────────────────────────────────────────────────────────────

function activateTab(root, panelClass, tabClass, dataAttr, index) {
  root.querySelectorAll('.' + panelClass).forEach(p => p.style.display = 'none');
  root.querySelectorAll('.' + tabClass).forEach(b => b.classList.remove('active'));
  const panel = root.querySelector(`[data-${dataAttr}="${index}"]`);
  const btn   = root.querySelectorAll('.' + tabClass)[index];
  if (panel) panel.style.display = 'block';
  if (btn)   btn.classList.add('active');
}

window.switchEntityTab = function(popupId, index) {
  try {
    const container = document.getElementById(popupId);
    if (!container) return;
    activateTab(container, 'entity-panel', 'entity-tab', 'entity', index);
  } catch (e) { console.error('switchEntityTab error', e); }
};

window.switchGoalTab = function(popupId, entityIndex, goalIndex) {
  try {
    const panel = document.querySelector(`#${popupId} .entity-panel[data-entity="${entityIndex}"]`);
    if (!panel) return;
    activateTab(panel, 'goal-panel', 'goal-tab', 'goal', goalIndex);
  } catch (e) { console.error('switchGoalTab error', e); }
};


// ── Popup builder ─────────────────────────────────────────────────────────────

let _popupSeq = 0;

// JSON.stringify a value for safe embedding inside a double-quoted HTML attribute.
// Browsers convert &quot; → " before handing the string to the JS engine.
function attrJson(v) {
  return JSON.stringify(v).replace(/"/g, '&quot;');
}

function buildActivityHtml(activity, currentEntityId, goalLabel) {
  const actId   = activity.id   ?? null;
  const actName = activity.name ?? 'Unnamed Activity';
  const unitLinks = Array.isArray(activity.unit_links) ? activity.unit_links : [];

  const actUrl  = actId ? `https://he.cecollaboratory.com/iui/activities/${actId}` : null;
  const learnMoreHtml = actUrl
    ? `<a href="${actUrl}" class="learn-more-btn" target="_blank" rel="noopener">Learn more about program</a>`
    : '';

  const nameHtml = `
    <div class="activity-name-header">
      <div class="activity-name-plain">${actName}</div>
      <span class="goal-label">${goalLabel || 'Program'}</span>
    </div>`;

  const unitsHtml = unitLinks.length
    ? `<div class="meta-single-line"><span class="field-label">IU Units:</span> ${
        unitLinks.map(u => u.url
          ? `<a href="${u.url}" class="unit-link" target="_blank" rel="noopener">${u.name}</a>`
          : u.name
        ).join(' | ')
      }</div>`
    : '';

  // Register pre-computed partner list keyed by activity id
  const communityPartners = Array.isArray(activity.community_partners)
    ? activity.community_partners : [];
  window._activityPartners = window._activityPartners || {};
  window._activityPartners[actId] = communityPartners;

  const filterBtnHtml = `<button class="activity-filter-btn"
    onclick="showOnlyActivityPartners(${attrJson(actId)}); return false;">
    Display other partners
  </button>`;

  const actionRowHtml = (learnMoreHtml || filterBtnHtml)
    ? `<div class="activity-action-row">${learnMoreHtml}${filterBtnHtml}</div>`
    : '';

  return `
    <div class="activity-item">
      ${nameHtml}
      ${actionRowHtml}
      ${unitsHtml}
    </div>`;
}

// ── Activity partner highlight ────────────────────────────────────────────────

window.showOnlyActivityPartners = function(actId) {
  // Visually uncheck all filter checkboxes (no change event fired, so applyFilters won't run)
  document.querySelectorAll('#filters input[type="checkbox"]').forEach(cb => {
    cb.checked = false;
  });

  const partnerIds = new Set(
    (window._activityPartners?.[actId] ?? []).map(p => p.id)
  );

  Object.entries(window._markerRegistry ?? {}).forEach(([entityId, entry]) => {
    const isPartner = partnerIds.has(Number(entityId)) || partnerIds.has(entityId);
    const opacity = isPartner ? '1' : '0';
    const events  = isPartner ? '' : 'none';
    const el = entry.marker.getElement();
    if (el) { el.style.opacity = opacity; el.style.pointerEvents = events; }
    const shadow = entry.marker._shadow;
    if (shadow) { shadow.style.opacity = opacity; }
  });
};

window.resetMarkerVisibility = function() {
  Object.values(window._markerRegistry ?? {}).forEach(entry => {
    const el = entry.marker.getElement();
    if (el) { el.style.opacity = '1'; el.style.pointerEvents = ''; }
    const shadow = entry.marker._shadow;
    if (shadow) { shadow.style.opacity = '1'; }
  });
};


// ── Partner dropdown helpers ──────────────────────────────────────────────────

window.toggleActivityPartners = function(actKey, listId, currentEntityId) {
  const listEl = document.getElementById(listId);
  if (!listEl) return;

  // Toggle off if already visible
  if (listEl.style.display !== 'none' && listEl.style.display !== '') {
    listEl.style.display = 'none';
    return;
  }

  // Read pre-computed partner list; filter out the current org
  const partners = (window._activityPartners?.[actKey] ?? [])
    .filter(p => p.id !== currentEntityId);

  listEl.innerHTML = partners.length
    ? partners.map(p =>
        `<div class="partner-link"
          onclick="openEntityPopup(${attrJson(p.id)}, ${attrJson(p.name)})"
        >${p.name}</div>`
      ).join('')
    : '<div class="partner-link-empty">No other partners found.</div>';

  listEl.style.display = 'block';
};

window.openEntityPopup = function(entityId, entityName) {
  const entry = window._markerRegistry?.[entityId];
  if (!entry) return;
  map.closePopup();
  entry.marker.openPopup();
  // If the target entity is not the first tab, switch to it
  if (entry.entityIndex > 0) {
    setTimeout(() => {
      document.querySelectorAll('.entity-tab').forEach(tab => {
        if (tab.textContent.trim() === entityName) tab.click();
      });
    }, 50);
  }
};

function buildEntityPanel(entity, entityIndex, popupId) {
  const name        = entity?.name ?? 'Unknown Organization';
  const url         = entity?.url;
  const description = entity?.description;
  const type        = entity?.type ?? '';
  const programs    = Array.isArray(entity?.programs) ? entity.programs : (entity?.programs ? [entity.programs] : []);
  const activities  = Array.isArray(entity?.activities) ? entity.activities : [];

  const nameHtml = `
    <div class="org-name-header">
      <div class="org-name-plain">${name}</div>
    </div>`;

  const typeHtml = type
    ? `<span class="org-type">${type}</span>`
    : '';

  const descHtml = description
    ? `<p class="org-description">${description}</p>`
    : '';

  function goalNumber(fullName) {
    const m = String(fullName).match(/Goal\s+(\d+)/i);
    return m ? parseInt(m[1]) : 999;
  }

  const activitiesHtml = activities.map(a => {
    const goals = Array.isArray(a.goal_names) ? a.goal_names : [];
    const sortedGoals = [...goals].sort((x, y) => goalNumber(x) - goalNumber(y));
    const label = sortedGoals.map(shortGoalLabel).join('<br>') || 'Program';
    return buildActivityHtml(a, entity?.id ?? null, label);
  }).join('');

  const goalPanelsHtml = `<div class="goal-panel">${activitiesHtml}</div>`;

  const goalsSection = `<div class="programs-heading">Programs</div>${goalPanelsHtml}`;

  return `
    <div class="entity-panel" data-entity="${entityIndex}" style="display:${entityIndex === 0 ? 'block' : 'none'};">
      <div class="org-header">
        ${nameHtml}
        ${typeHtml}
      </div>
      ${descHtml}
      ${goalsSection}
    </div>`;
}

function buildPopupHtml(entities, popupId) {
  if (!entities.length) {
    return `<div id="${popupId}" class="popup-container"><p class="org-description">No details available.</p></div>`;
  }

  const entityTabBarHtml = entities.length > 1
    ? `<div class="entity-tab-bar">
        ${entities.map((e, i) => `
          <button class="entity-tab${i === 0 ? ' active' : ''}"
                  onclick="switchEntityTab('${popupId}', ${i}); return false;">
            ${e?.name ?? `Entity ${i + 1}`}
          </button>`).join('')}
       </div>`
    : '';

  const panelsHtml = entities.map((e, i) => buildEntityPanel(e, i, popupId)).join('');

  return `
    <div id="${popupId}" class="popup-container">
      ${entityTabBarHtml}
      ${panelsHtml}
    </div>`;
}


// ── Marker rendering ──────────────────────────────────────────────────────────

function apply_markers(schools_geojson) {
  if (!schools_geojson?.features) return;

  // Clear existing markers only (preserve tile/GeoJSON layers)
  map.eachLayer(layer => {
    if (layer instanceof L.Marker) map.removeLayer(layer);
  });

  // Reset registry so openEntityPopup() can find the new markers
  window._markerRegistry = {};

  schools_geojson.features.forEach(feature => {
    const coords = feature.geometry?.coordinates;
    if (!Array.isArray(coords) || coords.length < 2) return;

    const [lon, lat] = coords;
    const entities = feature.properties?.entity ?? [];
    const popupId  = `popup-${++_popupSeq}`;

    const marker = L.marker([lat, lon])
      .addTo(map)
      .bindPopup(buildPopupHtml(entities, popupId), { maxWidth: 540 });

    // Register each entity so partner dropdowns can navigate to it
    entities.forEach((entity, entityIndex) => {
      if (entity?.id) {
        window._markerRegistry[entity.id] = { marker, entityIndex };
      }
    });
  });
}
