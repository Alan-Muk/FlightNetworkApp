from pathlib import Path
import math
import pandas as pd
import networkx as nx

# ----------------------------
# Constants
# ----------------------------

AIRPORT_COLUMNS = [
    "id", "name", "city", "country", "iata", "icao",
    "lat", "lon", "alt", "tz", "dst", "tz_db", "type", "source"
]

ROUTE_COLUMNS = [
    "airline", "airline_id", "source", "source_id",
    "dest", "dest_id", "codeshare", "stops", "equipment"
]

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Data"
AIRPORTS_FILE = DATA_DIR / "airlines.dat"
ROUTES_FILE = DATA_DIR / "routes.dat"


# ----------------------------
# Utility Functions
# ----------------------------

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth in kilometers.
    """
    R = 6371  # Earth radius in km

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def _load_airports() -> pd.DataFrame:
    """
    Load and clean airport data.
    """
    if not AIRPORTS_FILE.exists():
        raise FileNotFoundError(f"Missing airports file: {AIRPORTS_FILE}")

    airports = pd.read_csv(
        AIRPORTS_FILE,
        header=None,
        names=AIRPORT_COLUMNS,
        na_values=["\\N"]
    )

    # Keep only rows with essential fields
    airports = airports.dropna(subset=["id", "name", "lat", "lon"])

    # Type conversions
    airports["id"] = airports["id"].astype(int)
    airports["lat"] = airports["lat"].astype(float)
    airports["lon"] = airports["lon"].astype(float)

    return airports


def _load_routes() -> pd.DataFrame:
    """
    Load and clean route data.
    """
    if not ROUTES_FILE.exists():
        raise FileNotFoundError(f"Missing routes file: {ROUTES_FILE}")

    routes = pd.read_csv(
        ROUTES_FILE,
        header=None,
        names=ROUTE_COLUMNS,
        na_values=["\\N"]
    )

    # Keep only routes with valid airport IDs
    routes = routes.dropna(subset=["source_id", "dest_id"])

    routes["source_id"] = routes["source_id"].astype(int)
    routes["dest_id"] = routes["dest_id"].astype(int)

    # Optional cleanup for stops
    routes["stops"] = pd.to_numeric(routes["stops"], errors="coerce").fillna(0).astype(int)

    return routes


def _filter_valid_routes(routes: pd.DataFrame, airports: pd.DataFrame) -> pd.DataFrame:
    """
    Remove routes that reference airports not present in the airport dataset.
    """
    valid_airport_ids = set(airports["id"])

    routes = routes[
        routes["source_id"].isin(valid_airport_ids) &
        routes["dest_id"].isin(valid_airport_ids)
    ]

    return routes


# ----------------------------
# Main Graph Builder
# ----------------------------

def load_graph() -> nx.DiGraph:
    """
    Build and return a directed graph of the flight network.

    Nodes = airports
    Edges = flight routes
    """

    airports = _load_airports()
    routes = _load_routes()
    routes = _filter_valid_routes(routes, airports)

    G = nx.DiGraph()

    # Add airport nodes
    for _, row in airports.iterrows():
        G.add_node(
            row["id"],
            name=row["name"],
            city=row["city"] if pd.notna(row["city"]) else "Unknown",
            country=row["country"] if pd.notna(row["country"]) else "Unknown",
            iata=row["iata"] if pd.notna(row["iata"]) else None,
            icao=row["icao"] if pd.notna(row["icao"]) else None,
            lat=row["lat"],
            lon=row["lon"]
        )

    skipped_edges = 0
    duplicate_edges = 0

    # Add route edges
    for _, row in routes.iterrows():
        source_id = row["source_id"]
        dest_id = row["dest_id"]

        if source_id == dest_id:
            skipped_edges += 1
            continue  # skip self-loops

        source = G.nodes[source_id]
        dest = G.nodes[dest_id]

        distance_km = haversine(
            source["lat"], source["lon"],
            dest["lat"], dest["lon"]
        )

        if G.has_edge(source_id, dest_id):
            duplicate_edges += 1
            continue  # avoid duplicate directed edges

        G.add_edge(
            source_id,
            dest_id,
            airline=row["airline"] if pd.notna(row["airline"]) else None,
            airline_id=row["airline_id"] if pd.notna(row["airline_id"]) else None,
            source_code=row["source"] if pd.notna(row["source"]) else None,
            dest_code=row["dest"] if pd.notna(row["dest"]) else None,
            codeshare=row["codeshare"] if pd.notna(row["codeshare"]) else None,
            stops=row["stops"],
            equipment=row["equipment"] if pd.notna(row["equipment"]) else None,
            distance_km=round(distance_km, 2)
        )

    print("Flight graph loaded successfully")
    print(f"Airports: {G.number_of_nodes()}")
    print(f"Routes: {G.number_of_edges()}")
    print(f"Skipped self-loops: {skipped_edges}")
    print(f"Skipped duplicate edges: {duplicate_edges}")

    return G