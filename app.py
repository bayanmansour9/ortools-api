import os
from flask import Flask, request, jsonify
from waitress import serve
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

app = Flask(__name__)

@app.route('/optimize', methods=['POST'])
def optimize():
    data = request.get_json()
    locations = data.get('locations', [])

    if not locations or len(locations) < 2:
        return jsonify({'error': 'Please provide at least 2 locations'}), 400

    # Create distance matrix
    def euclidean_distance(i, j):
        x1, y1 = locations[i]
        x2, y2 = locations[j]
        return int(((x1 - x2)**2 + (y1 - y2)**2)**0.5 * 1000)

    dist_matrix = [[euclidean_distance(i, j) for j in range(len(locations))] for i in range(len(locations))]

    manager = pywrapcp.RoutingIndexManager(len(dist_matrix), 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        return dist_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        return jsonify({'error': 'No solution found'}), 500

    route = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        route.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    route.append(manager.IndexToNode(index))  # return to start

    return jsonify({
        'received_locations': locations,
        'optimized_route': route
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    serve(app, host="0.0.0.0", port=port)
