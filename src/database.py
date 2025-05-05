from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Float,
    Boolean,
    Index,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pyais import decode
import numpy as np
from src.route_generator import RouteGenerator
import random
import os
from datetime import datetime

Base = declarative_base()


class AISMessage(Base):
    """SQLAlchemy model for AIS messages."""

    __tablename__ = "ais_messages"

    id = Column(Integer, primary_key=True)
    mmsi = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    speed = Column(Float)
    course = Column(Integer)
    status = Column(Integer)
    payload = Column(String, nullable=False)
    is_valid = Column(Boolean, nullable=False)
    error_message = Column(String)

    __table_args__ = (
        UniqueConstraint("mmsi", "timestamp", name="_mmsi_timestamp_uc"),
        Index("idx_mmsi", "mmsi"),
        Index("idx_timestamp", "timestamp"),
    )


class DatabaseManager:
    """Manages SQLAlchemy database operations."""

    def __init__(self, db_url):
        # Check if database file exists
        db_path = db_url.replace("sqlite:///", "")
        if not os.path.exists(db_path):
            print(f"Database {db_path} does not exist. Creating new database.")

        self.engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def generate_unique_mmsi(self):
        """Generate a unique 9-digit MMSI."""
        session = self.Session()
        try:
            while True:
                mmsi = str(random.randint(1, 9)) + "".join(
                    str(random.randint(0, 9)) for _ in range(8)
                )
                existing = session.query(AISMessage).filter_by(mmsi=mmsi).first()
                if not existing:
                    return mmsi
        finally:
            session.close()

    def ingest_message(self, message):
        """Ingest and validate AIS message."""
        session = self.Session()
        try:
            decoded = decode(message["payload"]).asdict()
            mmsi = str(decoded["mmsi"])
            lat = decoded["lat"]
            lon = decoded["lon"]
            speed = decoded["speed"]
            course = decoded["course"]
            status = decoded["status"]

            if isinstance(message["timestamp"], str):
                timestamp = datetime.fromisoformat(message["timestamp"])

            is_valid = True
            error_message = ""
            if not (-90 <= lat <= 90):
                is_valid = False
                error_message += "Invalid latitude; "
            if not (-180 <= lon <= 180):
                is_valid = False
                error_message += "Invalid longitude; "
            if not (0 <= speed <= 102.2):
                is_valid = False
                error_message += "Invalid speed; "

            ais_message = AISMessage(
                mmsi=mmsi,
                timestamp=timestamp,
                latitude=lat,
                longitude=lon,
                speed=speed,
                course=course,
                status=status,
                payload=message["payload"],
                is_valid=is_valid,
                error_message=error_message,
            )
            session.add(ais_message)
            session.commit()
        except Exception as e:
            session.add(
                AISMessage(
                    mmsi=message.get("mmsi"),
                    timestamp=message.get("timestamp"),
                    payload=message["payload"],
                    is_valid=False,
                    error_message=str(e),
                )
            )
            session.commit()
        finally:
            session.close()

    def get_vessel_track(self, mmsi):
        """Retrieve vessel's trajectory."""
        session = self.Session()
        try:
            track = (
                session.query(
                    AISMessage.timestamp, AISMessage.latitude, AISMessage.longitude
                )
                .filter(AISMessage.mmsi == mmsi, AISMessage.is_valid == True)
                .order_by(AISMessage.timestamp)
                .all()
            )
            return track
        finally:
            session.close()

    def calculate_vessel_stats(self, mmsi, start_time, end_time):
        """Calculate distance and average speed within time window."""
        session = self.Session()
        try:
            rows = (
                session.query(
                    AISMessage.timestamp,
                    AISMessage.latitude,
                    AISMessage.longitude,
                    AISMessage.speed,
                )
                .filter(
                    AISMessage.mmsi == mmsi,
                    AISMessage.is_valid == True,
                    AISMessage.timestamp.between(start_time, end_time),
                )
                .order_by(AISMessage.timestamp)
                .all()
            )

            if not rows:
                return {"distance": 0, "avg_speed": 0}

            total_distance = 0
            for i in range(1, len(rows)):
                lat1, lon1 = rows[i - 1][1], rows[i - 1][2]
                lat2, lon2 = rows[i][1], rows[i][2]
                total_distance += RouteGenerator.haversine_distance(
                    lat1, lon1, lat2, lon2
                )

            avg_speed = np.mean([row[3] for row in rows]) if rows else 0
            return {"distance": total_distance, "avg_speed": avg_speed}
        finally:
            session.close()

    def get_all_vessels(self):
        """Retrieve all unique vessels and their stats."""
        session = self.Session()
        try:
            vessels = session.query(AISMessage.mmsi).distinct().all()
            vessel_data = []
            for (mmsi,) in vessels:
                stats = self.calculate_vessel_stats(mmsi, "2000-01-01", "2100-01-01")
                track = self.get_vessel_track(mmsi)
                vessel_data.append(
                    {
                        "mmsi": mmsi,
                        "distance": stats["distance"],
                        "avg_speed": stats["avg_speed"],
                        "track": [
                            [float(t.latitude), float(t.longitude)] for t in track
                        ],
                    }
                )
            return vessel_data
        finally:
            session.close()
