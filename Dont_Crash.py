from dotenv import dotenv_values
import requests
import webbrowser
import websocket
import json
from lib.math import normalize_heading
import time

FRONTEND_BASE = "noflight.monad.fi"
BACKEND_BASE = "noflight.monad.fi/backend"

game_id = None


def on_message(ws: websocket.WebSocketApp, message):
    [action, payload] = json.loads(message)

    if action != "game-instance":
        print([action, payload])
        return

     # New game tick arrived!
    game_state = json.loads(payload["gameState"])
    commands = generate_commands(game_state)

    time.sleep(0.1)
    ws.send(json.dumps(["run-command", {"gameId": game_id, "payload": commands}]))


def on_error(ws: websocket.WebSocketApp, error):
    print(error)


def on_open(ws: websocket.WebSocketApp):
    print("OPENED")
    ws.send(json.dumps(["sub-game", {"id": game_id}]))


def on_close(ws, close_status_code, close_msg):
    print("CLOSED")


def turn_towards(destination, current_dir):
    diff = normalize_heading(current_dir-destination)
    if diff <= 180:
        new_dir = normalize_heading(current_dir - min(diff, 20))
    else:
        new_dir = normalize_heading(current_dir + min(diff, 20))
    return new_dir


def distance(x1, y1, x2, y2):
    return ((x2-x1)**2 + (y2-y1)**2)**0.5

# Change this to your own implementation
# Funnily enough this run just ok with the code from Criss Cross :D
def generate_commands(game_state):
    commands = []
    #print(game_state)
    for aircraft in game_state["aircrafts"]:
        airport = [airport for airport in game_state['airports'] if airport['name'] == aircraft['destination']][0]
        
        new_dir = turn_towards(airport['direction'], aircraft['direction'])
        
        if aircraft['destination'] == 'A':
            print(aircraft)
            if aircraft['position']['y'] >= 0:
                new_dir = turn_towards(0, aircraft['direction'])
                if aircraft['position']['x'] >= 30:
                    new_dir = turn_towards(90, aircraft['direction'])
                if aircraft['position']['y'] > 80:
                    new_dir = turn_towards(180, aircraft['direction'])
                if aircraft['position']['x'] <= -16:
                    new_dir = turn_towards(270, aircraft['direction'])

        if aircraft['destination'] == 'B' or aircraft['destination'] == 'C':
            if aircraft['position']['y'] >= 0:
                new_dir = turn_towards(0, aircraft['direction'])
                if aircraft['position']['x'] >= airport['position']['x']-16:
                    new_dir = turn_towards(270, aircraft['direction'])
        


        commands.append(f"HEAD {aircraft['id']} {new_dir}")


    return commands


def main():
    config = dotenv_values()
    res = requests.post(
        f"https://{BACKEND_BASE}/api/levels/{config['LEVEL_ID']}",
        headers={
            "Authorization": config["TOKEN"]
        })

    if not res.ok:
        print(f"Couldn't create game: {res.status_code} - {res.text}")
        return

    game_instance = res.json()

    global game_id
    game_id = game_instance["entityId"]

    url = f"https://{FRONTEND_BASE}/?id={game_id}"
    print(f"Game at {url}")
    webbrowser.open(url, new=2)
    time.sleep(2)

    ws = websocket.WebSocketApp(
        f"wss://{BACKEND_BASE}/{config['TOKEN']}/", on_message=on_message, on_open=on_open, on_close=on_close, on_error=on_error)
    ws.run_forever()


if __name__ == "__main__":
    main()