from flask import Flask, render_template
import os


def create_app(db_manager):
    app = Flask(__name__, template_folder="../templates", static_folder="../static")

    @app.route("/")
    def index():
        vessels = db_manager.get_all_vessels()
        return render_template("index.html", vessels=vessels)

    @app.route("/api/vessel/<mmsi>/stats", methods=["GET"])
    def get_vessel_stats(mmsi):
        """Fetch vessel's statistics (distance and average speed) as JSON."""
        try:
            start_time = request.args.get("start_time", "2000-01-01")
            end_time = request.args.get("end_time", "2100-01-01")
            stats = db_manager.calculate_vessel_stats(mmsi, start_time, end_time)
            return jsonify(
                {
                    "mmsi": mmsi,
                    "distance": float(stats["distance"]),
                    "avg_speed": float(stats["avg_speed"]),
                    "start_time": start_time,
                    "end_time": end_time,
                }
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/shutdown")
    def shutdown():
        os._exit(0)  # Forcefully shutdown the Flask server
        return "Server is shutting down..."

    return app
