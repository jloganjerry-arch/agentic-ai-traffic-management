from app.core.config import settings
from app.data_providers.base_provider import TrafficStateProvider
from app.data_providers.sumo_provider import SumoTrafficProvider
from app.data_providers.camera_provider import CameraTrafficProvider
from typing import Optional

_provider_instance: Optional[TrafficStateProvider] = None

def get_provider(force_type: Optional[str] = None) -> TrafficStateProvider:
    """
    Factory function returning the active TrafficStateProvider singleton based on configuration.
    Controlled by settings.DATA_SOURCE_TYPE ('sumo' vs 'camera').
    """
    global _provider_instance
    source_type = (force_type or settings.DATA_SOURCE_TYPE).lower()

    if force_type is not None or _provider_instance is None:
        if source_type == "camera":
            _provider_instance = CameraTrafficProvider()
        else:
            _provider_instance = SumoTrafficProvider()

    return _provider_instance
