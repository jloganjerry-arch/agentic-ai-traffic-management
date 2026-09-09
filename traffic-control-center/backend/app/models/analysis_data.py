"""
Analysis Data Contract for Phase 4 & 5 (Traffic Analysis Agent & Platoon Detection).
Strictly analytical models without signal recommendations or control decisions.
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.traffic_data import Direction, TrafficRegime


# ============================================================================
# Analysis Enums
# ============================================================================

class CongestionCategory(str, Enum):
    """
    Standardized project vocabulary for congestion severity.
    Consistent across JCI and direction-level congestion.
    """
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


class AnalysisSpeedTrend(str, Enum):
    """Corridor-level observed speed trend."""
    INCREASING = "INCREASING"
    STABLE = "STABLE"
    DECREASING = "DECREASING"
    UNKNOWN = "UNKNOWN"


# ============================================================================
# Platoon Detail Model (Phase 5)
# ============================================================================

class PlatoonDetail(BaseModel):
    """
    Approaching convoy/platoon detection analytics.
    Analytical prototype model to provide context for the future Safety Agent.
    Not a claim of real-world accident prevention.
    """
    platoon_detected: bool = Field(False, description="True if approaching vehicle group satisfies platoon criteria")
    vehicle_count: int = Field(0, ge=0, description="Number of vehicles in the detected platoon")
    vehicle_ids: List[str] = Field(default_factory=list, description="IDs of vehicles comprising the platoon")
    average_speed_kmh: float = Field(0.0, ge=0.0, description="Mean speed of platoon vehicles in km/h")
    speed_dispersion_kmh: float = Field(0.0, ge=0.0, description="Sample standard deviation of platoon speeds in km/h")
    lead_vehicle_distance_m: float = Field(0.0, ge=0.0, description="Distance from intersection stop-bar to lead vehicle in meters")
    lead_vehicle_eta_s: float = Field(0.0, ge=0.0, description="Time to junction of the lead vehicle in seconds")
    avg_headway_gap_m: float = Field(0.0, ge=0.0, description="Average distance headway between successive platoon vehicles in meters")
    criteria_notes: str = Field(
        "Criteria: count>=3, speed>=35km/h, sample_std<=6km/h (or spread<=8km/h), headway<=45m, single direction",
        description="Explainable criteria description"
    )


# ============================================================================
# JCI Factor Breakdown Model (Phase 4)
# ============================================================================

class FactorContribution(BaseModel):
    """Explainable component contribution for JCI."""
    raw_value: float = Field(..., description="Observed raw physical measurement")
    normalized_value: float = Field(..., ge=0.0, le=1.0, description="Normalized factor (0.0 to 1.0)")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight factor in JCI formula")
    contribution: float = Field(..., ge=0.0, le=1.0, description="Weighted contribution (normalized_value * weight)")


class JciFactorBreakdown(BaseModel):
    """
    Transparent factor breakdown for dashboard explainability.
    Formula: JCI = 0.40 * NormQueue + 0.35 * NormDensity + 0.25 * NormOccupancy
    Thresholds (100m, 60 veh/km) are prototype normalization thresholds.
    """
    queue: FactorContribution
    density: FactorContribution
    occupancy: FactorContribution


class JunctionCongestionIndex(BaseModel):
    """Explainable Junction Congestion Index."""
    score: float = Field(..., ge=0.0, le=1.0, description="JCI score constrained to [0.0, 1.0]")
    category: CongestionCategory = Field(..., description="Congestion category: LOW, MODERATE, HIGH, SEVERE")
    factor_breakdown: JciFactorBreakdown = Field(..., description="Detailed explainable factors contributing to JCI")


# ============================================================================
# Direction-Level Analysis Model
# ============================================================================

class DirectionAnalysis(BaseModel):
    """
    Analytical diagnostics for a single approach corridor.
    Does NOT contain signal recommendations or control actions.
    """
    direction: Direction = Field(..., description="Corridor approach direction")
    congestion_level: CongestionCategory = Field(..., description="Approach-level congestion: LOW, MODERATE, HIGH, SEVERE")
    density_veh_km: float = Field(..., ge=0.0, description="Vehicle density in veh/km")
    queue_severity_score: float = Field(..., ge=0.0, le=1.0, description="Normalized queue severity (0.0 to 1.0)")
    arrival_rate_vpm: float = Field(..., ge=0.0, description="Estimated arrival rate in vehicles per minute")
    speed_trend: AnalysisSpeedTrend = Field(AnalysisSpeedTrend.UNKNOWN, description="Observed corridor speed trend")
    platoon: PlatoonDetail = Field(default_factory=PlatoonDetail, description="Approaching platoon detection diagnostics")


# ============================================================================
# Junction-Level Analysis State Model
# ============================================================================

class JunctionAnalysisState(BaseModel):
    """
    Authoritative analysis output produced by the Analysis Agent.
    Strictly analytical; contains ZERO signal control decisions or recommendations.
    """
    junction_id: str = Field(..., description="Physical junction identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Snapshot timestamp")
    data_source: str = Field(..., description="Preserved data source label (e.g. TEST_SIMULATION)")
    traffic_state: TrafficRegime = Field(..., description="Analytically derived regime: PEAK, NON_PEAK, TRANSITION")
    jci: JunctionCongestionIndex = Field(..., description="Junction Congestion Index and factor breakdown")
    critical_direction: Direction = Field(..., description="Approach corridor with highest analytical load")
    directions: Dict[Direction, DirectionAnalysis] = Field(..., description="Diagnostics per approach corridor")
    platoons_detected: List[Direction] = Field(default_factory=list, description="List of directions with active platoons")
