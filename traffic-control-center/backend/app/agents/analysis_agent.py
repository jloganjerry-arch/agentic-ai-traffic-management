"""
Traffic Analysis Agent (Agent 2) & Approaching Vehicle / Platoon Detection (Phase 4 & 5).
Responsibility: "WHAT DOES THE TRAFFIC DATA MEAN?"

Interprets structured measurements from the Monitoring Agent (JunctionTrafficState)
and produces comprehensive analytical diagnostics (JunctionAnalysisState).

STRICT ARCHITECTURAL RULE:
This agent is purely analytical. It does NOT recommend signal phases,
does NOT compute green extensions, and NEVER publishes to MQTT.
"""

import math
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.traffic_data import (
    Direction,
    TrafficRegime,
    SpeedTrend,
    ApproachingVehicle,
    DirectionTrafficData,
    JunctionTrafficState,
)

from app.models.analysis_data import (
    CongestionCategory,
    AnalysisSpeedTrend,
    FactorContribution,
    JciFactorBreakdown,
    JunctionCongestionIndex,
    PlatoonDetail,
    DirectionAnalysis,
    JunctionAnalysisState,
)


class TrafficAnalysisAgent:
    """
    Agent 2: Diagnostic and congestion analytics engine.
    Answers: "WHAT DOES THE TRAFFIC DATA MEAN?"
    """

    # Prototype Normalization Constants (Documented for this intersection model)
    NORM_QUEUE_METERS: float = 100.0        # Prototype max queue normalization baseline
    NORM_DENSITY_VEH_KM: float = 60.0       # Prototype max density normalization baseline
    WEIGHT_QUEUE: float = 0.40              # JCI Queue weight
    WEIGHT_DENSITY: float = 0.35            # JCI Density weight
    WEIGHT_OCCUPANCY: float = 0.25          # JCI Occupancy weight

    # Platoon Detection Constants
    PLATOON_MIN_COUNT: int = 3              # Minimum vehicles to qualify as a platoon
    PLATOON_MIN_SPEED_KMH: float = 35.0     # Minimum approaching speed threshold
    PLATOON_MAX_STD_DEV_KMH: float = 6.0    # Maximum sample std deviation of speed
    PLATOON_MAX_SPEED_SPREAD_KMH: float = 8.0 # Maximum speed spread (max - min)
    PLATOON_MAX_HEADWAY_METERS: float = 45.0  # Maximum distance gap between successive vehicles
    PLATOON_MAX_TIME_HEADWAY_SEC: float = 3.0 # Maximum time headway gap between successive vehicles

    def __init__(self, agent_id: str = "agent-2"):
        self.id = agent_id
        self.name = "Traffic Analysis Agent"
        self.role = "Traffic State Diagnostics & Congestion Analytics"
        self.responsibility = "WHAT DOES THE TRAFFIC DATA MEAN?"

    # ========================================================================
    # 1. Junction Congestion Index (JCI)
    # ========================================================================

    def compute_jci(self, state: JunctionTrafficState) -> JunctionCongestionIndex:
        """
        Computes the explainable Junction Congestion Index:
        JCI = 0.40 * NormQueue + 0.35 * NormDensity + 0.25 * NormOccupancy
        Constrained to [0.0, 1.0].
        """
        # 1. Raw measurements
        total_queue = state.total_queue_length
        avg_density = (
            sum(d.traffic_density for d in state.directions.values()) / len(state.directions)
            if state.directions
            else 0.0
        )
        raw_occupancy = state.junction_occupancy

        # 2. Normalized values (0.0 to 1.0)
        norm_queue = round(min(1.0, max(0.0, total_queue / self.NORM_QUEUE_METERS)), 4)
        norm_density = round(min(1.0, max(0.0, avg_density / self.NORM_DENSITY_VEH_KM)), 4)
        norm_occupancy = round(min(1.0, max(0.0, raw_occupancy)), 4)

        # 3. Weighted contributions
        contrib_queue = round(norm_queue * self.WEIGHT_QUEUE, 4)
        contrib_density = round(norm_density * self.WEIGHT_DENSITY, 4)
        contrib_occupancy = round(norm_occupancy * self.WEIGHT_OCCUPANCY, 4)

        # 4. Total JCI Score
        jci_score = round(min(1.0, max(0.0, contrib_queue + contrib_density + contrib_occupancy)), 2)

        # 5. Deterministic Category Classification
        # 0.00-0.24: LOW | 0.25-0.49: MODERATE | 0.50-0.74: HIGH | 0.75-1.00: SEVERE
        if jci_score < 0.25:
            category = CongestionCategory.LOW
        elif jci_score < 0.50:
            category = CongestionCategory.MODERATE
        elif jci_score < 0.75:
            category = CongestionCategory.HIGH
        else:
            category = CongestionCategory.SEVERE

        breakdown = JciFactorBreakdown(
            queue=FactorContribution(
                raw_value=round(total_queue, 1),
                normalized_value=norm_queue,
                weight=self.WEIGHT_QUEUE,
                contribution=contrib_queue,
            ),
            density=FactorContribution(
                raw_value=round(avg_density, 1),
                normalized_value=norm_density,
                weight=self.WEIGHT_DENSITY,
                contribution=contrib_density,
            ),
            occupancy=FactorContribution(
                raw_value=round(raw_occupancy, 3),
                normalized_value=norm_occupancy,
                weight=self.WEIGHT_OCCUPANCY,
                contribution=contrib_occupancy,
            ),
        )

        return JunctionCongestionIndex(
            score=jci_score,
            category=category,
            factor_breakdown=breakdown,
        )

    # ========================================================================
    # 2. Approaching Vehicle / Platoon Detection (Phase 5)
    # ========================================================================

    def detect_platoon(self, direction_data: DirectionTrafficData) -> PlatoonDetail:
        """
        Evaluates approaching vehicles for a SINGLE corridor approach.
        Analytical prototype model to provide approaching-vehicle context for the future Safety Agent.
        It is not a claim of real-world accident prevention.

        Primary Implementation Rule:
        - Vehicle count >= 3
        - All speeds >= 35.0 km/h
        - Sample standard deviation <= 6.0 km/h AND speed spread <= 8.0 km/h
        - Distance headway between successive vehicles <= 45.0m (or time headway <= 3.0s)
        - Strictly direction-specific
        """
        candidates: List[ApproachingVehicle] = direction_data.approaching_vehicle_details

        # Filter to active approaching vehicles
        approaching_list = [v for v in candidates if v.speed >= self.PLATOON_MIN_SPEED_KMH and v.distance_to_junction > 0]

        # Rule 1: At least 3 vehicles required
        if len(approaching_list) < self.PLATOON_MIN_COUNT:
            return PlatoonDetail(
                platoon_detected=False,
                vehicle_count=len(approaching_list),
                vehicle_ids=[v.vehicle_id for v in approaching_list],
            )

        # Sort spatially by distance to intersection ascending (closest vehicle first)
        approaching_list.sort(key=lambda v: v.distance_to_junction)

        speeds = [v.speed for v in approaching_list]
        n = len(speeds)
        mean_speed = sum(speeds) / n

        # Rule 3: Speed Consistency (Sample Standard Deviation & Speed Spread)
        # Sample standard deviation: s = sqrt( sum((x - mean)^2) / (n - 1) )
        variance = sum((x - mean_speed) ** 2 for x in speeds) / (n - 1)
        sample_std_dev = math.sqrt(variance)
        speed_spread = max(speeds) - min(speeds)

        if sample_std_dev > self.PLATOON_MAX_STD_DEV_KMH or speed_spread > self.PLATOON_MAX_SPEED_SPREAD_KMH:
            return PlatoonDetail(
                platoon_detected=False,
                vehicle_count=n,
                vehicle_ids=[v.vehicle_id for v in approaching_list],
                average_speed_kmh=round(mean_speed, 1),
                speed_dispersion_kmh=round(sample_std_dev, 2),
            )

        # Rule 4: Spatial Proximity (Headway between adjacent vehicles in convoy)
        headway_gaps: List[float] = []
        is_spatially_cohesive = True

        for i in range(n - 1):
            dist_gap = approaching_list[i + 1].distance_to_junction - approaching_list[i].distance_to_junction
            headway_gaps.append(dist_gap)

            # Time headway: dist_gap / (speed in m/s)
            lead_mps = approaching_list[i].speed / 3.6
            time_gap = dist_gap / lead_mps if lead_mps > 0 else 999.0

            # Both distance gap and time gap exceeded means cluster is broken
            if dist_gap > self.PLATOON_MAX_HEADWAY_METERS and time_gap > self.PLATOON_MAX_TIME_HEADWAY_SEC:
                is_spatially_cohesive = False
                break

        if not is_spatially_cohesive:
            return PlatoonDetail(
                platoon_detected=False,
                vehicle_count=n,
                vehicle_ids=[v.vehicle_id for v in approaching_list],
                average_speed_kmh=round(mean_speed, 1),
                speed_dispersion_kmh=round(sample_std_dev, 2),
                avg_headway_gap_m=round(sum(headway_gaps) / len(headway_gaps), 1) if headway_gaps else 0.0,
            )

        # All criteria satisfied: Approaching Platoon Detected!
        lead_vehicle = approaching_list[0]
        avg_headway = round(sum(headway_gaps) / len(headway_gaps), 1) if headway_gaps else 0.0

        return PlatoonDetail(
            platoon_detected=True,
            vehicle_count=n,
            vehicle_ids=[v.vehicle_id for v in approaching_list],
            average_speed_kmh=round(mean_speed, 1),
            speed_dispersion_kmh=round(sample_std_dev, 2),
            lead_vehicle_distance_m=lead_vehicle.distance_to_junction,
            lead_vehicle_eta_s=lead_vehicle.estimated_time_of_arrival,
            avg_headway_gap_m=avg_headway,
        )

    # ========================================================================
    # 3. Direction-Level Analytical Metrics
    # ========================================================================

    def analyze_direction(self, direction_data: DirectionTrafficData) -> DirectionAnalysis:
        """Computes analytical metrics for a single approach corridor."""
        # 1. Approach Congestion Level
        # Formula: 0.50 * NormQueue(50m) + 0.50 * NormDensity(40veh/km)
        queue_score = min(1.0, max(0.0, direction_data.queue_length / 50.0))
        density_score = min(1.0, max(0.0, direction_data.traffic_density / 40.0))
        approach_score = round(0.50 * queue_score + 0.50 * density_score, 2)

        if approach_score < 0.25:
            congestion_lvl = CongestionCategory.LOW
        elif approach_score < 0.50:
            congestion_lvl = CongestionCategory.MODERATE
        elif approach_score < 0.75:
            congestion_lvl = CongestionCategory.HIGH
        else:
            congestion_lvl = CongestionCategory.SEVERE

        # 2. Arrival Rate (vehicles arriving per minute)
        # Count vehicles expected within the next 60 seconds
        arrivals_60s = [v for v in direction_data.approaching_vehicle_details if 0 < v.estimated_time_of_arrival <= 60.0]
        if arrivals_60s:
            arrival_rate_vpm = float(len(arrivals_60s))
        elif direction_data.approaching_vehicle_details:
            mean_eta = sum(v.estimated_time_of_arrival for v in direction_data.approaching_vehicle_details) / len(direction_data.approaching_vehicle_details)
            arrival_rate_vpm = round((len(direction_data.approaching_vehicle_details) / mean_eta) * 60.0, 1) if mean_eta > 0 else 0.0
        else:
            arrival_rate_vpm = 0.0

        # 3. Speed Trend (Derived from acceleration)
        if not direction_data.approaching_vehicle_details:
            speed_trend = AnalysisSpeedTrend.UNKNOWN
        else:
            accels = [v.acceleration for v in direction_data.approaching_vehicle_details if v.acceleration is not None]
            if not accels:
                speed_trend = AnalysisSpeedTrend.UNKNOWN
            else:
                mean_accel = sum(accels) / len(accels)
                if mean_accel > 0.15:
                    speed_trend = AnalysisSpeedTrend.INCREASING
                elif mean_accel < -0.15:
                    speed_trend = AnalysisSpeedTrend.DECREASING
                else:
                    speed_trend = AnalysisSpeedTrend.STABLE

        # 4. Platoon Detection
        platoon = self.detect_platoon(direction_data)

        return DirectionAnalysis(
            direction=direction_data.direction,
            congestion_level=congestion_lvl,
            density_veh_km=direction_data.traffic_density,
            queue_severity_score=round(queue_score, 2),
            arrival_rate_vpm=arrival_rate_vpm,
            speed_trend=speed_trend,
            platoon=platoon,
        )

    # ========================================================================
    # 4. Critical Direction Identification
    # ========================================================================

    def identify_critical_direction(
        self, state: JunctionTrafficState, dir_analyses: Dict[Direction, DirectionAnalysis]
    ) -> Direction:
        """
        Identifies the corridor approach with highest analytical urgency/load.
        Pure analytical determination; does NOT issue a signal change command.
        """
        urgency_scores: Dict[Direction, float] = {}

        for d_enum, d_data in state.directions.items():
            analysis = dir_analyses.get(d_enum)
            queue_sev = analysis.queue_severity_score if analysis else 0.0
            norm_dens = min(1.0, d_data.traffic_density / 40.0)
            norm_app = min(1.0, d_data.approaching_count / 10.0)

            # Platoon adds an analytical urgency bonus (+0.20)
            platoon_bonus = 0.20 if (analysis and analysis.platoon.platoon_detected) else 0.0

            score = round(0.40 * queue_sev + 0.30 * norm_dens + 0.20 * norm_app + platoon_bonus, 3)
            urgency_scores[d_enum] = score

        # Sort descending by score, tie break by vehicle count
        critical = max(
            urgency_scores.keys(),
            key=lambda d: (urgency_scores[d], state.directions[d].vehicle_count),
        )
        return critical

    # ========================================================================
    # 5. Traffic Regime Classification
    # ========================================================================

    def classify_traffic_regime(self, jci_score: float) -> TrafficRegime:
        """
        Classifies traffic regime analytically from JCI:
        - JCI < 0.35: NON_PEAK
        - JCI >= 0.65: PEAK
        - 0.35 <= JCI < 0.65: TRANSITION
        """
        if jci_score < 0.35:
            return TrafficRegime.NON_PEAK
        elif jci_score >= 0.65:
            return TrafficRegime.PEAK
        else:
            return TrafficRegime.TRANSITION

    # ========================================================================
    # 6. Master Analyze Method
    # ========================================================================

    def analyze(self, monitoring_state: JunctionTrafficState) -> JunctionAnalysisState:
        """
        Transforms JunctionTrafficState from Monitoring Agent into JunctionAnalysisState.
        Answers: "WHAT DOES THE TRAFFIC DATA MEAN?"
        """
        # 1. Compute JCI
        jci = self.compute_jci(monitoring_state)

        # 2. Analyze each direction
        directions_analysis: Dict[Direction, DirectionAnalysis] = {}
        platoons_found: List[Direction] = []

        for dir_enum, dir_data in monitoring_state.directions.items():
            analysis = self.analyze_direction(dir_data)
            directions_analysis[dir_enum] = analysis
            if analysis.platoon.platoon_detected:
                platoons_found.append(dir_enum)

        # 3. Critical Direction
        critical_direction = self.identify_critical_direction(monitoring_state, directions_analysis)

        # 4. Traffic Regime
        regime = self.classify_traffic_regime(jci.score)

        # 5. Build and return immutable analysis state
        return JunctionAnalysisState(
            junction_id=monitoring_state.junction_id,
            timestamp=datetime.now(),
            data_source=monitoring_state.data_source,  # Strictly preserve data source
            traffic_state=regime,
            jci=jci,
            critical_direction=critical_direction,
            directions=directions_analysis,
            platoons_detected=platoons_found,
        )

    def get_summary(self, analysis_state: JunctionAnalysisState) -> Dict[str, Any]:
        """
        Serializes analytical diagnostics for dashboard and future pipeline stages.
        Guaranteed to contain NO signal recommendations or commands.
        """
        return {
            "agent_id": self.id,
            "agent_name": self.name,
            "stage": "Analysis",
            "question_answered": self.responsibility,
            "junction_id": analysis_state.junction_id,
            "data_source": analysis_state.data_source,
            "timestamp": analysis_state.timestamp.isoformat(),
            "traffic_state": analysis_state.traffic_state.value,
            "jci": {
                "score": analysis_state.jci.score,
                "category": analysis_state.jci.category.value,
                "factor_breakdown": {
                    "queue": analysis_state.jci.factor_breakdown.queue.model_dump(),
                    "density": analysis_state.jci.factor_breakdown.density.model_dump(),
                    "occupancy": analysis_state.jci.factor_breakdown.occupancy.model_dump(),
                },
            },
            "critical_direction": analysis_state.critical_direction.value,
            "platoons_detected": [d.value for d in analysis_state.platoons_detected],
            "directions": {
                d.value: {
                    "congestion_level": data.congestion_level.value,
                    "density_veh_km": data.density_veh_km,
                    "queue_severity_score": data.queue_severity_score,
                    "arrival_rate_vpm": data.arrival_rate_vpm,
                    "speed_trend": data.speed_trend.value,
                    "platoon": data.platoon.model_dump(),
                }
                for d, data in analysis_state.directions.items()
            },
        }
