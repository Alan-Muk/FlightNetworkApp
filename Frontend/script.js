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