# backend/app.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import networkx as nx
from graph import load_graph

app = FastAPI(title="Flight Network API")

# Allow frontend JS to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

G = load_graph()

@app.get("/airports")
def get_airports():
    # Return all airports as geoJSON-like features
    features = []
    for node, data in G.nodes(data=True):
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [data["lon"], data["lat"]]},
            "properties": {"id": node, "name": data["name"], "city": data["city"], "country": data["country"], "iata": data["iata"]}
        })
    return {"type": "FeatureCollection", "features": features}

@app.get("/routes")
def get_routes():
    # Return all routes as geoJSON-like features
    features = []
    for u, v in G.edges():
        u_data = G.nodes[u]
        v_data = G.nodes[v]
        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[u_data["lon"], u_data["lat"]], [v_data["lon"], v_data["lat"]]]},
            "properties": {"source": u, "dest": v}
        })
    return {"type": "FeatureCollection", "features": features}

@app.get("/shortest-path")
def shortest_path(source: int, target: int):
    try:
        path = nx.shortest_path(G, source=source, target=target)
        coords = [{"lat": G.nodes[n]["lat"], "lon": G.nodes[n]["lon"], "name": G.nodes[n]["name"]} for n in path]
        return {"path": coords}
    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail="No path found")