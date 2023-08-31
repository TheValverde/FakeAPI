from flask import Flask, jsonify, render_template, request
import random

app = Flask(__name__)

# Variable to keep track of whether the API is enabled or disabled
api_enabled = False

# Sample data schema
sample_data = {
    "user": {
        "id": lambda: random.randint(1, 1000),
        "name": lambda: random.choice(["Alice", "Bob", "Charlie"]),
        "email": lambda: random.choice(["alice@example.com", "bob@example.com", "charlie@example.com"])
    },
    "order": {
        "id": lambda: random.randint(1000, 2000),
        "amount": lambda: round(random.uniform(10.0, 100.0), 2),
        "status": lambda: random.choice(["shipped", "pending", "cancelled"])
    },
    "nhl": {
        "game": {
            "id": lambda: f"2021020{random.randint(100,999)}",
            "date": lambda: "2023-09-01",
            "status": lambda: "live",
            "period": lambda: random.randint(1, 3),
            "time_left": lambda: f"{random.randint(0, 19)}:{random.randint(0, 59):02d}"
        },
        "teams": {
            "home": {
                "name": lambda: "New York Rangers",
                "score": lambda: random.randint(0, 5)
            },
            "away": {
                "name": lambda: "Boston Bruins",
                "score": lambda: random.randint(0, 5)
            }
        },
        "players": {
            "player1": {
                "name": lambda: "Player 1",
                "goals": lambda: random.randint(0, 2),
                "assists": lambda: random.randint(0, 2)
            },
            "player2": {
                "name": lambda: "Player 2",
                "goals": lambda: random.randint(0, 2),
                "assists": lambda: random.randint(0, 2)
            }
        },
        "penalties": lambda: [{
            "player": "Player 1",
            "type": "Hooking",
            "duration": "2min"
        }]
    }
}


# Recursive function to generate sample data
def generate_sample_data(data_schema):
    result = {}
    for key, value in data_schema.items():
        if callable(value):
            result[key] = value()
        elif isinstance(value, dict):
            result[key] = generate_sample_data(value)
    return result

@app.route('/')
def index():
    global api_enabled
    return render_template('index.html', api_enabled=api_enabled)

@app.route('/toggle', methods=['POST'])
def toggle_api():
    global api_enabled
    api_enabled = not api_enabled
    return "OK", 200

@app.route('/api/<string:endpoint>', methods=['GET'])
def api_endpoint(endpoint):
    global api_enabled
    if api_enabled:
        if endpoint in sample_data:
            data = generate_sample_data(sample_data[endpoint])
            return jsonify(data), 200
        else:
            return "Endpoint not found", 404
    else:
        return "API is disabled", 503

@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    response.cache_control.no_cache = True
    response.cache_control.must_revalidate = True
    return response

if __name__ == '__main__':
    app.run(debug=True)