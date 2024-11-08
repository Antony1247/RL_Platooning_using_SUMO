import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import calinski_harabasz_score
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage

dataset = pd.read_csv('/Users/antonyjalappat/final_final_project/clustering_data_extraction/Sample data extraction/vehicle_data.csv')
X = dataset[['X', 'Y', 'Speed', 'Angle']].values
num_clusters = len(dataset)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
print(X_scaled);

cluster = AgglomerativeClustering(n_clusters=None, distance_threshold=3, linkage='ward')
cluster_labels = cluster.fit_predict(X_scaled)

# Ensure each cluster has at most 5 elements
cluster_assignments = {}
for i, label in enumerate(cluster_labels):
    if label not in cluster_assignments:
        cluster_assignments[label] = [i]
    elif len(cluster_assignments[label]) < 5:
        cluster_assignments[label].append(i)
    else:
        new_label = max(cluster_assignments.keys()) + 1
        cluster_assignments[new_label] = [i]

# Print the number of clusters and elements in each cluster
print("Number of clusters:", len(cluster_assignments))
for label, elements in cluster_assignments.items():
    print("Cluster", label, ":", elements)

# Add cluster labels to the dataset
dataset['Cluster'] = cluster_labels

leader_vehicles = {}
for label, elements in cluster_assignments.items():
    leader_vehicle = None
    for element in elements:
        vehicle = dataset.iloc[element]
        if leader_vehicle is None:
            leader_vehicle = vehicle
        else:
            # Choose the vehicle based on the angle criteria
            if vehicle['Angle'] >= 0 and vehicle['Angle'] <= 180:
                if vehicle['X'] > leader_vehicle['X'] or (vehicle['X'] == leader_vehicle['X'] and vehicle['Y'] > leader_vehicle['Y']):
                    leader_vehicle = vehicle
            elif vehicle['Angle'] > 180 and vehicle['Angle'] <= 360:
                if vehicle['X'] < leader_vehicle['X'] or (vehicle['X'] == leader_vehicle['X'] and vehicle['Y'] < leader_vehicle['Y']):
                    leader_vehicle = vehicle
    leader_vehicles[label] = leader_vehicle

# Set all speeds in each cluster to the speed of the leader vehicle in that cluster
for label, leader_vehicle in leader_vehicles.items():
    cluster_elements = cluster_assignments[label]
    for element_index in cluster_elements:
        dataset.at[element_index, 'Speed'] = leader_vehicle['Speed']


# Save the clusters with the vehicle data to a CSV file
with open('clustered_vehicle_data_with_leader.csv', 'w') as f:
    f.write("Cluster,Id,X,Y,Speed,Angle,Lane_position,Leader\n")
    for label, elements in cluster_assignments.items():
        for element in elements:
            vehicle = dataset.iloc[element]
            if vehicle.equals(leader_vehicles[label]):
                leader = 'Yes'
            else:
                leader = 'No'
            f.write(f"{label},{vehicle['Vehicle_ID']},{vehicle['X']},{vehicle['Y']},{vehicle['Speed']},{vehicle['Angle']},{vehicle['Lane_Position']},{leader}\n")

print("Clustered vehicle data with leaders saved successfully.")

# Plot the clusters
plt.figure(figsize=(8, 6))
for label, elements in cluster_assignments.items():
    cluster_X = X[elements]
    plt.scatter(cluster_X[:, 0], cluster_X[:, 1], label=f'Cluster {label}')
plt.title('Hierarchical Clustering')
plt.xlabel('X Coordinate')
plt.ylabel('Y Coordinate')
# plt.legend()
plt.show()


linked = linkage(X_scaled, 'ward')
plt.figure(figsize=(10, 7))
dendrogram(linked,
           orientation='top',
           labels=cluster_labels,
           distance_sort='descending',
           show_leaf_counts=True)
plt.title('Hierarchical Clustering Dendrogram')
plt.xlabel('Vehicles')
plt.ylabel('Distance')
plt.show()
