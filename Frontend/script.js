const API_BASE = "http://127.0.0.1:8000";

const map = L.map("map").setView([20, 0], 2);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 18,
  attribution: "&copy; OpenStreetMap contributors"
}).addTo(map);

let airportsData = [];
let airportsLayer = null;
let routesLayer = null;
let pathLayer = null;
let routesVisible = false;

const sourceSelect = document.getElementById("sourceSelect");
const targetSelect = document.getElementById("targetSelect");
const modeSelect = document.getElementById("modeSelect");
const statusEl = document.getElementById("status");
const routeInfo = document.getElementById("routeInfo");
const routeSummary = document.getElementById("routeSummary");
const routeList = document.getElementById("routeList");

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  return await res.json();
}

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.background = isError ? "#f8d7da" : "#fff3cd";
  statusEl.style.borderColor = isError ? "#f5c2c7" : "#ffe69c";
}

function populateAirportSelects(features) {
  const sorted = [...features].sort((a, b) =>
    a.properties.name.localeCompare(b.properties.name)
  );

  for (const feature of sorted) {
    const airport = feature.properties;
    const label = `${airport.name} (${airport.iata || "N/A"}) - ${airport.city}, ${airport.country}`;

    const option1 = document.createElement("option");
    option1.value = airport.id;
    option1.textContent = label;

    const option2 = document.createElement("option");
    option2.value = airport.id;
    option2.textContent = label;

    sourceSelect.appendChild(option1);
    targetSelect.appendChild(option2);
  }
}

async function loadAirports() {
  try {
    const data = await fetchJSON(`${API_BASE}/airports`);
    airportsData = data.features;

    airportsLayer = L.geoJSON(data, {
      pointToLayer: (feature, latlng) =>
        L.circleMarker(latlng, {
          radius: 4
        }),
      onEachFeature: (feature, layer) => {
        const props = feature.properties;
        layer.bindPopup(`
          <strong>${props.name}</strong><br>
          ${props.city}, ${props.country}<br>
          IATA: ${props.iata || "N/A"}<br>
          Airport ID: ${props.id}
        `);
      }
    }).addTo(map);

    populateAirportSelects(airportsData);
    setStatus("Airports loaded. Select two airports to find a route.");
  } catch (err) {
    console.error(err);
    setStatus("Failed to load airports.", true);
  }
}

async function loadRoutes() {
  try {
    const data = await fetchJSON(`${API_BASE}/routes?limit=3000`);

    if (routesLayer) {
      map.removeLayer(routesLayer);
    }

    routesLayer = L.geoJSON(data, {
      style: {
        color: "#1f6feb",
        weight: 1,
        opacity: 0.35
      }
    });

    if (routesVisible) {
      routesLayer.addTo(map);
    }
  } catch (err) {
    console.error(err);
    setStatus("Failed to load routes.", true);
  }
}

function clearPath() {
  if (pathLayer) {
    map.removeLayer(pathLayer);
    pathLayer = null;
  }

  routeInfo.classList.add("hidden");
  routeSummary.innerHTML = "";
  routeList.innerHTML = "";
}

async function findShortestPath() {
  const source = sourceSelect.value;
  const target = targetSelect.value;
  const mode = modeSelect.value;

  if (!source || !target) {
    setStatus("Please select both source and target airports.", true);
    return;
  }

  if (source === target) {
    setStatus("Source and target airports must be different.", true);
    return;
  }

  clearPath();
  setStatus("Finding route...");

  try {
    const data = await fetchJSON(
      `${API_BASE}/shortest-path?source=${source}&target=${target}&mode=${mode}`
    );

    const coords = data.path.map(p => [p.lat, p.lon]);

    pathLayer = L.polyline(coords, {
      weight: 4,
      opacity: 0.9
    }).addTo(map);

    map.fitBounds(pathLayer.getBounds(), { padding: [30, 30] });

    routeSummary.innerHTML = `
      <p><strong>Mode:</strong> ${data.mode === "distance" ? "Shortest Distance" : "Fewest Connections"}</p>
      <p><strong>Stops:</strong> ${data.stops}</p>
      <p><strong>Total Distance:</strong> ${data.total_distance_km} km</p>
    `;

    for (const airport of data.path) {
      const li = document.createElement("li");
      li.textContent = `${airport.name} (${airport.iata || "N/A"}) - ${airport.city}, ${airport.country}`;
      routeList.appendChild(li);
    }

    routeInfo.classList.remove("hidden");
    setStatus("Route found successfully.");
  } catch (err) {
    console.error(err);
    setStatus("No route found or request failed.", true);
  }
}

document.getElementById("findPathBtn").addEventListener("click", findShortestPath);

document.getElementById("clearPathBtn").addEventListener("click", () => {
  clearPath();
  setStatus("Route cleared.");
});

document.getElementById("toggleRoutesBtn").addEventListener("click", () => {
  routesVisible = !routesVisible;

  if (routesLayer) {
    if (routesVisible) {
      routesLayer.addTo(map);
      setStatus("Routes displayed.");
    } else {
      map.removeLayer(routesLayer);
      setStatus("Routes hidden.");
    }
  }
});

loadAirports();
loadRoutes();

// ============================================================
// Notes on Frontend Map Application
// ============================================================
//
// This frontend application provides an interactive geographic
// visualization of the flight network using Leaflet.js.
//
// The application communicates with the FastAPI backend to:
//
//     - Load airport data
//     - Load route data
//     - Compute shortest flight paths
//     - Display geographic network information on a map
//
//
// Core Technologies
// -----------------
// - Leaflet.js
//     Used for interactive map rendering and geographic layers.
//
// - OpenStreetMap
//     Provides the base tile layer for geographic visualization.
//
// - Fetch API
//     Used for asynchronous communication with the backend API.
//
// - GeoJSON
//     Used as the data exchange format for airports and routes.
//
//
// Application State
// -----------------
// Several global variables are used to track map layers and
// application state:
//
//     airportsLayer
//         Stores rendered airport markers.
//
//     routesLayer
//         Stores rendered route lines.
//
//     pathLayer
//         Stores the currently displayed shortest path.
//
//     routesVisible
//         Tracks whether route overlays are currently enabled.
//
//
// Map Initialization
// ------------------
// The map is initialized with:
//
//     - A global center point
//     - A low zoom level for world-scale visualization
//     - OpenStreetMap tiles as the base layer
//
// Airports and routes are then loaded dynamically from the API.
//
//
// Airport Loading
// ---------------
// Airport data is requested from:
//
//     GET /airports
//
// Airports are rendered as Leaflet circle markers and include:
//
//     - Airport name
//     - City and country
//     - IATA code
//     - Airport ID
//
// Popup information is attached to each marker.
//
// Airport data is also used to populate the source and target
// dropdown menus for shortest path selection.
//
//
// Route Loading
// --------------
// Route data is requested from:
//
//     GET /routes
//
// Routes are rendered as GeoJSON LineString features.
//
// A configurable limit is used to reduce rendering overhead
// because drawing thousands of geographic lines in the browser
// can impact performance.
//
// Route visibility can be toggled on and off dynamically.
//
//
// Shortest Path Functionality
// ---------------------------
// Users can select:
//
//     - Source airport
//     - Destination airport
//     - Routing mode
//
// Two routing modes are supported:
//
//     1. hops
//         Finds the route with the fewest flight connections.
//
//     2. distance
//         Finds the geographically shortest route.
//
// The frontend sends requests to:
//
//     GET /shortest-path
//
// The returned airport sequence is converted into a Leaflet
// polyline and displayed on the map.
//
//
// Route Visualization
// -------------------
// The computed shortest path is:
//
//     - Rendered as a highlighted polyline
//     - Automatically zoomed into using fitBounds()
//     - Displayed alongside route summary information
//
// Additional route details shown include:
//
//     - Number of stops
//     - Total travel distance
//     - Ordered airport list
//
//
// Error Handling
// --------------
// Basic error handling is implemented for:
//
//     - Failed API requests
//     - Invalid airport selections
//     - Missing routes between airports
//
// User-friendly status messages are displayed in the UI.
//
//
// Performance Considerations
// --------------------------
// - Route rendering is capped to reduce browser load.
//
// - Existing layers are removed before re-rendering to avoid
//   duplicate map objects.
//
// - GeoJSON is used because it integrates efficiently with
//   Leaflet.
//
// - Path rendering occurs only when requested by the user.
//
//
// Potential Future Improvements
// -----------------------------
// - Add airport search/autocomplete
// - Add route animation
// - Add airline-based filtering
// - Add clustering for dense airport regions
// - Add loading indicators/spinners
// - Add dark mode map themes
// - Add mobile responsiveness improvements
// - Cache API responses for performance
// - Add airport statistics and analytics
// - Support real-time flight data integration
//
// ============================================================
