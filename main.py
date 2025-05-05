import asyncio
import os
from src.route_generator import RouteGenerator
from src.vessel import Vessel
from src.database import DatabaseManager
from src.websocket_server import WebSocketStreamer
from src.dashboard import create_app
import threading


async def main():
    """Main entry point for the AIS simulation."""
    # Configuration
    config = {
        # "csv_file": "data/ports.csv",
        "csv_file": "data/UpdatedPub150.csv",
        "db_file": "sqlite:///data/ais_data.db",
        "num_vessels": 1,
        "speed_knots": 10.0,
        "interval_seconds": 5 * 60,
        "speed_factor": -1,
        # "speed_factor": 1.0,
        "websocket_port": 8765,
        "flask_port": 5000,
    }

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # Initialize components
    db_manager = DatabaseManager(config["db_file"])
    route_generator = RouteGenerator(
        config["csv_file"], config["speed_knots"], config["interval_seconds"]
    )
    streamer = WebSocketStreamer(config["websocket_port"], config["speed_factor"])

    # Generate vessels and routes
    vessels = []
    used_ports = set()

    def gen_vessel_and_route():
        nonlocal used_ports
        # Generate unique MMSI
        mmsi = db_manager.generate_unique_mmsi()
        vessel = Vessel(mmsi)
        vessels.append(vessel)

        # Select unique ports
        while True:
            origin, destination = route_generator.select_random_ports()
            port_pair = (origin["name"], destination["name"])
            if port_pair not in used_ports:
                used_ports.add(port_pair)
                break

        # Generate route and positions
        waypoints = route_generator.generate_route(origin, destination)
        positions = route_generator.interpolate_positions(waypoints)
        messages = vessel.generate_ais_messages(positions)

        return messages

    # WebSocket simulation task
    async def run_simulation(messages):
        await streamer.run(messages, db_manager)

    # Run Flask dashboard in a thread-safe async way
    async def run_dashboard():
        app = create_app(db_manager)

        def run_flask():
            app.run(port=config["flask_port"], debug=False, use_reloader=False)

        flask_thread = threading.Thread(target=run_flask)
        flask_thread.start()
        return flask_thread

    # Generate tasks
    tasks = [
        run_simulation(gen_vessel_and_route()) for _ in range(config["num_vessels"])
    ]

    # Run dashboard in background
    flask_thread = await run_dashboard()

    # Run simulation tasks and exit after completion
    await asyncio.gather(*tasks)

    # Keep Flask alive
    flask_thread.join()


# Entry point
if __name__ == "__main__":
    asyncio.run(main())
