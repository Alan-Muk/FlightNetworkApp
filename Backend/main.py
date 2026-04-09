# backend/main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import networkx as nx
from graph import load_graph

app = FastAPI(title="Flight Network API")

# Allow frontend JS to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later if deployed
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    G = load_graph()
except Exception as e:
    raise RuntimeError(f"Failed to load graph: {e}")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "airports": G.number_of_nodes(),
        "routes": G.number_of_edges()
    }


@app.get("/airports")
def get_airports():
    features = []

    for node, data in G.nodes(data=True):
        if "lat" not in data or "lon" not in data:
            continue

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [data["lon"], data["lat"]]
            },
            "properties": {
                "id": node,
                "name": data.get("name"),
                "city": data.get("city"),
                "country": data.get("country"),
                "iata": data.get("iata")
            }
        })

    return {"type": "FeatureCollection", "features": features}


@app.get("/routes")
def get_routes(limit: int = Query(default=5000, ge=1, le=20000)):
    features = []

    for i, (u, v, edge_data) in enumerate(G.edges(data=True)):
        if i >= limit:
            break

        u_data = G.nodes[u]
        v_data = G.nodes[v]

        if "lat" not in u_data or "lon" not in u_data or "lat" not in v_data or "lon" not in v_data:
            continue

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [u_data["lon"], u_data["lat"]],
                    [v_data["lon"], v_data["lat"]]
                ]
            },
            "properties": {
                "source": u,
                "dest": v,
                "distance_km": round(edge_data.get("distance_km", 0), 2),
                "airline": edge_data.get("airline")
            }
        })

    return {"type": "FeatureCollection", "features": features}


@app.get("/shortest-path")
def shortest_path(
    source: int,
    target: int,
    mode: str = Query(default="hops", pattern="^(hops|distance)$")
):
    try:
        if mode == "distance":
            path = nx.shortest_path(G, source=source, target=target, weight="distance_km")
        else:
            path = nx.shortest_path(G, source=source, target=target)

        coords = []
        total_distance = 0

        for i, node in enumerate(path):
            node_data = G.nodes[node]
            coords.append({
                "id": node,
                "lat": node_data["lat"],
                "lon": node_data["lon"],
                "name": node_data["name"],
                "city": node_data["city"],
                "country": node_data["country"],
                "iata": node_data["iata"]
            })

            if i < len(path) - 1:
                edge = G[path[i]][path[i + 1]]
                total_distance += edge.get("distance_km", 0)

        return {
            "mode": mode,
            "airport_ids": path,
            "stops": max(len(path) - 1, 0),
            "total_distance_km": round(total_distance, 2),
            "path": coords
        }

    except nx.NodeNotFound:
        raise HTTPException(status_code=404, detail="Airport not found")
    except nx.NetworkXNoPath:
        raise HTTPException(status_code=404, detail="No path found")