import os
from waitress import serve
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/optimize', methods=['POST'])
def optimize():
    data = request.get_json()
    locations = data.get('locations', [])
    return jsonify({
        'received_locations': locations,
        'route': list(range(len(locations)))
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # اقرأ المنفذ من البيئة أو استخدم 8080 كخيار افتراضي
    serve(app, host="0.0.0.0", port=port)
