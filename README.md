
# Flight Network Map

This project visualizes global flight routes using OpenFlights data.

- Backend: FastAPI + NetworkX
- Frontend: Leaflet.js
- Features:
  - Interactive map of airports
  - Flight routes visualization
  - Shortest path between airports

## How to run

1. Install dependencies:
=======
# Project Structure

FlightNetworkApp/
│
├── Backend/
│   ├── main.py
│   ├── graph.py
│   ├── requirements.txt
│   └── data/
│       ├── airports.dat
│       └── routes.dat
│
├── Frontend/
│   ├── index.html
│   ├── script.js
│   └── styles.css
│
└── README.md

# Flight Network App

A full-stack flight route visualization and pathfinding application that models global airports and airline routes as a directed graph using real-world aviation data.

## Overview

FlightNetworkApp allows users to explore airport connections on an interactive world map and compute routes between airports using graph-based pathfinding.

The application uses:

- **FastAPI** for the backend API
- **NetworkX** for graph modeling and shortest-path computation
- **Leaflet.js** for interactive map visualization
- **OpenFlights** data for airports and airline routes

---

## Features

- Interactive map of global airports
- Airport popups with metadata
- Airline route visualization
- Shortest path calculation between airports
- Graph-based modeling of airport connections
- GeoJSON-like API responses for easy frontend integration

---

## Tech Stack

### Backend
- Python
- FastAPI
- Pandas
- NetworkX

### Frontend
- JavaScript
- Leaflet.js
- OpenStreetMap tiles

### Data
- OpenFlights airport and route dataset

---

## How It Works

The project models the flight network as a **directed graph**:

- **Airports** are stored as graph **nodes**
- **Routes** are stored as graph **edges**

Each airport includes metadata such as:

- name
- city
- country
- IATA code
- coordinates

The backend exposes endpoints that return airport and route data for map rendering, as well as a shortest-path endpoint that computes routes between two airports.

---

## API Endpoints

### `GET /health`
Returns backend status and graph statistics.

### `GET /airports`
Returns all airports as GeoJSON-like point features.

### `GET /routes`
Returns all routes as GeoJSON-like line features.

### `GET /shortest-path?source=<id>&target=<id>&mode=<mode>`
Returns the computed route between two airports.

#### Query Parameters
- `source` → source airport ID
- `target` → destination airport ID
- `mode` → routing mode:
  - `hops` = fewest connections
  - `distance` = shortest geographic distance

---

## Example Use Cases

- Visualize global flight connectivity
- Explore airport networks
- Compare route paths between cities
- Demonstrate graph-based pathfinding on real-world data

---

## Screenshots

> Add screenshots here:
- Airport map
- Route visualization
- Shortest path result
- Route search UI

---

## How to Run

## 1. Clone the repository

```bash
git clone https://github.com/Alan-Muk/FlightNetworkApp.git
cd FlightNetworkApp
>>>>>>> 4095a69 (Updated Planned approach to the project)
