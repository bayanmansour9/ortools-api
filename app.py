import os
from flask import Flask, request, jsonify
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

app = Flask(__name__)
SCALE = 1000  # ثابت لتحويل الكسور العشرية لأعداد صحيحة

def solve_vrp(data):
    model_data = {
        'distance_matrix': data['distance_matrix'],
        'demands_weight': [0] + data['weights'],
        'demands_volume': [0] + data['volumes'],
        'vehicle_capacities_weight': data['vehicle_capacities_weight'],
        'vehicle_capacities_volume': data['vehicle_capacities_volume'],
        'store_ids': data['store_ids'],
        'warehouse_index': data['warehouse_index'],
        'num_vehicles': len(data['vehicle_capacities_weight']),
        'depot': data['warehouse_index']
    }

    manager = pywrapcp.RoutingIndexManager(
        len(model_data['distance_matrix']),
        model_data['num_vehicles'],
        model_data['depot']
    )
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(model_data['distance_matrix'][from_node][to_node])

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    def demand_weight_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return int(model_data['demands_weight'][from_node])

    weight_callback_index = routing.RegisterUnaryTransitCallback(demand_weight_callback)
    routing.AddDimensionWithVehicleCapacity(
        weight_callback_index, 0,
        model_data['vehicle_capacities_weight'],
        True, 'Weight'
    )

    def demand_volume_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return int(model_data['demands_volume'][from_node])

    volume_callback_index = routing.RegisterUnaryTransitCallback(demand_volume_callback)
    routing.AddDimensionWithVehicleCapacity(
        volume_callback_index, 0,
        model_data['vehicle_capacities_volume'],
        True, 'Volume'
    )

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

    solution = routing.SolveWithParameters(search_parameters)

    if not solution:
        return {'error': 'No solution found'}

    result = {'routes': []}
    for vehicle_id in range(model_data['num_vehicles']):
        index = routing.Start(vehicle_id)
        route = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != model_data['depot']:
                store_index = node - 1
                if store_index < len(model_data['store_ids']):
                    route.append(model_data['store_ids'][store_index])
            index = solution.Value(routing.NextVar(index))

        if route:
            result['routes'].append({
                'vehicle_id': vehicle_id,
                'store_ids': route
            })

    return result

@app.route('/optimize', methods=['POST'])
def optimize():
    try:
        data = request.get_json()
        result = solve_vrp(data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    from waitress import serve
    port = int(os.environ.get("PORT", 8080))
    serve(app, host="0.0.0.0", port=port)
