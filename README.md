# AIS Simulation Solution

## Overview

This Python-based solution simulates the movement of vessels along dynamically generated maritime routes using `searoute-py`. It generates AIS position reports with `pyais`, streams them over WebSocket, stores them in a SQLite database using SQLAlchemy, and displays them via a Flask-powered web dashboard.

---

## Folder Structure
```bash
ais_simulation/
├── data/
│   ├── ports.csv          # Sample port data
│   └── ais_data.db        # SQLite database (created if absent)
├── src/
│   ├── __init__.py        # Makes src a Python package
│   ├── route_generator.py # Route generation logic
│   ├── vessel.py          # Vessel simulation and AIS message generation
│   ├── database.py        # SQLAlchemy database operations
│   ├── websocket_server.py # WebSocket streaming and receiving
│   └── dashboard.py        # Flask dashboard and API
├── templates/
│   └── index.html         # Flask template for dashboard
├── static/
│   ├── css/
│   │   └── style.css      # Dashboard styles
│   └── js/
│       └── map.js         # JavaScript for Leaflet map
├── main.py                # Entry point for the simulation
├── tests.py               # Unit and integration tests
├── README.md              # Project documentation
├── requirements.txt       # Python dependencies
```

---

## Program Structure

- **`main.py`**: Initializes all components and runs the simulation, dashboard, and WebSocket server.
- **`src/route_generator.py`**: Loads ports and generates interpolated vessel routes.
- **`src/vessel.py`**: Simulates vessel movement and generates AIS messages.
- **`src/database.py`**: Manages SQLite DB using SQLAlchemy; handles MMSI uniqueness and schema creation.
- **`src/websocket_server.py`**: Handles AIS message streaming via WebSocket.
- **`src/dashboard.py`**: Flask app for vessel track and statistics dashboard.
- **`templates/index.html`**: Web dashboard HTML template.
- **`static/css/style.css`**: Stylesheet for the dashboard UI.
- **`static/js/map.js`**: JavaScript for rendering vessel tracks using Leaflet.
- **`tests.py`**: Contains unit and integration tests for ingestion and analytics logic.

---

## Assumptions

- Simulates 1 vessel with unique MMSIs.
- AIS messages are generated every 5 minutes.
- Playback runs in real-time (`1.0x` speed).
- `ports.csv` includes UTF-8-encoded data (e.g., Rotterdam, Hamburg).
- SQLite DB (`ais_data.db`) is created if missing.
- Flask dashboard runs on [http://localhost:5000](http://localhost:5000).
- API endpoints return data in JSON.
- Tests use an in-memory SQLite database.

---

## Setup Instructions

### 1. Create the Project
```bash
mkdir ais_simulation_project
cd ais_simulation_project
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv env
env\scripts\activate
```

### 3. Install Dependencies:
```bash
pip install -r requirements.txt
```


### 4. Run the Simulation:
```bash
python main.py
```

---
## Running Tests

- The tests.py file includes unit and integration tests for:
- Ingestion Logic: Tests DatabaseManager.ingest_message for valid and invalid AIS messages.
- Analytics Logic: Tests DatabaseManager.get_vessel_track and DatabaseManager.calculate_vessel_stats for various scenarios.
- API Endpoints: Tests /api/vessel/<mmsi>/track and /api/vessel/<mmsi>/stats for correct responses and error handling.

#### To run tests:
```bash
pytest tests.py -v
```
- Expected output will show test results (e.g., test_ingest_valid_message PASSED, etc.). Ensure pytest is installed via requirements.txt.

## Access the Dashboard and API:

- Dashboard: Open http://localhost:5000 in a browser.
- API Endpoints:
- GET /api/vessel/<mmsi>/track: Fetch vessel trajectory.
- GET /api/vessel/<mmsi>/stats?start_time=<iso>&end_time=<iso>: - Fetch vessel stats (optional start_time and end_time).

---
---

## Design Decisions

- Database Check: Checks for ais_data.db; creates it with schema if absent.
- Unique Constraint: Enforces unique MMSI-timestamp pairs via UniqueConstraint.
- MMSI Generation: Random 9-digit MMSIs, verified unique via database checks.
- SQLAlchemy: Provides ORM for scalable database operations.
- Database: SQLite with indexes on mmsi and timestamp and a unique constraint.
- Flask Dashboard: Uses Leaflet.js for map visualization and a table for stats.
- API Endpoints: Fetch vessel tracks and stats, returning JSON for integration.
- File Encoding: Uses UTF-8 for ports.csv to handle potential non-ASCII characters.
- Validation: Checks latitude, longitude, and speed; logs malformed messages.
- Pre-calculation: Positions are pre-calculated for simplicity.
- Testing: Uses pytest with an in-memory database to ensure isolation and repeatability.

## Running the Solution

- Create ais_data.db if it doesn't exist.
- Simulate vessel and generate AIS messages.
- Stream messages via WebSocket and ingest into data/ais_data.db.
- Start the Flask dashboard and API.


- View the dashboard at http://localhost:5000.

## Analytics

- Track Retrieval: Fetches ordered positions per vessel via get_vessel_track.
- Statistics: Calculates total distance and average speed via calculate_vessel_stats.
- Dashboard: Visualizes tracks on a map and displays stats in a table.
- API: Provides programmatic access to track and stats data.

## Trade-offs

- Simplified Course: Assumes constant course (0°) for simplicity.
- No muliple vessel support.
- Pre-calculation: Limits dynamic route adjustments.
- Dashboard lacks real-time updates.
