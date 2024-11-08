import csv
import traci

# Open a CSV file in write mode
with open('/Users/antonyjalappat/final_final_project/clustering_data_extraction/Sample data extraction/vehicle_data.csv', 'w', newline='') as csvfile:
    # Define the CSV writer
    writer = csv.writer(csvfile)

    # Write header row
    writer.writerow(['Vehicle_ID', 'X', 'Y', 'Speed', 'Angle', 'Lane_Position'])
    
    traci.start(['sumo', '-c', '/Users/antonyjalappat/final_final_project/clustering_data_extraction/maps/singlelane/singlelane.sumocfg'])
    
    # Advance simulation by 100 seconds
    while traci.simulation.getCurrentTime() <= 900000:  # 100 seconds in milliseconds
        traci.simulationStep()

    # Get the IDs of all vehicles in the simulation after 100 seconds
    vehicle_ids = traci.vehicle.getIDList()

    # Iterate over each vehicle and get its properties
    for vehicle_id in vehicle_ids:
        # Get the position (x, y) of the vehicle
        vehicle_position = traci.vehicle.getPosition(vehicle_id)
        x, y = vehicle_position

        # Get the angle of the vehicle
        angle = traci.vehicle.getAngle(vehicle_id)

        # Get the speed of the vehicle
        speed = traci.vehicle.getSpeed(vehicle_id)

        # Get the lane position of the vehicle
        lane_position = traci.vehicle.getLanePosition(vehicle_id)

        # Write the vehicle data to the CSV file
        writer.writerow([vehicle_id, x, y, speed, angle, lane_position])


# Close the TraCI connection
traci.close()
