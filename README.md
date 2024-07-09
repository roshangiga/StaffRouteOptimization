# Vehicle Routing Problem Optimization

This project solves a Vehicle Routing Problem (VRP) for optimizing the pickup and drop-off of staff members using a fleet of vehicles with varying capacities.

## Features

- **Optimized Routing**: Minimize the total distance traveled by all vehicles.
- **Capacity Constraints**: Ensure vehicles do not exceed their passenger capacities.
- **Demand Fulfillment**: Ensure all staff members are picked up and transported to the depot.
- **Customizable Configuration**: Define vehicle capacities, starting points, and depot location.

## Requirements

- Python 3.x
- `ortools` library for solving the VRP
- `geopandas` and `matplotlib` for visualizing the routes and the map

## Installation

```bash
pip install ortools geopandas matplotlib
```

# Vehicle Routing Problem (VRP) Constraints and Requirements

## Vehicle Capacity
- Each vehicle has a defined capacity, limiting the number of passengers it can carry at any given time.
- The capacity of each vehicle is specified and must be adhered to throughout the routing.

## Demand at Each Location
- Each staff member location has a demand of one passenger.
- The depot and vehicle starting points have a demand of zero.
- The total load on a vehicle is the sum of the demands of all visited locations, excluding the depot.

## Depot
- The depot is the starting and ending point for all routes.
- Vehicles must start and end their routes at the depot.

## Vehicle Start and End Locations
- Each vehicle has a specified starting location.
- All vehicles end their routes at the depot.

## Distance Calculation
- The distances between locations are calculated using the Euclidean distance formula.
- The total distance for each vehicle's route is the sum of the distances between consecutive locations on that route.

## Routing Constraints
- The routing model must ensure that all staff members are picked up and transported to the depot.
- Each vehicle must respect its capacity constraint while picking up staff members.
- The routes must minimize the total distance traveled by all vehicles.

## Solver Configuration
- The solver uses a specific search strategy to find the optimal or near-optimal routes.
- The search strategy used is "PATH_CHEAPEST_ARC," which builds a solution by repeatedly connecting the nearest node.

## Exclusion of Depot from Load Calculation
- The depot does not contribute to the vehicle load.
- The demand of the depot is always zero and is excluded from the load calculation.

## Visualization

The routes are visualized on a map of Mauritius, showing the paths taken by each vehicle, the distances between stops, and the vehicle loads.

![Route Visualization](https://github.com/roshangiga/StaffRouteOptimization/blob/main/myplot.png)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Google OR-Tools](https://developers.google.com/optimization/)
- [GeoPandas](https://geopandas.org/)
- [Matplotlib](https://matplotlib.org/)
- [Natural Earth Data](https://www.naturalearthdata.com/)
- [GADM](https://gadm.org/)

