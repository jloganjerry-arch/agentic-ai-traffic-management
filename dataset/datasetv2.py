"""
SUMO TraCI Dataset V2.5 Collector
==================================

Research-quality data collection for Agentic AI-Driven Multi-Agent
Intelligent Traffic Management.

This version merges two independent implementations:
  - Explicit internal-lane filtering, clear inline documentation, and
    a straightforward density calculation.
  - Single-pass vehicle iteration, travel-time/throughput/delay tracking,
    a multi-factor weighted congestion score, vehicle-category counts,
    and rule-based AI target labels.

Two correctness fixes applied during the merge (see inline notes marked
FIXED):
  1. Emergency-vehicle counts previously used a mismatched dictionary key
     and were silently dropped -- never raised an error, just always
     read back as zero.
  2. Internal SUMO junction-connector lanes (IDs starting with ':') were
     being included in lane-length and occupancy aggregates, which
     distorts Traffic_Density and Lane_Occupancy since those lanes are
     not real approach lanes.

All features are collected directly from SUMO TraCI APIs or derived
mathematically from simulation state. No synthetic or randomly generated
data is used.

Output: traffic_dataset_v2.csv
"""

import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# ---------------------------------------------------------------------------
# SUMO Environment Setup
# ---------------------------------------------------------------------------
if "SUMO_HOME" not in os.environ:
    raise EnvironmentError(
        "SUMO_HOME environment variable is not set. "
        "Please point it to your SUMO installation root."
    )

TOOLS_PATH = os.path.join(os.environ["SUMO_HOME"], "tools")
sys.path.append(TOOLS_PATH)

import traci  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration Constants
# ---------------------------------------------------------------------------
SUMO_BINARY = os.path.join(os.environ["SUMO_HOME"], "bin", "sumo")
SUMO_CONFIG = r"C:\Traffic Project\config\junction.sumocfg"
OUTPUT_CSV = "traffic_dataset_v2.csv"

# --- Direction Mapping -------------------------------------------------------
# Populate this dictionary with your network's incoming edge IDs.
# Example: "E0": "North" means vehicles on edge E0 are approaching from North.
# Open your net.xml in netedit or sumo-gui to find the real edge IDs --
# vehicles on unmapped edges are simply not counted in any direction.
INCOMING_EDGE_DIRECTION_MAP: Dict[str, str] = {
    "E2": "North",
    "E3": "South",
    "E4": "West",
    "E5": "East",
}

# --- Vehicle Category Mapping -----------------------------------------------
# Maps substrings of traci.vehicle.getTypeID() to category labels.
# The first match wins; if nothing matches, the vehicle is classified as "Car".
# NOTE: category values here must exactly match the "<Category>_Count" keys
# pre-initialized in process_vehicles_single_pass() below -- this is exactly
# the mismatch that silently dropped emergency vehicles in an earlier draft.
VEHICLE_TYPE_CATEGORY_MAP: Dict[str, str] = {
    "bus": "Bus",
    "truck": "Truck",
    "motorcycle": "Motorcycle",
    "emergency": "Emergency_Vehicle",   # FIXED: was "Emergency" (key mismatch)
    "police": "Emergency_Vehicle",      # FIXED
    "ambulance": "Emergency_Vehicle",   # FIXED
    "fire": "Emergency_Vehicle",        # FIXED
}

# --- Congestion Scoring Thresholds ------------------------------------------
# Each factor contributes 0 (low), 1 (medium), or 2 (high) points.
# Total score: 0-1 -> Low, 2-3 -> Medium, >=4 -> High
# These are reasonable starting points, not measured values from your
# specific junction -- tune after observing your own simulation's normal range.
CONGESTION_THRESHOLDS = {
    "speed": {"high": 2.5, "medium": 5.0},       # m/s  (lower = worse)
    "queue": {"high": 15, "medium": 8},          # vehicles
    "wait": {"high": 20.0, "medium": 10.0},      # seconds
    "density": {"high": 30.0, "medium": 15.0},   # veh / km
    "occupancy": {"high": 50.0, "medium": 25.0}, # percent
}

# --- Green Time Policy -------------------------------------------------------
GREEN_TIME_POLICY = {0: 20, 1: 35, 2: 50}  # seconds

# --- Logging -----------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# =============================================================================
# Helper Functions
# =============================================================================

def start_sumo() -> None:
    """Launch SUMO simulation via TraCI."""
    sumo_cmd = [SUMO_BINARY, "-c", SUMO_CONFIG]
    traci.start(sumo_cmd)
    logger.info("SUMO started with config: %s", SUMO_CONFIG)


def get_monitored_lanes() -> List[str]:
    """Return all real (non-internal) lane IDs in the network.

    FIXED: SUMO internal junction-connector lanes are prefixed with ':'
    and do not represent real approach lanes. Including them distorts
    Total_Lane_Length_M and Average_Lane_Occupancy, so they are filtered
    out here, once, rather than at every call site.
    """
    return [lane_id for lane_id in traci.lane.getIDList() if not lane_id.startswith(":")]


def get_direction_from_edge(edge_id: str) -> Optional[str]:
    """Return cardinal direction for a given edge ID if mapped."""
    return INCOMING_EDGE_DIRECTION_MAP.get(edge_id)


def get_vehicle_category(type_id: str) -> str:
    """
    Classify a SUMO vehicle type ID into a research category.

    Falls back to 'Car' if no keyword matches.
    """
    tid_lower = type_id.lower()
    for substring, category in VEHICLE_TYPE_CATEGORY_MAP.items():
        if substring in tid_lower:
            return category
    return "Car"


def get_tls_info() -> Dict[str, Any]:
    """
    Extract traffic light signal information.

    Returns:
        Current_TLS_Phase   : Phase index of the first TLS (-1 if none).
        Remaining_Green_Time: Seconds left in the current phase, but only
                              reported when that phase is actually green
                              (0.0 during red/yellow) -- the field name
                              promises green time specifically, not just
                              "time until any phase change".
    """
    tls_ids: List[str] = traci.trafficlight.getIDList()
    if not tls_ids:
        return {"Current_TLS_Phase": -1, "Remaining_Green_Time": 0.0}

    # NOTE: For multi-intersection networks, extend this to iterate over all TLS.
    tls_id = tls_ids[0]

    current_phase = traci.trafficlight.getPhase(tls_id)
    next_switch = traci.trafficlight.getNextSwitch(tls_id)
    now = traci.simulation.getTime()

    remaining_phase_time = max(0.0, next_switch - now)

    # SUMO state encoding: 'G'/'g' = green, 'y' = yellow, 'r' = red
    state = traci.trafficlight.getRedYellowGreenState(tls_id)
    is_green = any(signal in ("G", "g") for signal in state)

    return {
        "Current_TLS_Phase": current_phase,
        "Remaining_Green_Time": round(remaining_phase_time, 2) if is_green else 0.0,
    }


def get_lane_aggregate_data(lane_ids: List[str]) -> Dict[str, Any]:
    """
    Collect lane-level data in a single pass over the pre-filtered,
    real (non-internal) lane list.

    Returns:
        Total_Lane_Length_M   : Sum of all monitored lane lengths (meters).
        Average_Lane_Occupancy: Mean occupancy (0-100) across monitored lanes.
        Halting_Vehicles      : Total halting vehicles (SUMO standard definition).
    """
    if not lane_ids:
        return {
            "Total_Lane_Length_M": 0.0,
            "Average_Lane_Occupancy": 0.0,
            "Halting_Vehicles": 0,
        }

    total_length = 0.0
    total_occupancy = 0.0
    total_halting = 0

    for lane_id in lane_ids:
        total_length += traci.lane.getLength(lane_id)
        total_occupancy += traci.lane.getLastStepOccupancy(lane_id)
        total_halting += traci.lane.getLastStepHaltingNumber(lane_id)

    return {
        "Total_Lane_Length_M": total_length,
        "Average_Lane_Occupancy": round(total_occupancy / len(lane_ids), 2),
        "Halting_Vehicles": total_halting,
    }


def process_vehicles_single_pass() -> Dict[str, Any]:
    """
    Iterate over all vehicles ONCE, accumulating all per-vehicle metrics.

    This is the primary efficiency optimization: one TraCI loop collects
    kinematics, emissions, waiting times, types, and edge data simultaneously
    instead of re-querying the vehicle list for each metric group.
    """
    vehicle_ids: List[str] = traci.vehicle.getIDList()
    count = len(vehicle_ids)

    # Pre-initialise all counters to guarantee schema completeness even when
    # zero vehicles are present this step.
    acc: Dict[str, Any] = {
        "Vehicle_Count": count,
        "Queue_Length": 0,
        "Total_Speed": 0.0,
        "Max_Speed": 0.0,
        "Min_Speed": float("inf"),
        "Total_Wait": 0.0,
        "Max_Wait": 0.0,
        "Total_Accel": 0.0,
        "Total_CO2": 0.0,
        "Total_Fuel": 0.0,
        "Total_NOx": 0.0,
        "Total_PMx": 0.0,
        "Total_Delay": 0.0,
        "North_Count": 0,
        "South_Count": 0,
        "East_Count": 0,
        "West_Count": 0,
        "Car_Count": 0,
        "Bus_Count": 0,
        "Truck_Count": 0,
        "Motorcycle_Count": 0,
        "Emergency_Vehicle_Count": 0,  # FIXED: matches category label exactly now
    }

    if count == 0:
        acc["Min_Speed"] = 0.0
        return acc

    for vid in vehicle_ids:
        # --- Core kinematics ------------------------------------------------
        speed = traci.vehicle.getSpeed(vid)
        wait = traci.vehicle.getWaitingTime(vid)
        accel = traci.vehicle.getAcceleration(vid)

        acc["Total_Speed"] += speed
        acc["Total_Wait"] += wait
        acc["Total_Accel"] += accel
        acc["Max_Speed"] = max(acc["Max_Speed"], speed)
        acc["Min_Speed"] = min(acc["Min_Speed"], speed)
        acc["Max_Wait"] = max(acc["Max_Wait"], wait)

        # Queue: speed < 0.1 m/s (preserves original dataset.py definition;
        # Halting_Vehicles from get_lane_aggregate_data uses SUMO's own
        # stricter halting definition as a separate, complementary field)
        if speed < 0.1:
            acc["Queue_Length"] += 1

        # --- Environmental outputs ------------------------------------------
        acc["Total_CO2"] += traci.vehicle.getCO2Emission(vid)
        acc["Total_Fuel"] += traci.vehicle.getFuelConsumption(vid)
        acc["Total_NOx"] += traci.vehicle.getNOxEmission(vid)
        acc["Total_PMx"] += traci.vehicle.getPMxEmission(vid)

        # --- Delay (time loss vs. free-flow travel) --------------------------
        acc["Total_Delay"] += traci.vehicle.getTimeLoss(vid)

        # --- Direction by current edge ID ------------------------------------
        edge_id = traci.vehicle.getRoadID(vid)
        direction = get_direction_from_edge(edge_id)
        if direction == "North":
            acc["North_Count"] += 1
        elif direction == "South":
            acc["South_Count"] += 1
        elif direction == "East":
            acc["East_Count"] += 1
        elif direction == "West":
            acc["West_Count"] += 1

        # --- Vehicle category -------------------------------------------------
        type_id = traci.vehicle.getTypeID(vid)
        category = get_vehicle_category(type_id)
        acc[f"{category}_Count"] += 1  # FIXED: category labels now match pre-init keys

    return acc


def compute_derived_metrics(
    acc: Dict[str, Any], lane_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compute averages, density, and other derived quantities.

    Handles zero-vehicle steps safely.
    """
    count = acc["Vehicle_Count"]

    if count == 0:
        return {
            "Average_Speed": 0.0,
            "Maximum_Speed": 0.0,
            "Minimum_Speed": 0.0,
            "Average_Waiting_Time": 0.0,
            "Maximum_Waiting_Time": 0.0,
            "Average_Acceleration": 0.0,
            "Average_Delay": 0.0,
            "Traffic_Density": 0.0,
            "Lane_Occupancy": lane_data["Average_Lane_Occupancy"],
            "Total_CO2_Emission": 0.0,
            "Total_Fuel_Consumption": 0.0,
            "Total_NOx_Emission": 0.0,
            "Total_PMx_Emission": 0.0,
        }

    avg_speed = acc["Total_Speed"] / count
    avg_wait = acc["Total_Wait"] / count
    avg_accel = acc["Total_Accel"] / count
    avg_delay = acc["Total_Delay"] / count

    # Traffic Density: vehicles per kilometre of monitored (real) lane length
    total_length_km = lane_data["Total_Lane_Length_M"] / 1000.0
    density = count / total_length_km if total_length_km > 0 else 0.0

    return {
        "Average_Speed": round(avg_speed, 2),
        "Maximum_Speed": round(acc["Max_Speed"], 2),
        "Minimum_Speed": round(acc["Min_Speed"], 2),
        "Average_Waiting_Time": round(avg_wait, 2),
        "Maximum_Waiting_Time": round(acc["Max_Wait"], 2),
        "Average_Acceleration": round(avg_accel, 2),
        "Average_Delay": round(avg_delay, 2),
        "Traffic_Density": round(density, 2),
        "Lane_Occupancy": lane_data["Average_Lane_Occupancy"],
        "Total_CO2_Emission": round(acc["Total_CO2"], 2),
        "Total_Fuel_Consumption": round(acc["Total_Fuel"], 2),
        "Total_NOx_Emission": round(acc["Total_NOx"], 2),
        "Total_PMx_Emission": round(acc["Total_PMx"], 2),
    }


def update_travel_time_metrics(
    entry_times: Dict[str, float], current_time: float
) -> Tuple[float, int, Dict[str, float]]:
    """
    Track departed and arrived vehicles to compute travel times and
    intersection throughput.

    Returns:
        Average_Travel_Time   : Mean travel time of vehicles that exited
                                 this step (0.0 if none exited).
        Intersection_Throughput: Number of vehicles that arrived/exited
                                 this step.
        Updated entry_times dictionary (arrived vehicles pruned so the
        dictionary does not grow unbounded over a long simulation).
    """
    departed = traci.simulation.getDepartedIDList()
    arrived = traci.simulation.getArrivedIDList()

    for vid in departed:
        entry_times[vid] = current_time

    travel_times: List[float] = []
    for vid in arrived:
        if vid in entry_times:
            travel_times.append(current_time - entry_times[vid])
            del entry_times[vid]

    avg_travel_time = sum(travel_times) / len(travel_times) if travel_times else 0.0
    throughput = len(arrived)

    return round(avg_travel_time, 2), throughput, entry_times


def compute_congestion_level(
    queue_len: int,
    avg_wait: float,
    avg_speed: float,
    density: float,
    occupancy: float,
) -> int:
    """
    Multi-factor rule-based congestion classification.

    Each of five factors (speed, queue, wait, density, occupancy)
    contributes 0, 1, or 2 points. Total: 0-1 -> Low (0), 2-3 -> Medium (1),
    >=4 -> High (2). Using five independent signals rather than one avoids
    a single noisy metric (e.g. a momentary empty-but-slow reading)
    misclassifying the whole step.
    """
    score = 0

    if avg_speed < CONGESTION_THRESHOLDS["speed"]["high"]:
        score += 2
    elif avg_speed < CONGESTION_THRESHOLDS["speed"]["medium"]:
        score += 1

    if queue_len >= CONGESTION_THRESHOLDS["queue"]["high"]:
        score += 2
    elif queue_len >= CONGESTION_THRESHOLDS["queue"]["medium"]:
        score += 1

    if avg_wait >= CONGESTION_THRESHOLDS["wait"]["high"]:
        score += 2
    elif avg_wait >= CONGESTION_THRESHOLDS["wait"]["medium"]:
        score += 1

    if density >= CONGESTION_THRESHOLDS["density"]["high"]:
        score += 2
    elif density >= CONGESTION_THRESHOLDS["density"]["medium"]:
        score += 1

    if occupancy >= CONGESTION_THRESHOLDS["occupancy"]["high"]:
        score += 2
    elif occupancy >= CONGESTION_THRESHOLDS["occupancy"]["medium"]:
        score += 1

    if score >= 4:
        return 2
    elif score >= 2:
        return 1
    return 0


def get_recommended_green_time(congestion_level: int) -> int:
    """Return rule-based recommended green duration in seconds."""
    return GREEN_TIME_POLICY.get(congestion_level, 20)


def build_record(
    step_counter: int,
    lane_data: Dict[str, Any],
    acc: Dict[str, Any],
    derived: Dict[str, Any],
    tls: Dict[str, Any],
    avg_travel_time: float,
    throughput: int,
) -> Dict[str, Any]:
    """Assemble the final feature vector for the current simulation step."""
    congestion = compute_congestion_level(
        queue_len=acc["Queue_Length"],
        avg_wait=derived["Average_Waiting_Time"],
        avg_speed=derived["Average_Speed"],
        density=derived["Traffic_Density"],
        occupancy=derived["Lane_Occupancy"],
    )

    return {
        # --- Simulation -----------------------------------------------------
        "Time": int(traci.simulation.getTime()),
        "Simulation_Step": step_counter,
        # --- Traffic --------------------------------------------------------
        "Vehicle_Count": acc["Vehicle_Count"],
        "Queue_Length": acc["Queue_Length"],
        "Halting_Vehicles": lane_data["Halting_Vehicles"],
        "Traffic_Density": derived["Traffic_Density"],
        "Lane_Occupancy": derived["Lane_Occupancy"],
        # --- Speed ----------------------------------------------------------
        "Average_Speed": derived["Average_Speed"],
        "Maximum_Speed": derived["Maximum_Speed"],
        "Minimum_Speed": derived["Minimum_Speed"],
        "Average_Acceleration": derived["Average_Acceleration"],
        # --- Waiting --------------------------------------------------------
        "Average_Waiting_Time": derived["Average_Waiting_Time"],
        "Maximum_Waiting_Time": derived["Maximum_Waiting_Time"],
        # --- Traffic Signal ---------------------------------------------------
        "Current_TLS_Phase": tls["Current_TLS_Phase"],
        "Remaining_Green_Time": tls["Remaining_Green_Time"],
        # --- Direction Counts -------------------------------------------------
        "North_Count": acc["North_Count"],
        "South_Count": acc["South_Count"],
        "East_Count": acc["East_Count"],
        "West_Count": acc["West_Count"],
        # --- Vehicle Categories -------------------------------------------------
        "Car_Count": acc["Car_Count"],
        "Bus_Count": acc["Bus_Count"],
        "Truck_Count": acc["Truck_Count"],
        "Motorcycle_Count": acc["Motorcycle_Count"],
        "Emergency_Vehicle_Count": acc["Emergency_Vehicle_Count"],
        # --- Environment --------------------------------------------------------
        "Total_CO2_Emission": derived["Total_CO2_Emission"],
        "Total_Fuel_Consumption": derived["Total_Fuel_Consumption"],
        "Total_NOx_Emission": derived["Total_NOx_Emission"],
        "Total_PMx_Emission": derived["Total_PMx_Emission"],
        # --- Traffic Performance --------------------------------------------------
        "Average_Travel_Time": avg_travel_time,
        "Average_Delay": derived["Average_Delay"],
        "Intersection_Throughput": throughput,  # FIXED: removed duplicate Vehicles_Exited
        # --- AI Target Labels -----------------------------------------------------
        "Congestion_Level": congestion,
        "Recommended_Green_Time": get_recommended_green_time(congestion),
    }


# =============================================================================
# Main Execution
# =============================================================================

def main() -> None:
    """Run the full simulation loop and export Dataset V2.5."""
    logger.info("=" * 60)
    logger.info(" SUMO TraCI Dataset V2.5 Collector")
    logger.info("=" * 60)

    if not INCOMING_EDGE_DIRECTION_MAP:
        logger.warning(
            "INCOMING_EDGE_DIRECTION_MAP is empty. Direction counts will all "
            "be zero. Please configure your incoming edge IDs at the top of "
            "this script."
        )

    start_sumo()

    lane_ids = get_monitored_lanes()  # computed once; lane geometry is static

    dataset: List[Dict[str, Any]] = []
    step_counter = 0
    entry_times: Dict[str, float] = {}

    try:
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            step_counter += 1
            current_time = traci.simulation.getTime()

            lane_data = get_lane_aggregate_data(lane_ids)
            acc = process_vehicles_single_pass()
            derived = compute_derived_metrics(acc, lane_data)
            avg_travel_time, throughput, entry_times = update_travel_time_metrics(
                entry_times, current_time
            )
            tls = get_tls_info()

            record = build_record(
                step_counter, lane_data, acc, derived, tls, avg_travel_time, throughput
            )
            dataset.append(record)

            if step_counter % 100 == 0:
                logger.info(
                    "Step %5d | Time=%4d | Vehicles=%2d | Congestion=%d",
                    step_counter,
                    record["Time"],
                    record["Vehicle_Count"],
                    record["Congestion_Level"],
                )

        logger.info("Simulation finished. Total steps collected: %d", step_counter)

    except Exception:
        logger.exception("Simulation aborted due to an error.")
        raise

    finally:
        traci.close()
        logger.info("TraCI connection closed.")

    columns = [
        "Time", "Simulation_Step",
        "Vehicle_Count", "Queue_Length", "Halting_Vehicles",
        "Traffic_Density", "Lane_Occupancy",
        "Average_Speed", "Maximum_Speed", "Minimum_Speed", "Average_Acceleration",
        "Average_Waiting_Time", "Maximum_Waiting_Time",
        "Current_TLS_Phase", "Remaining_Green_Time",
        "North_Count", "South_Count", "East_Count", "West_Count",
        "Car_Count", "Bus_Count", "Truck_Count", "Motorcycle_Count",
        "Emergency_Vehicle_Count",
        "Total_CO2_Emission", "Total_Fuel_Consumption",
        "Total_NOx_Emission", "Total_PMx_Emission",
        "Average_Travel_Time", "Average_Delay", "Intersection_Throughput",
        "Congestion_Level", "Recommended_Green_Time",
    ]

    df = pd.DataFrame(dataset, columns=columns)
    df.to_csv(OUTPUT_CSV, index=False)

    logger.info("=" * 60)
    logger.info(" Dataset V2.5 exported: %s", OUTPUT_CSV)
    logger.info(" Records written: %d", len(df))
    logger.info("=" * 60)

    print("\nPreview (first 5 rows):")
    print(df.head())

    print("\nCongestion Level distribution:")
    print(df["Congestion_Level"].value_counts().sort_index())

    print("\nRecommended Green Time distribution:")
    print(df["Recommended_Green_Time"].value_counts().sort_index())


if __name__ == "__main__":
    main()