from fastapi.testclient import TestClient
from app.main import app
import json

def test_websocket_channels():
    client = TestClient(app)

    print("Testing /ws/signals WebSocket channel...")
    with client.websocket_connect("/ws/signals") as websocket:
        data = websocket.receive_json()
        assert data["event"] == "signal_state_sync"
        assert "signals" in data
        assert "source" in data
        assert "confidence" in data

    print("Testing /ws/logs WebSocket channel...")
    with client.websocket_connect("/ws/logs") as websocket:
        data = websocket.receive_json()
        assert data["event"] == "log_stream_connected"
        assert "message" in data

    print("Testing /ws/heartbeat WebSocket channel...")
    with client.websocket_connect("/ws/heartbeat") as websocket:
        data = websocket.receive_json()
        assert data["event"] == "heartbeat"
        assert data["status"] == "ONLINE"
        assert "latency_ms" in data

    print("ALL WEBSOCKET CHANNEL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_websocket_channels()
