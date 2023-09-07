from pythonosc import udp_client
import requests
import time
import tkinter as tk
import threading

# Initialize OSC client
client = udp_client.SimpleUDPClient("127.0.0.1", 5005)

# Your Flask API endpoint
api_endpoint = "http://127.0.0.1:5000/api/nhl_game"

def translate_coordinates(x, y, rink_dims=(100, 50), canvas_dims=(500, 250)):
    rink_x, rink_y = rink_dims
    canvas_x, canvas_y = canvas_dims
    scale_x = canvas_x / rink_x
    scale_y = canvas_y / rink_y
    return x * scale_x, y * scale_y

def fetch_data():
    while True:
        try:
            response = requests.get(api_endpoint)
            if response.status_code == 200:
                data = response.json()

                # Update Tkinter labels
                game_time_label.config(text=f"Game Time: {data['game_time']}")
                score_label.config(text=f"Score (Home/Away): {data['score']['home']} / {data['score']['away']}")
                puck_position_label.config(text=f"Puck Position: {data['puck_position']}")
                
                # Update canvas
                canvas.delete("all")
                for team in ['home', 'away']:
                    for player, player_info in data['player_positions'][team].items():
                        position = player_info['position']
                        x, y = translate_coordinates(position[0], position[1])
                        color = "blue" if team == "home" else "red"
                        canvas.create_oval(x-5, y-5, x+5, y+5, fill=color)
                
                puck_x, puck_y = translate_coordinates(data['puck_position'][0], data['puck_position'][1])
                canvas.create_oval(puck_x-5, puck_y-5, puck_x+5, puck_y+5, fill="black")

                # Send OSC messages
                client.send_message("/nhl/game_time", data["game_time"])
                client.send_message("/nhl/score/home", data["score"]["home"])
                client.send_message("/nhl/score/away", data["score"]["away"])
                client.send_message("/nhl/puck_position", data["puck_position"])

                for team in ["home", "away"]:
                    for player, player_info in data["player_positions"][team].items():
                        position = player_info['position']
                        client.send_message(f"/nhl/player_positions/{team}/{player}", position)

                print("OSC messages sent.")
            else:
                print(f"Failed to fetch data from API, status code: {response.status_code}")

        except Exception as e:
            print(f"An error occurred: {e}")

        time.sleep(1)

# Initialize Tkinter window
root = tk.Tk()
root.title("NHL Game OSC Client")

# Create labels to display the game state
game_time_label = tk.Label(root, text="Game Time: ")
game_time_label.pack()
score_label = tk.Label(root, text="Score (Home/Away): ")
score_label.pack()
puck_position_label = tk.Label(root, text="Puck Position: ")
puck_position_label.pack()

# Create a canvas for "live preview"
canvas = tk.Canvas(root, width=500, height=300, background="white")
canvas.pack()

# Start the fetch_data function in a new thread
t = threading.Thread(target=fetch_data)
t.daemon = True  # This makes the thread exit when the main program exits
t.start()

# Run the Tkinter event loop
root.mainloop()
