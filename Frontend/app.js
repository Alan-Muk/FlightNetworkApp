const map = L.map('map').setView([20,0], 2);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18
}).addTo(map);

async function loadAirports() {
    const res = await fetch('http://127.0.0.1:8000/airports');
    const data = await res.json();
    L.geoJSON(data, {
        onEachFeature: (feature, layer) => {
            layer.bindPopup(`${feature.properties.name}, ${feature.properties.city}, ${feature.properties.country}`);
        }
    }).addTo(map);
}

async function loadRoutes() {
    const res = await fetch('http://127.0.0.1:8000/routes');
    const data = await res.json();
    L.geoJSON(data, {color: 'blue', weight: 1}).addTo(map);
}

loadAirports();
loadRoutes();