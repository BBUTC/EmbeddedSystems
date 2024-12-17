import time
from datetime import datetime
import random
import paho
from paho.mqtt import client as mqtt_client
import os

class GameState:
    received_roll = False
    dice_roll = None
    rps_results = [0, 0]
    received_rps = False
    received_movement = [False, 0]
    received_button = False
    client = None

def line_break(message):
    if len(message) < 16:
        for i in range(len(message), 16):
            message += " "
    return message

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
    # For paho-mqtt 2.0.0, you need to add the properties parameter.
    # def on_connect(client, userdata, flags, rc, properties):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    # Set Connecting Client ID
    client = mqtt_client.Client(client_id=client_id)

    # For paho-mqtt 2.0.0, you need to set callback_api_version.
    # client = mqtt_client.Client(client_id=client_id, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)

    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60

def on_disconnect(client, userdata, rc):
    print("Disconnected with result code: %s", rc)
    reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
    while reconnect_count < MAX_RECONNECT_COUNT:
        print("Reconnecting in %d seconds...", reconnect_delay)
        time.sleep(reconnect_delay)

        try:
            client.reconnect()
            print("Reconnected successfully!")
            return
        except Exception as err:
            print("%s. Reconnect failed. Retrying...", err)

        reconnect_delay *= RECONNECT_RATE
        reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
        reconnect_count += 1
    print("Reconnect failed after %s attempts. Exiting...", reconnect_count)
    client.loop_stop()

def publish(client, msg, topic):
    result = client.publish(topic, msg)
    # result: [0, 1]
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")
        
def print_to_lcd(message):
    publish(GameState.client, message, "board/request/display") 
    #print the message to the LCD screen

def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        
        msgTopics = msg.topic.split("/")
        # print("Debug : ",msgTopics)

        if msgTopics[-1] == "dice": # Check if the topic is the result topic
            GameState.dice_roll = [int(msg.payload.decode()), int(msgTopics[1][-1])] # Decode the received payload
            print(f"Received `{GameState.dice_roll[0]}` from `{msg.topic}` topic")
            GameState.received_roll = True  # Update the flag
        elif msgTopics[-1] == "rps":
            rops = msg.payload.decode().split(",")  # Decode the received payload
            GameState.rps_results = [int(x) for x in rops]
            GameState.received_rps = True  # Update the flag
        elif msgTopics[-1] == "hall":
            GameState.received_movement = [True, int(msgTopics[1][-1])]  # Update the flag
        elif msgTopics[-1] == "button":
            GameState.received_button = True  # Update the flag

    # topics = ["esp01/meeple0/result/dice", "esp01/meeple1/result/dice", "esp01/meeple0/hall", "esp01/meeple1/hall", 
    #           "board/result/rps"]
    client.subscribe("esp01/+/result/#")
    client.subscribe("board/result/#")
    client.on_message = on_message

client_id = ""
if os.getenv('MQTT_Host') == None:
    broker = "localhost"
else :
    broker = os.getenv('MQTT_Host')

port = 1883

class Meeple:
    def __init__(self, name, short_name, position):
        self.name = name
        self.short_name = short_name
        self.position = position
        self.initial_position = position

    def move(self, steps, meepleNumber):
        self.position += steps
        print_to_lcd(f"Meeple {meepleNumber} Pos: {self.position}")

    def reset_position(self, meepleNumber):
        print_to_lcd(f"Reset p{meepleNumber}") 
        wait_for_move(meepleNumber)
        self.position = self.initial_position

def wait_for_button():
    while not GameState.received_button:
        time.sleep(1)
    GameState.received_button = False
    return True

def wait_for_move(meeple_number):
    correct_meeple = False
    while not correct_meeple:
        while not GameState.received_movement[0]:
                time.sleep(1)
        if GameState.received_movement[1] == meeple_number-1:
            correct_meeple=True
        GameState.received_movement[0] = False
    return True

def roll_dice(meepleNumber):
    

    print("Requesting dice roll...")
    publish(GameState.client, "dice", f"esp01/meeple{meepleNumber-1}/request")  # Send the request
    correct_meeple = False

    while not correct_meeple:
        # Wait for the response
        while not GameState.received_roll:
            wait_time = 0.1
            time.sleep(wait_time)

        if GameState.dice_roll[1] == meepleNumber-1:
            correct_meeple=True
        GameState.received_roll = False
        

    # Process the result
    print(f"Dice roll result: {GameState.dice_roll}")
    
    # Reset the flag for the next roll
    return int(GameState.dice_roll[0])
    
    #get the dice roll from the dice
    
def rock_paper_scissors():
    
    publish(GameState.client, "Play rps", "board/request/rps")
    # Wait for the response
    while not GameState.received_rps:
        wait_time = 0.1
        time.sleep(wait_time)
        
    GameState.received_rps = False
    return GameState.rps_results
    #get the rock paper scissors result from the meeples

def battle(name1, name2, position):
    print_to_lcd(f"{name1} and {name2} encountered each other at position {position}")
    result1,result2 = rock_paper_scissors()

    while result1 == result2:
        print_to_lcd("It's a tie! Battle again.")
        result1,result2 = rock_paper_scissors()
    # 1=rock 2=paper, 3=scissors
    if (result1 == 1 and result2 == 3) or (result1 == 2 and result2 == 1) or (result1 == 3 and result2 == 2):
        print_to_lcd(f"{name1} wins! {name2} goes back to the initial position.")
        time.sleep(1)

        return name1
    else:
        print_to_lcd(f"{name2} wins! {name1} goes back to the initial position.")
        time.sleep(1)

        return name2

def play_game():
    meeple1 = Meeple("Meeple1", "p1", 0)
    meeple2 = Meeple("Meeple2", "p2", 10)
    moves_counter = 0

    # Randomly decide which meeple starts first
    current_turn = meeple1 if random.choice([True, False]) else meeple2
    
    while meeple1.position < meeple2.position:
        print_to_lcd(f"{current_turn.short_name} turn")
        time.sleep(1)
        
        if current_turn == meeple1:
            publish(GameState.client, "led high", "esp01/meeple0/request")
            publish(GameState.client, "led low", "esp01/meeple1/request")
            print_to_lcd(f"{current_turn.name} is rolling the dice...")
            time.sleep(1)
            moves_counter = roll_dice(1)
            
            while(moves_counter > 0):
                print("DEBUG : Entered movement while")
                print_to_lcd(line_break(f"{meeple1.short_name}:{meeple1.position} & {meeple2.short_name}:{meeple2.position}") +
                         f"{current_turn.short_name} turn & m:{moves_counter}")
                wait_for_move(1)
                meeple1.move(1, 1)
                if(meeple1.position == meeple2.position):
                    if(battle(meeple1.short_name, meeple2.short_name, meeple2.position) == meeple1.short_name):
                        if(meeple1.position == 10):
                            return 1
                        meeple2.reset_position(2)
                        print_to_lcd(line_break(f"{meeple1.short_name}:{meeple1.position} & {meeple2.short_name}:{meeple2.position}") +
                         f"{current_turn.short_name} turn & m:{moves_counter}")
                    else:
                        meeple1.reset_position(1)
                        moves_counter = 0
                if moves_counter != 0:
                    moves_counter -= 1
                time.sleep(1)
            
            current_turn = meeple2
        else:
            publish(GameState.client, "led high", "esp01/meeple1/request")
            publish(GameState.client, "led low", "esp01/meeple0/request")
            print_to_lcd(f"{current_turn.name} is rolling the dice...")
            time.sleep(1)
            moves_counter = roll_dice(2)
            
            while(moves_counter > 0):
                print_to_lcd(line_break(f"{meeple1.short_name}:{meeple1.position} & {meeple2.short_name}:{meeple2.position}") +
                         f"{current_turn.short_name} turn & m:{moves_counter}")
                wait_for_move(2)
                meeple2.move(-1, 2)
                if(meeple1.position == meeple2.position):
                    if(battle(meeple1.short_name, meeple2.short_name, meeple2.position) == meeple2.short_name):
                        if(meeple2.position == 0):
                            return 2
                        meeple1.reset_position(1)
                        print_to_lcd(line_break(f"{meeple1.short_name}:{meeple1.position} & {meeple2.short_name}:{meeple2.position}") +
                         f"{current_turn.short_name} turn & m:{moves_counter}")
                    else:
                        meeple2.reset_position(2)
                        moves_counter = 0
                if moves_counter != 0:
                    moves_counter -= 1
                time.sleep(1)
            current_turn = meeple1
        
if __name__ == '__main__':
    print("Host : ", broker)
    print("Port : ", port)
    GameState.client = connect_mqtt()
    subscribe(GameState.client)

    GameState.client.loop_start()

    playing = True

    # This is the main function
    while playing == True:
        print_to_lcd("Press to start")
        wait_for_button()
        winner = play_game()
        print_to_lcd("p"+str(winner)+" won the game!")
        time.sleep(10)

