from flask import Flask, jsonify, render_template, request
import random, json, threading, time
from math import sqrt


app = Flask(__name__)

# Variable to keep track of whether the API is enabled or disabled
api_enabled = False

#Initialize game state
#Setting rink dims as 100x50 just to keep it simple
game_state = {
    "game_time": 0,
    "score": {"home": 0, "away": 0},
    "player_positions": {"home": {}, "away": {}},  # Initialize as empty dictionaries
    "puck_position": [50, 25],
    "puck_possession": None,  # None or "home" or "away"
}

# Define roles
ROLES = ["Center", "Wing", "Wing", "Defense", "Defense"]

def init_players():
    for team in ["home", "away"]:
        for i, role in enumerate(ROLES):
            player_key = f"player{i+1}"
            game_state["player_positions"][team][player_key] = {
                "position": [random.randint(0, 100), random.randint(0, 50)],
                "role": role,
                "state": "idle",
            }
init_players()
def distance(point1, point2):
    return sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def move_point(start, end, speed):
    delta_x = end[0] - start[0]
    delta_y = end[1] - start[1]
    new_x = start[0] + delta_x * speed
    new_y = start[1] + delta_y * speed
    return [new_x, new_y]

def closest_player_to_puck(team):
    closest_player = None
    closest_distance = float('inf')

    for player, position in game_state["player_positions"][team].items():
        dist = distance(position, game_state["puck_position"])
        if dist < closest_distance:
            closest_distance = dist
            closest_player = player

    return closest_player

# Function to decide next action based on role and game state
def decide_action(team, player_info):
    if game_state["puck_possession"] == team:
        if player_info["role"] == "Center":
            return "make_pass" if random.random() > 0.5 else "take_shot"
        elif player_info["role"] == "Wing":
            return "position_for_pass"
        else:  # Defense
            return "defend"
    else:
        if player_info["role"] == "Defense":
            return "defend"
        else:
            return "chase_puck"

def move_based_on_state(player_info):
    state = player_info["state"]
    target_point = None
    
    if state == "chase_puck":
        target_point = game_state["puck_position"]
    elif state == "defend":
        target_point = [25, 25]  # example defensive position
    elif state == "position_for_pass":
        target_point = [75, 25]  # example position for receiving pass
    elif state == "make_pass":
        target_point = [80, 20]  # example position for making a pass
    elif state == "take_shot":
        target_point = [100, 25]  # example position for taking a shot

    if target_point:
        return move_point(player_info["position"], target_point, 0.1)
    else:
        return player_info["position"]


# Function to update the game state
def update_game_state():
    global game_state
    while True:
        game_state["game_time"] += 1
        puck_target = [random.randint(0, 100), random.randint(0, 50)]
        game_state["puck_position"] = move_point(game_state["puck_position"], puck_target, 0.1)
        
        for team in ["home", "away"]:
            for player_key, player_info in game_state["player_positions"][team].items():
                player_info["state"] = decide_action(team, player_info)
                player_info["position"] = move_based_on_state(player_info)

        # Implement basic goal logic
        if game_state["puck_position"][0] <= 0:
            game_state["score"]["away"] += 1
            game_state["puck_position"] = [50, 25]
        elif game_state["puck_position"][0] >= 100:
            game_state["score"]["home"] += 1
            game_state["puck_position"] = [50, 25]
            
        time.sleep(1)
        
# Start the thread to update game state
game_thread = threading.Thread(target=update_game_state)
game_thread.daemon = True
game_thread.start()

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

@app.route('/api/nhl_game', methods=['GET'])
def api_nhl_game():
    global api_enabled
    if api_enabled:
        return jsonify(game_state), 200
    else:
        return "API is disabled", 503


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