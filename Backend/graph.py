import pandas as pd
import networkx as nx

def load_graph():
    airports_cols = [
        "id","name","city","country","iata","icao",
        "lat","lon","alt","tz","dst","tz_db","type","source"
    ]
    routes_cols = [
        "airline","airline_id","source","source_id",
        "dest","dest_id","codeshare","stops","equipment"
    ]

    airports = pd.read_csv("data/airports.dat", header=None, names=airports_cols)
    routes = pd.read_csv("data/routes.dat", header=None, names=routes_cols)

    # Clean routes
    routes = routes[(routes["source_id"] != "\\N") & (routes["dest_id"] != "\\N")]
    routes["source_id"] = routes["source_id"].astype(int)
    routes["dest_id"] = routes["dest_id"].astype(int)

    G = nx.DiGraph()

    # Add nodes
    for _, row in airports.iterrows():
        G.add_node(
            row["id"],
            name=row["name"],
            city=row["city"],
            country=row["country"],
            iata=row["iata"],
            lat=row["lat"],
            lon=row["lon"]
        )

    # Add edges
    for _, row in routes.iterrows():
        G.add_edge(row["source_id"], row["dest_id"])

    return G