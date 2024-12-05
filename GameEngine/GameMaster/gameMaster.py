import time
from datetime import datetime
import random
import paho
from paho.mqtt import client as mqtt_client
import os

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

def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        publish(client, "The Meeple Moved", "Board/Output")

    client.subscribe("Meeple")
    client.on_message = on_message

client_id = ""
if os.getenv('MQTT_Host') == None:
    broker = "localhost"
else :
    broker = os.getenv('MQTT_Host')

port = 1883



class Meeple:
    def __init__(self, name, position):
        self.name = name
        self.position = position
        self.initial_position = position

    def move(self, steps):
        self.position += steps

    def reset_position(self):
        self.position = self.initial_position

def roll_dice():
    return random.randint(1, 6)
    #get the dice roll from the dice
    
def rock_paper_scissors():
    return random.randint(1, 3)
    #get the rock paper scissors result from the meeples

def battle(name1, name2, position):
    print(f"{name1} and {name2} encountered each other at position {position}")
    result1 = rock_paper_scissors()
    result2 = rock_paper_scissors()

    while result1 == result2:
        print("It's a tie! Battle again.")
        result1 = rock_paper_scissors()
        result2 = rock_paper_scissors()
    
    if (result1 == 1 and result2 == 3) or (result1 == 2 and result2 == 1) or (result1 == 3 and result2 == 2):
        print(f"{name1} wins! {name2} goes back to the initial position.")
        return name1
    else:
        print(f"{name2} wins! {name1} goes back to the initial position.")
        return name2

def play_game():
    meeple1 = Meeple("Meeple1", 0)
    meeple2 = Meeple("Meeple2", 10)

    # Randomly decide which meeple starts first
    current_turn = meeple1 if random.choice([True, False]) else meeple2

    while meeple1.position < meeple2.position:
        if current_turn == meeple1:
            steps = roll_dice()
            if(meeple1.position + steps >= meeple2.position): 
                if(battle(meeple1.name, meeple2.name, meeple2.position) == meeple1.name):
                    meeple2.reset_position()
                    meeple1.move(steps)
                else:
                    meeple1.reset_position()
            else:
                meeple1.move(roll_dice())
            
            current_turn = meeple2
        else:
            steps = roll_dice()
            if(meeple2.position - steps <= meeple1.position): 
                if(battle(meeple1.name, meeple2.name, meeple2.position) == meeple1.name):
                    meeple2.reset_position()
                else:
                    meeple1.reset_position()
                    meeple2.move(-steps)
            else:
                meeple2.move(-roll_dice())
            current_turn = meeple1

        print(f"{meeple1.name} is at position {meeple1.position}")
        print(f"{meeple2.name} is at position {meeple2.position}")
        
if __name__ == '__main__':
    print("Host : ", broker)
    print("Port : ", port)
    client = connect_mqtt()
    subscribe(client)

    client.loop_start()
    
    # This is the main function 
    play_game()
