import os

class Settings:
    PROJECT_NAME: str = "Traffic Control Center Backend"
    API_V1_STR: str = "/api/v1"
    WS_PATH: str = "/ws/live"
    DATA_SOURCE_TYPE: str = os.getenv("DATA_SOURCE_TYPE", "sumo")  # 'sumo' or 'camera'
    SUMO_SIMULATION_SPEED: float = float(os.getenv("SUMO_SIMULATION_SPEED", "1.0"))
    MQTT_BROKER_HOST: str = os.getenv("MQTT_BROKER_HOST", "localhost")
    MQTT_BROKER_PORT: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    MQTT_TOPIC: str = os.getenv("MQTT_TOPIC", "traffic/signals")

settings = Settings()
