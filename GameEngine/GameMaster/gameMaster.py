import time
from datetime import datetime
import random
import paho
from paho.mqtt import client as mqtt_client
import os

received_roll = False
dice_roll = None
rps_results = [0, 0]
received_rps = False
received_movement = False

def line_break(message):
    if message < 16:
        for i in range(len(message), 17):
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
    publish(client, message, "Board/Output") #Change the topic to the correct topic
    #print the message to the LCD screen

def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        #print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        
        global received_roll, dice_roll
        msgTopics = msg.topic.split("/")
        if msg.topic[-2:] == ["dice","result"]: # Check if the topic is the result topic
            dice_roll = int(msg.payload.decode())  # Decode the received payload
            print(f"Received `{dice_roll}` from `{msg.topic}` topic")
            received_roll = True  # Update the flag
        elif msg.topic[-2:] == ["rps","result"]:
            rops = msg.payload.decode().split(".")  # Decode the received payload
            rps_results = [int(x) for x in rops]
            received_roll = True  # Update the flag
        elif msg.topic[-1] == ["hall"]:
            received_movement = True  # Update the flag

    topics = [("esp01/meeple0/dice/result", 0),
              ("esp01/meeple1/dice/result", 0),
              ("esp01/meeple0/hall", 0),
              ("esp01/meeple1/hall", 0),
              ("board/result/rps", 0)]
    client.subscribe(topics)
    client.on_message = on_message

client_id = ""
if os.getenv('MQTT_Host') == None:
    broker = "localhost"
else :
    broker = os.getenv('MQTT_Host')

port = 1883

class Meeple:
    print_to_lcd("Meeple 1 and Meeple 2 are ready to play!") 
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
        while not received_movement:
            time.sleep(1)
        received_movement = False
        self.position = self.initial_position

def roll_dice(meepleNumber):
    
    global received_roll, dice_roll
    print("Requesting dice roll...")
    publish(client, "Roll the dice!", "roll/meeple"+ meepleNumber +"/dice/request")  # Send the request

    # Wait for the response
    while not received_roll:
        wait_time = 0.1
        time.sleep(wait_time)

    # Process the result
    print(f"Dice roll result: {dice_roll}")
    
    # Reset the flag for the next roll
    received_roll = False
    return dice_roll
    
    #get the dice roll from the dice
    
def rock_paper_scissors():
    
    # Wait for the response
    while not received_rps:
        wait_time = 0.1
        time.sleep(wait_time)
        
    received_rps = False
    #get the rock paper scissors result from the meeples

def battle(name1, name2, position):
    print_to_lcd(f"{name1} and {name2} encountered each other at position {position}")
    result1,result2 = rps_results

    while result1 == result2:
        print_to_lcd("It's a tie! Battle again.")
        rock_paper_scissors()
        result1,result2 = rps_results
    
    if (result1 == 1 and result2 == 3) or (result1 == 2 and result2 == 1) or (result1 == 3 and result2 == 2):
        print_to_lcd(f"{name1} wins! {name2} goes back to the initial position.")
        return name1
    else:
        print_to_lcd(f"{name2} wins! {name1} goes back to the initial position.")
        return name2

def play_game():
    meeple1 = Meeple("Meeple1", 0)
    meeple2 = Meeple("Meeple2", 10)
    moves_counter = 0

    # Randomly decide which meeple starts first
    current_turn = meeple1 if random.choice([True, False]) else meeple2
    print_to_lcd(f"{current_turn.name} turn")
    time.sleep(1)
    print_to_lcd(f"{meeple1.short_name} at:{meeple1.position} & {meeple2.short_name} at:{meeple2.position}")

    while meeple1.position < meeple2.position:
        print_to_lcd(f"{current_turn.short_name} turn")
        time.sleep(1)
        
        if current_turn == meeple1:
            publish(client, "led high", "esp01/meeple0/request/led")
            publish(client, "led low", "esp01/meeple1/request/led")
            print_to_lcd(f"{current_turn.name} is rolling the dice...")
            time.sleep(1)
            moves_counter = roll_dice(1)
            
            while(moves_counter > 0):
                print_to_lcd(line_break(f"{meeple1.short_name} at:{meeple1.position} & {meeple2.short_name} at:{meeple2.position}") +
                         f"{current_turn.short_name} turn & moves:{moves_counter}")
                while not received_movement:
                    time.sleep(1)
                received_movement = False
                meeple1.move(1, 1)
                if(meeple1.position == meeple2.position):
                    if(battle(meeple1.name, meeple2.name, meeple2.position) == meeple1.name):
                        meeple2.reset_position(2)
                    else:
                        meeple1.reset_position(1)
                        moves_counter = 0
                moves_counter -= 1
                time.sleep(1)
            
            current_turn = meeple2
        else:
            publish(client, "led high", "esp01/meeple1/request/led")
            publish(client, "led low", "esp01/meeple0/request/led")
            print_to_lcd(f"{current_turn.name} is rolling the dice...")
            time.sleep(1)
            steps = roll_dice(2)
            
            while(moves_counter > 0):
                print_to_lcd(line_break(f"{meeple1.short_name} at:{meeple1.position} & {meeple2.short_name} at:{meeple2.position}") +
                         f"{current_turn.short_name} turn & moves:{moves_counter}")
                while not received_movement:
                    time.sleep(1)
                received_movement = False
                meeple2.move(1, 2)
                if(meeple1.position == meeple2.position):
                    if(battle(meeple1.name, meeple2.name, meeple2.position) == meeple2.name):
                        meeple1.reset_position(1)
                    else:
                        meeple2.reset_position(2)
                        moves_counter = 0
                moves_counter -= 1
                time.sleep(1)
            current_turn = meeple1
        
if __name__ == '__main__':
    print("Host : ", broker)
    print("Port : ", port)
    client = connect_mqtt()
    subscribe(client)

    client.loop_start()

    # This is the main function

    play_game()
