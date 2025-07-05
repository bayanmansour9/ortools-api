from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/optimize', methods=['POST'])
def optimize():
    data = request.get_json()
    locations = data.get('locations', [])

    # رد تجريبي (بدون OR-Tools حالياً)
    return jsonify({
        'received_locations': locations,
        'route': list(range(len(locations)))
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
