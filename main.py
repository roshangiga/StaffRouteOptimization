import random
import math
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from ortools.constraint_solver import pywrapcp, routing_enums_pb2


def create_data_model():
    # Generate synthetic locations for 60 staff members in Mauritius
    num_staff = 30
    random.seed(3)  # For reproducibility
    locations = [(random.uniform(-20.5, -20.0), random.uniform(57.3, 57.8)) for _ in range(num_staff)]

    # Define the depot (Myt Tower in Ebene)
    depot_location = (-20.2430, 57.4924)  # Approximate location of Myt Tower in Ebene
    locations.insert(0, depot_location)

    # Generate random starting points for each vehicle
    vehicle_starts = [(random.uniform(-20.5, -20.0), random.uniform(57.3, 57.8)) for _ in range(6)]

    # Add starting points to locations
    for start in vehicle_starts:
        locations.append(start)

    # Get distance matrix using Euclidean distance
    distance_matrix = get_distance_matrix(locations)

    # Define vehicle capacities (between 5 to 10)
    vehicle_capacities = [random.randint(5, 10) for _ in range(6)]

    data = {
        'distance_matrix': distance_matrix,
        'demands': [1] * num_staff + [0] + [0] * 6,
        # 1 passenger for each staff, depot and starting points have no demand
        'vehicle_capacities': vehicle_capacities,
        'num_vehicles': len(vehicle_capacities),
        'depot': 0,
        'vehicle_starts': list(range(len(locations) - 6, len(locations))),  # Indices of vehicle starting points
        'vehicle_ends': [0] * 6,  # All vehicles end at the depot
        'locations': locations
    }
    return data


def print_data(data):
    print("Distance Matrix:")
    for row in data['distance_matrix']:
        print(row)

    print("\nDemands:")
    print(data['demands'])

    print("\nVehicle Capacities:")
    print(data['vehicle_capacities'])

    print("\nNumber of Vehicles:")
    print(data['num_vehicles'])

    print("\nDepot Index:")
    print(data['depot'])

    print("\nVehicle Start Indices:")
    print(data['vehicle_starts'])

    print("\nVehicle End Indices:")
    print(data['vehicle_ends'])

    print("\nLocations:")
    for loc in data['locations']:
        print(loc)

def get_distance_matrix(locations):
    distance_matrix = []
    for loc1 in locations:
        row = []
        for loc2 in locations:
            distance = euclidean_distance(loc1, loc2)
            row.append(distance)
        distance_matrix.append(row)
    return distance_matrix


def euclidean_distance(point1, point2):
    return int(math.sqrt(
        (point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) * 10000)  # Scale for better integer handling


def create_routing_model(data):
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']), data['num_vehicles'], data['vehicle_starts'],
                                           data['vehicle_ends'])
    routing = pywrapcp.RoutingModel(manager)

    transit_callback_index = register_transit_callback(routing, data, manager)
    add_capacity_constraints(routing, data, manager, transit_callback_index)

    return routing, manager


def register_transit_callback(routing, data, manager):
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    return routing.RegisterTransitCallback(distance_callback)


def add_capacity_constraints(routing, data, manager, transit_callback_index):
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        data['vehicle_capacities'],  # vehicle maximum capacities
        True,  # start cumul to zero
        'Capacity')


def solve_vrp(routing, manager):
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.seconds = 30

    return routing.SolveWithParameters(search_parameters)


def print_solution(data, manager, routing, solution):
    #shapefile_path = 'gadm41_MUS_1.shp'  # Replace with the actual path to the shapefile

    # Load the Mauritius shapefile
    #mauritius = gpd.read_file(shapefile_path)

    # Plot the Mauritius map
    #fig, ax = plt.subplots(figsize=(15, 15))
    #mauritius.plot(ax=ax, color='lightgrey', edgecolor='black')

    total_distance = 0
    vehicle_routes = []
    total_staff = sum(data['demands'][:-7])  # exclude depot and vehicle starts
    total_vehicle_capacity = sum(data['vehicle_capacities'])
    print(f'Total staff: {total_staff}')
    print(f'Total vehicle capacity: {total_vehicle_capacity}\n')

    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        route = []
        route_load = 0
        plan_output = f'------ Vehicle {vehicle_id} (capacity: {data["vehicle_capacities"][vehicle_id]}) ------\n\n'
        step = 1
        route_distance = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            if node_index < len(data['distance_matrix']):  # exclude depot and start locations
                route_load += data['demands'][node_index]
            route.append(node_index)
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            if manager.IndexToNode(index) < len(data['distance_matrix']):
                distance = data['distance_matrix'][manager.IndexToNode(previous_index)][manager.IndexToNode(index)]
                route_distance += distance
                plan_output += f' #{step} : {manager.IndexToNode(previous_index)} -> {manager.IndexToNode(index)} (distance: {distance / 1000.0:.2f} km)\n'
                step += 1
        route.append(manager.IndexToNode(index))
        vehicle_routes.append(route)

        # Print the route
        plan_output += f'Total distance: {route_distance / 1000.0:.2f} km\n'
        plan_output += f'Total Load: {route_load}\n'
        print(plan_output)

    print('Total distance of all routes: {:.2f} km'.format(total_distance / 1000.0))
    plot_routes(data, vehicle_routes)


def plot_routes(data, vehicle_routes):
    plt.figure(figsize=(15, 15))
    locations = data['locations']
    depot = locations[0]
    vehicle_starts = data['vehicle_starts']
    colors = ['b', 'g', 'r', 'c', 'm', 'y']

    for vehicle_id, route in enumerate(vehicle_routes):
        color = colors[vehicle_id % len(colors)]
        for i in range(len(route) - 1):
            from_node = route[i]
            to_node = route[i + 1]
            from_loc = locations[from_node]
            to_loc = locations[to_node]
            plt.plot([from_loc[1], to_loc[1]], [from_loc[0], to_loc[0]], color + 'o-')
            plt.text(from_loc[1], from_loc[0], f'{from_node}', fontsize=12, ha='right')
            plt.text((from_loc[1] + to_loc[1]) / 2, (from_loc[0] + to_loc[0]) / 2,
                     f'{data["distance_matrix"][from_node][to_node] / 1000.0:.2f} km',
                     fontsize=11, ha='center', va='center', color=color)
            arrow = FancyArrowPatch((from_loc[1], from_loc[0]), (to_loc[1], to_loc[0]),
                                    color=color, arrowstyle='->', mutation_scale=25, lw=1, fill=False)
            plt.gca().add_patch(arrow)


    for start in vehicle_starts:
        start_loc = locations[start]
        plt.plot(start_loc[1], start_loc[0], 'ko', markersize=10)
        vehicle_id = data['vehicle_starts'].index(start)
        plt.text(start_loc[1], start_loc[0], f'V{vehicle_id} ({data["vehicle_capacities"][vehicle_id]})', fontsize=12,
                 ha='right')

    plt.plot(depot[1], depot[0], 'rs', markersize=15)  # Depot
    plt.text(depot[1], depot[0], 'Depot', fontsize=12, ha='right')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Vehicle Routes')
    plt.show()


def main():
    data = create_data_model()
    print_data(data)

    routing, manager = create_routing_model(data)
    solution = solve_vrp(routing, manager)
    if solution:
        print_solution(data, manager, routing, solution)


if __name__ == '__main__':
    main()
