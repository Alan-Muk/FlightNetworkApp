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

# ============================================================
# Notes on Backend API Implementation
# ============================================================
#
# This module provides a REST API for interacting with the
# flight network graph built from airport and route data.
#
# The API is implemented using FastAPI and exposes endpoints
# for:
#     - System health checks
#     - Airport data retrieval
#     - Route visualization data
#     - Shortest path calculations
#
#
# Application Startup
# -------------------
# The flight graph is loaded once during application startup
# using the `load_graph()` function from graph.py.
#
# This avoids rebuilding the graph on every request and keeps
# API responses fast.
#
# If graph loading fails, the application raises a RuntimeError
# during startup to prevent the API from running with invalid
# or incomplete data.
#
#
# CORS Configuration
# ------------------
# CORS middleware is enabled so frontend applications
# (such as a React or JavaScript map client) can access
# the API from a different origin.
#
# `allow_origins=["*"]` is acceptable for development,
# but should be restricted to trusted domains in production.
#
#
# Endpoint Overview
# -----------------
#
# GET /health
#     Returns API status information and graph statistics,
#     including the number of airports and routes loaded.
#
#
# GET /airports
#     Returns airport nodes as GeoJSON Point features.
#
#     Each feature contains:
#         - Geographic coordinates
#         - Airport metadata
#         - Airport identifiers
#
#     The GeoJSON format allows direct integration with
#     frontend mapping libraries such as:
#         - Leaflet
#         - Mapbox
#         - OpenLayers
#
#
# GET /routes
#     Returns route edges as GeoJSON LineString features.
#
#     A configurable `limit` parameter is used to prevent
#     extremely large responses that could slow down the
#     frontend or overload the browser.
#
#     Each route feature contains:
#         - Source airport
#         - Destination airport
#         - Airline information
#         - Route distance
#
#
# GET /shortest-path
#     Computes the shortest route between two airports.
#
#     Two routing modes are supported:
#
#     1. hops
#         Minimizes the number of flight connections.
#
#     2. distance
#         Minimizes total geographic travel distance using
#         the `distance_km` edge weight.
#
#     NetworkX shortest path algorithms are used internally.
#
#     The response includes:
#         - Ordered airport IDs
#         - Stop count
#         - Total distance
#         - Full airport metadata for each step in the path
#
#
# GeoJSON Design
# --------------
# Airports and routes are returned as GeoJSON FeatureCollections
# so they can be visualized directly on geographic map layers
# without additional transformation on the frontend.
#
#
# Error Handling
# --------------
# The API converts NetworkX exceptions into HTTP errors:
#
#     NodeNotFound
#         Returned when an airport ID does not exist.
#
#     NetworkXNoPath
#         Returned when no valid route exists between
#         the selected airports.
#
# Both cases return HTTP 404 responses with descriptive
# error messages.
#
#
# Performance Considerations
# --------------------------
# - The graph is stored in memory for fast access.
#
# - Route responses are capped using a configurable limit.
#
# - GeoJSON is used because it is lightweight and directly
#   compatible with browser-based mapping tools.
#
# - Shortest path calculations are computed dynamically
#   at request time using NetworkX algorithms.
#
#
# Potential Future Improvements
# -----------------------------
# - Add airport search endpoints
# - Add airline filtering
# - Add caching for shortest-path queries
# - Add authentication/rate limiting
# - Restrict CORS origins in production
# - Replace in-memory graph storage with a graph database
# - Add weighted routing based on time/cost instead of
#   only geographic distance
#
# ============================================================
