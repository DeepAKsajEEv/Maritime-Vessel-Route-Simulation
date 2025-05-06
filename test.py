import pytest
from src.database import DatabaseManager, AISMessage
from src.dashboard import create_app
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from pyais import encode_msg
import json

# Fixture to create an in-memory database
@pytest.fixture
def db_manager():
    db = DatabaseManager('sqlite:///:memory:')
    yield db
    # Cleanup is handled by in-memory database being temporary

# Fixture to create a Flask test client
@pytest.fixture
def client(db_manager):
    app = create_app(db_manager)
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Helper to create a valid AIS message
def create_ais_message(mmsi, lat, lon, speed, timestamp, course=0, status=0):
    ais_data = {
        'mmsi': mmsi,
        'lat': lat,
        'lon': lon,
        'msg_type': 1,
        'speed': speed,
        'course': course,
        'status': status
    }
    encoded = encode_msg(ais_data)
    return {
        'message': 'AIVDM',
        'mmsi': str(mmsi),
        'timestamp': timestamp,
        'payload': encoded[0]
    }

# Unit Tests for Ingestion Logic
def test_ingest_valid_message(db_manager):
    """Test ingestion of a valid AIS message."""
    message = create_ais_message(
        mmsi=123456789,
        lat=51.9225,
        lon=4.4792,
        speed=10.0,
        timestamp='2025-01-01T00:00:00'
    )
    db_manager.ingest_message(message)
    
    session = db_manager.Session()
    result = session.query(AISMessage).first()
    session.close()
    
    assert result is not None
    assert result.mmsi == '123456789'
    assert result.latitude == 51.9225
    assert result.longitude == 4.4792
    assert result.speed == 10.0
    assert result.is_valid == True
    assert result.error_message == ''

def test_ingest_invalid_latitude(db_manager):
    """Test ingestion of a message with invalid latitude."""
    message = create_ais_message(
        mmsi=123456789,
        lat=91.0,  # Invalid latitude
        lon=4.4792,
        speed=10.0,
        timestamp='2025-01-01T00:00:00'
    )
    db_manager.ingest_message(message)
    
    session = db_manager.Session()
    result = session.query(AISMessage).first()
    session.close()
    
    assert result is not None
    assert result.mmsi == '123456789'
    assert result.is_valid == False
    assert 'Invalid latitude' in result.error_message

def test_ingest_invalid_longitude(db_manager):
    """Test ingestion of a message with invalid longitude."""
    message = create_ais_message(
        mmsi=123456789,
        lat=51.9225,
        lon=181.0,  # Invalid longitude
        speed=10.0,
        timestamp='2025-01-01T00:00:00'
    )
    db_manager.ingest_message(message)
    
    session = db_manager.Session()
    result = session.query(AISMessage).first()
    session.close()
    
    assert result is not None
    assert result.is_valid == False
    assert 'Invalid longitude' in result.error_message

def test_ingest_invalid_speed(db_manager):
    """Test ingestion of a message with invalid speed."""
    message = create_ais_message(
        mmsi=123456789,
        lat=51.9225,
        lon=4.4792,
        speed=150.0,  # Invalid speed
        timestamp='2025-01-01T00:00:00'
    )
    db_manager.ingest_message(message)
    
    session = db_manager.Session()
    result = session.query(AISMessage).first()
    session.close()
    
    assert result.is_valid == False
    assert 'Invalid speed' in result.error_message

def test_ingest_malformed_payload(db_manager):
    """Test ingestion of a message with a malformed payload."""
    message = {
        'message': 'AIVDM',
        'mmsi': '123456789',
        'timestamp': '2025-01-01T00:00:00',
        'payload': 'invalid_payload'
    }
    db_manager.ingest_message(message)
    
    session = db_manager.Session()
    result = session.query(AISMessage).first()
    session.close
