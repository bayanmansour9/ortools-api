from flask import Flask, request, jsonify
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

app = Flask(__name__)

@app.route('/optimize', methods=['POST'])
def optimize():
    data = request.get_json()
    locations = data.get('locations', [])

    # مثال: نستخدم OR-Tools لحل مشكلة مسار البائع المتجول (TSP)

    # عدد النقاط
    n = len(locations)
    if n == 0:
        return jsonify({'error': 'No locations provided'}), 400

    # حساب مسافة إقليدية بين نقطتين
    def distance(i, j):
        x1, y1 = locations[i]
        x2, y2 = locations[j]
        return int(((x1 - x2)**2 + (y1 - y2)**2)**0.5 * 1000)  # تقريب بالمتر

    # انشاء مصفوفة المسافات
    dist_matrix = [[distance(i, j) for j in range(n)] for i in range(n)]

    # إنشاء مدير التوجيه
    manager = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manager)

    def dist_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return dist_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(dist_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # إعداد معايير البحث
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # حل المشكلة
    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        route = []
        index = routing.Start(0)
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route.append(node)
            index = solution.Value(routing.NextVar(index))
        route.append(manager.IndexToNode(index))  # العودة للنقطة الأولى

        return jsonify({
            'received_locations': locations,
            'optimized_route': route
        })
    else:
        return jsonify({'error': 'No solution found'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
