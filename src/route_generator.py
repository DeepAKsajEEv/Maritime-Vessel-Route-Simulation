import csv
from math import radians, sin, cos, sqrt, atan2
import searoute as sr
from datetime import datetime, timedelta
import random


class RouteGenerator:
    """Handles port loading, route generation, and position interpolation."""

    def __init__(self, csv_file, speed_knots, interval_seconds):
        self.ports = self._load_ports(csv_file)
        self.speed_knots = speed_knots
        self.interval_seconds = interval_seconds

    def _load_ports(self, csv_file):
        """Load ports from CSV file."""
        ports = []
        try:
            with open(csv_file, "r", encoding="ISO-8859-1") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ports.append(
                        {
                            "name": row["MAIN_PORT_NAME"],
                            "lat": float(row["LATITUDE"]),
                            "lon": float(row["LONGITUDE"]),
                        }
                    )
        except Exception as e:
            raise ValueError(f"Failed to load ports: {e}")
        return ports

    def select_random_ports(self):
        """Select two random ports as origin and destination."""
        if len(self.ports) < 2:
            raise ValueError("Insufficient ports in CSV")
        return tuple(random.sample(self.ports, 2))

    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two coordinates in nautical miles."""
        R = 6371e3  # Earth's radius in meters
        phi1, phi2 = radians(lat1), radians(lat2)
        delta_phi = radians(lat2 - lat1)
        delta_lambda = radians(lon2 - lon1)
        a = sin(delta_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c / 1852  # Convert to nautical miles

    def generate_route(self, origin, destination):
        """Generate route using searoute-py."""
        try:
            route = sr.searoute(
                [origin["lon"], origin["lat"]], [destination["lon"], destination["lat"]]
            )
            return route.geometry.coordinates
        except Exception as e:
            raise RuntimeError(f"Failed to generate route: {e}")

    def interpolate_positions(self, waypoints):
        """Interpolate positions along the route at fixed intervals."""
        positions = []
        total_distance = 0
        distances = []

        # Calculate distances between waypoints
        for i in range(len(waypoints) - 1):
            lon1, lat1 = waypoints[i]
            lon2, lat2 = waypoints[i + 1]
            dist = self.haversine_distance(lat1, lon1, lat2, lon2)
            total_distance += dist
            distances.append(dist)

        # Calculate time to cover each segment
        speed_mps = self.speed_knots * 0.514444  # Convert knots to meters/second
        time_per_segment = [dist * 1852 / speed_mps for dist in distances]
        total_time = sum(time_per_segment)

        # Generate positions
        current_time = 0
        start_time = datetime.now()
        while current_time <= total_time:
            elapsed_time = 0
            for i, seg_time in enumerate(time_per_segment):
                if elapsed_time + seg_time >= current_time:
                    t = (current_time - elapsed_time) / seg_time if seg_time > 0 else 0
                    lon1, lat1 = waypoints[i]
                    lon2, lat2 = waypoints[i + 1]
                    lat = lat1 + t * (lat2 - lat1)
                    lon = lon1 + t * (lon2 - lon1)
                    positions.append(
                        {
                            "lat": lat,
                            "lon": lon,
                            "timestamp": start_time + timedelta(seconds=current_time),
                        }
                    )
                    break
                elapsed_time += seg_time
            current_time += self.interval_seconds

        return positions
