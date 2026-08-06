from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.data_providers.schemas import TrafficState, OverviewState, ApproachState, SignalHeadState, HardwareNodeState, TrendData

class TrafficStateProvider(ABC):
    """
    Abstract base class interface for traffic state data providers.
    Decouples FastAPI routes, AI agents, and WebSocket handlers from whether data
    originates from SUMO simulation (Semester 5) or live YOLOv8 vision pipeline (Semester 6).
    """

    @abstractmethod
    async def get_current_state(self) -> TrafficState:
        """
        Returns the unified TrafficState object containing all telemetry metrics.
        Must be implemented by concrete providers.
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """
        Returns the name of the active data provider source.
        """
        pass

    # Standardized convenience getters wrapping get_current_state()
    async def get_overview(self) -> Dict[str, Any]:
        """Returns overview summary metrics."""
        state = await self.get_current_state()
        return state.overview.model_dump()

    async def get_approaches(self) -> List[Dict[str, Any]]:
        """Returns approach telemetry for North, South, East, West approaches."""
        state = await self.get_current_state()
        return [app.model_dump() for app in state.approaches]

    async def get_signals(self) -> List[Dict[str, Any]]:
        """Returns signal state and timers for all signal heads."""
        state = await self.get_current_state()
        return [sig.model_dump() for sig in state.signals]

    async def get_trends(self) -> Dict[str, List[Dict[str, Any]]]:
        """Returns historical/time-series trend data for charts."""
        state = await self.get_current_state()
        return state.trends.model_dump()

    async def get_hardware_status(self) -> List[Dict[str, Any]]:
        """Returns status of hardware nodes/microcontrollers."""
        state = await self.get_current_state()
        return [hw.model_dump() for hw in state.hardware_status]
