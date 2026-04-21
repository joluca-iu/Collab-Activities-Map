// Initialize the map, centered on Indianapolis
const map = L.map("map").setView([39.7684, -86.1581], 10);

// Add a base tile layer
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors"
}).addTo(map);


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

function buildActivityHtml(activity) {
  const actUrl  = activity.url  ?? null;
  const actName = activity.name ?? 'Unnamed Activity';
  const focuses = Array.isArray(activity.focuses) ? activity.focuses : [];
  const contact = [activity.contactFirstname, activity.contactLastname].filter(Boolean).join(' ');
  const office  = activity.contactOffice ?? null;
  const units   = activity.units ?? null;

  const nameHtml = actUrl
    ? `<a href="${actUrl}" class="activity-name" target="_blank" rel="noopener">${actName}</a>`
    : `<span class="activity-name-plain">${actName}</span>`;

  const focusesLabelHtml = focuses.length
    ? `<div class="social-issue-line"><span class="field-label">Social Issue Addressed:</span> ${focuses.join(', ')}</div>`
    : '';

  const contactHtml = contact
    ? `<div class="meta-single-line"><span class="field-label">Contact:</span> ${contact}${office ? `, ${office}` : ''}</div>`
    : '';

  const unitsHtml = units
    ? `<div class="meta-single-line"><span class="field-label">Units:</span> ${units}</div>`
    : '';

  return `
    <div class="activity-item">
      ${nameHtml}
      ${focusesLabelHtml}
      ${contactHtml}
      ${unitsHtml}
    </div>`;
}

function buildEntityPanel(entity, entityIndex, popupId) {
  const name        = entity?.name ?? 'Unknown Organization';
  const url         = entity?.url;
  const description = entity?.description;
  const type        = entity?.type ?? '';
  const programs    = Array.isArray(entity?.programs) ? entity.programs : (entity?.programs ? [entity.programs] : []);
  const activities  = Array.isArray(entity?.activities) ? entity.activities : [];

  const nameHtml = url
    ? `<a href="${url}" class="org-name" target="_blank" rel="noopener">${name}</a>`
    : `<span class="org-name-plain">${name}</span>`;

  const typeHtml = type
    ? `<span class="org-type">${type}</span>`
    : '';

  const descHtml = description
    ? `<p class="org-description">${description}</p>`
    : `<p class="org-description org-description--empty"><em>No description available.</em></p>`;

  function activitiesForGoal(goalName) {
    const goalActivities = activities.filter(a => {
      const goals = Array.isArray(a.goal_names) ? a.goal_names : [];
      // Show if activity matches this goal, or has no goal mapping (show under all)
      return goals.length === 0 || goals.includes(goalName);
    });
    return goalActivities.length
      ? goalActivities.map(buildActivityHtml).join('')
      : `<div class="activity-item"><p class="activity-description"><em>No activities listed for this goal.</em></p></div>`;
  }

  const goalTabsHtml = programs.length
    ? programs.map((p, i) => `
        <button class="goal-tab${i === 0 ? ' active' : ''}"
                onclick="switchGoalTab('${popupId}', ${entityIndex}, ${i}); return false;">
          ${shortGoalLabel(p)}
        </button>`).join('')
    : '';

  const goalPanelsHtml = programs.length
    ? programs.map((p, i) => `
        <div class="goal-panel" data-goal="${i}" style="display:${i === 0 ? 'block' : 'none'};">
          ${activitiesForGoal(p)}
        </div>`).join('')
    : `<div class="goal-panel" data-goal="0">${activitiesForGoal('')}</div>`;

  const goalsSection = programs.length
    ? `<div class="goal-tab-bar">${goalTabsHtml}</div>${goalPanelsHtml}`
    : goalPanelsHtml;

  return `
    <div class="entity-panel" data-entity="${entityIndex}" style="display:${entityIndex === 0 ? 'block' : 'none'};">
      <div class="org-header">
        ${nameHtml}
        ${typeHtml}
      </div>
      <div class="iu-crimson-line"></div>
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

  schools_geojson.features.forEach(feature => {
    const coords = feature.geometry?.coordinates;
    if (!Array.isArray(coords) || coords.length < 2) return;

    const [lon, lat] = coords;
    const entities = feature.properties?.entity ?? [];
    const popupId  = `popup-${++_popupSeq}`;

    L.marker([lat, lon])
      .addTo(map)
      .bindPopup(buildPopupHtml(entities, popupId), { maxWidth: 540 });
  });
}
