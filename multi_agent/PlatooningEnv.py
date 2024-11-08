from pettingzoo import ParallelEnv
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import traci
from sumolib import checkBinary

TOTAL_STEPS = 3000

class PlatooningParallelEnv(ParallelEnv):
    metadata = {'render_modes': ['human'], 'name': "platooning_v2"}

    def __init__(self):
        super().__init__()

        self.num_platoons = 2  # Number of platoons
        self.agents = [f"platoon_{i}_follower" for i in range(self.num_platoons)]
        self.possible_agents = self.agents.copy()

        self.action_spaces = {agent: spaces.Discrete(3) for agent in self.agents}
        self.observation_spaces = {
            agent: spaces.Box(low=np.array([0, 0]), high=np.array([50, 200]), dtype=np.float32) for agent in self.agents
        }

        self.STEPS = 0
        self.sumo_binary = checkBinary('sumo-gui') # Adjust this path to your SUMO binary
        traci.start([self.sumo_binary, "-c", "./maps/singlelane/singlelane.sumocfg", "--tripinfo-output", "tripinfo.xml"])

        for _ in range(20):
            traci.simulationStep()
            self.STEPS += 1

        self.vehicles = self.initialize_vehicles()

    def initialize_vehicles(self):

        vehicles = {}
        vehicles1 = traci.vehicle.getIDList()
        if not vehicles1:
            raise ValueError("No vehicles found in the simulation.")

        # Sort vehicles based on their lane position (x coordinate)
        vehicles_sorted_by_x = sorted(vehicles1, key=lambda veh: traci.vehicle.getPosition(veh)[0], reverse=True)
        if len(vehicles_sorted_by_x) < 2:
            raise ValueError("Not enough vehicles in the simulation to form a platoon.")

        for i in range(self.num_platoons):
                leader_index = 3 * i
                follower_index = 3 * i + 1
                follower2_index = 3 * i + 2
                leader_id = vehicles_sorted_by_x[leader_index]
                follower_id = vehicles_sorted_by_x[follower_index]
                follower_id2 = vehicles_sorted_by_x[follower2_index]
                vehicles[f"platoon_{i}_follower"] = {"leader": leader_id, "follower": follower_id, "follower2": follower_id2}

        return vehicles
    
    def calculate_distance(self, leader_id, follower_id):
        leader_pos = traci.vehicle.getPosition(leader_id)
        follower_pos = traci.vehicle.getPosition(follower_id)

        distance = ((leader_pos[0] - follower_pos[0])**2 + (leader_pos[1] - follower_pos[1])**2)**0.5
        return distance

    def step(self, actions):
        self.STEPS += 1
        rewards = {}
        observations = {}
        dones = {}
        infos = {agent: {} for agent in self.agents}

        for agent, action in actions.items():
            self.adjust_leader_speed(agent)
            self.apply_action(agent, action)

        traci.simulationStep()

        for agent in self.agents:
            observations[agent] = self.observe(agent)
            rewards[agent] = self.calculate_reward(agent)
            dones[agent] = self.STEPS >= TOTAL_STEPS

        if self.STEPS >= TOTAL_STEPS:
            traci.close()

        return observations, rewards, dones, infos
    

    def adjust_leader_speed(self, agent):
        # Desired headway distance between the leader and the first follower
        desired_speed = 5
        leader = self.vehicles[agent]["leader"]
        traci.vehicle.setSpeed(leader, desired_speed)

    # def adjust_leader_speed(self, agent):
    #     # Desired headway distance between the leader and the first follower
    #     desired_headway = 15

    #     leader = self.vehicles[agent]["leader"]
    #     first_follower = self.vehicles[agent]["follower"]

    #     current_headway = self.calculate_distance(leader, first_follower)

    #     if current_headway < desired_headway:
    #         # If too close, decrease leader's speed
    #         new_speed_leader = max(traci.vehicle.getSpeed(self.leader) + 1, 15)  
    #     elif current_headway > desired_headway:
    #         # If too far, increase leader's speed, but set a maximum limit
    #         new_speed_leader = min(traci.vehicle.getSpeed(self.leader) - 1, 5)  
    #     else:
    #         # Maintain current speed if the distance is within an acceptable range
    #         new_speed_leader = traci.vehicle.getSpeed(self.leader)
        
    #     traci.vehicle.setSpeed(self.leader, new_speed_leader)

    def apply_action(self, agent, action):
        follower_id = self.vehicles[agent]["follower"]
        follower_id2 = self.vehicles[agent]["follower2"]
        leader = self.vehicles[agent]["leader"]
        leader_lane_index = traci.vehicle.getLaneIndex(leader)
        leader_speed = traci.vehicle.getSpeed(leader)
        current_speed = traci.vehicle.getSpeed(follower_id)
        if action == 0:  # Accelerate
            traci.vehicle.setSpeed(follower_id, current_speed + 3)
        elif action == 1:  # Decelerate
            traci.vehicle.setSpeed(follower_id, current_speed - 3)
        else:
            traci.vehicle.setSpeed(follower_id, leader_speed)
        # No action needed for maintaining speed (action == 2)


        # Logic for adjusting the second follower's speed, aiming for a dynamic desired distance
        dynamic_desired_distance = 10 + 0.1 * traci.vehicle.getSpeed(follower_id2)
        current_distance = self.calculate_distance(follower_id, follower_id2)
        
        # Adjust the second follower's speed based on the dynamic desired distance
        if current_distance > dynamic_desired_distance + 5:
            new_speed_second_follower = traci.vehicle.getSpeed(follower_id2) + 3
        elif current_distance < dynamic_desired_distance - 5:
            new_speed_second_follower = traci.vehicle.getSpeed(follower_id2) - 3
        else:  # Slight adjustment based on the first follower's action
            if action == 0:  # Accelerate
                new_speed_second_follower = min(traci.vehicle.getSpeed(follower_id2) + 3, traci.vehicle.getSpeed(follower_id))
            elif action == 1:  # Decelerate
                new_speed_second_follower = traci.vehicle.getSpeed(follower_id2) - 3
            else:
                new_speed_second_follower = traci.vehicle.getSpeed(leader)

        # Update the speed of the second follower
        traci.vehicle.setSpeed(follower_id2, new_speed_second_follower)

        traci.vehicle.changeLane(follower_id,leader_lane_index, 0)
        traci.vehicle.setLaneChangeMode(follower_id, 512)

        traci.vehicle.changeLane(follower_id2,leader_lane_index, 0)
        traci.vehicle.setLaneChangeMode(follower_id2, 512)

    def observe(self, agent):
        follower_id = self.vehicles[agent]["follower"]
        leader_id = self.vehicles[agent]["leader"]
        follower_speed = traci.vehicle.getSpeed(follower_id)
        current_headway = self.calculate_distance(leader_id , follower_id )
        return np.array([follower_speed, current_headway], dtype=np.float32)

    def calculate_reward(self, agent):
        reward=0
        follower_id = self.vehicles[agent]["follower"]
        leader_id = self.vehicles[agent]["leader"]
        current_headway = self.calculate_distance(leader_id, follower_id)

        if 0 < current_headway <= 35:
            reward += 1  # Positive reward for maintaining optimal distance
        else:
            reward -= 1  # Negative reward for being too close or too far
        
        return reward

    def reset(self):
        traci.close()
        traci.start([self.sumo_binary, "-c", "./maps/singlelane/singlelane.sumocfg", "--tripinfo-output", "tripinfo.xml"])
        for _ in range(20):
            traci.simulationStep()
            self.STEPS += 1
        self.vehicles = self.initialize_vehicles()
        self.STEPS = 0
        return {agent: self.observe(agent) for agent in self.agents}

    def render(self, mode='human'):
        pass

    def close(self):
        traci.close()
