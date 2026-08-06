import os
import sys
import pandas as pd

# SUMO
if "SUMO_HOME" not in os.environ:
    raise EnvironmentError("SUMO_HOME not set")

tools = os.path.join(os.environ["SUMO_HOME"], "tools")
sys.path.append(tools)

import traci

sumoBinary = os.path.join(os.environ["SUMO_HOME"], "bin", "sumo")

sumoCmd = [
    sumoBinary,
    "-c",
    r"C:\Traffic Project\config\junction.sumocfg"
]

traci.start(sumoCmd)

dataset = []

while traci.simulation.getMinExpectedNumber() > 0:

    traci.simulationStep()

    time = traci.simulation.getTime()

    vehicleIDs = traci.vehicle.getIDList()

    vehicle_count = len(vehicleIDs)

    queue_length = 0
    total_speed = 0
    total_wait = 0

    for vid in vehicleIDs:

        speed = traci.vehicle.getSpeed(vid)
        wait = traci.vehicle.getWaitingTime(vid)

        total_speed += speed
        total_wait += wait

        if speed < 0.1:
            queue_length += 1

    avg_speed = total_speed / vehicle_count if vehicle_count else 0
    avg_wait = total_wait / vehicle_count if vehicle_count else 0

    dataset.append([
        int(time),
        vehicle_count,
        queue_length,
        round(avg_speed,2),
        round(avg_wait,2)
    ])

traci.close()

df = pd.DataFrame(dataset, columns=[
    "Time",
    "Vehicle_Count",
    "Queue_Length",
    "Average_Speed",
    "Average_Waiting_Time"
])

df.to_csv("traffic_dataset.csv", index=False)

print("Dataset created successfully!")
print(df.head())