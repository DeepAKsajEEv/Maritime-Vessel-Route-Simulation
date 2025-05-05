from pyais.encode import encode_dict


class Vessel:
    """Manages vessel simulation and AIS message generation."""

    def __init__(self, mmsi, speed_knots=10.0):
        self.mmsi = mmsi
        self.speed_knots = speed_knots

    def generate_ais_messages(self, positions):
        """Generate AIS messages for each position."""
        messages = []
        for pos in positions:
            ais_data = {
                "mmsi": self.mmsi,
                "lat": pos["lat"],
                "lon": pos["lon"],
                "msg_type": 1,
                "speed": self.speed_knots,
                "course": 0,
                "status": 0,
            }
            try:
                encoded = encode_dict(ais_data)
                messages.append(
                    {
                        "message": "AIVDM",
                        "mmsi": self.mmsi,
                        "timestamp": pos["timestamp"].isoformat(),
                        "payload": encoded[0],
                    }
                )
            except Exception as e:
                print(f"Failed to encode AIS message: {e}")
        return messages
