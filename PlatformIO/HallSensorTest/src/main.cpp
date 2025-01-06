#include <Arduino.h>
#include <Wire.h>
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <string>

const char* ssid = "ben partage";
const char* password = "jaifaittopzero";
const char* mqtt_server = "192.168.43.208";


int hallPin = 0;
int greenLedPin = 2;
// put function declarations here:
void myFunction();
int lastHallValue = 0;


WiFiClient espClient;
void setup_wifi() {
  //Setup for the wifi
  delay(10);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}

PubSubClient client(mqtt_server, 1880, espClient);

void reconnect() {
  //Connects back to the MQTT broker
  while (!client.connected()) {
    if (client.connect("ESP01")) {
      // Subscribe to a topic
      // Change the meeple number to 1 for the second player
      client.subscribe("esp01/meeple0/request");
    } else {
      delay(500);
    }
  }
}

void callback(char* topic, byte* payload, unsigned int length){
  //Reads the message and acts accordingly (LED on/off or dice roll)
  payload[length] = '\0';
  if(strcmp((char*) payload, "dice") == 0){
    int dice_roll = random(1,7);
    // Change the meeple number to 1 for the second player
    client.publish("esp01/meeple0/result/dice", String(dice_roll).c_str());
  }
  else if (strcmp((char*) payload, "led low") == 0)
  {
    digitalWrite(greenLedPin, LOW);
  }
  else if (strcmp((char*) payload, "led high") == 0)
  {
    digitalWrite(greenLedPin, HIGH);
  }
  
}

void setup() {
  //PIN Modes
  pinMode(hallPin, INPUT);
  pinMode(greenLedPin, OUTPUT);

  digitalWrite(greenLedPin, LOW);
  setup_wifi();

  //Sets the mqtt broker and callback function
  client.setServer(mqtt_server, 1880);
  client.setCallback(callback);
  //Connects to the MQTT Broker
  reconnect();
  //Blinks to indicate successful connection
  digitalWrite(greenLedPin, HIGH);
  delay(500);
  digitalWrite(greenLedPin, LOW);
  delay(500);
  digitalWrite(greenLedPin, HIGH);
  delay(500);
  digitalWrite(greenLedPin, LOW);
  delay(500);
  digitalWrite(greenLedPin, HIGH);
  delay(500);
  digitalWrite(greenLedPin, LOW);
  delay(500);
}



void loop() {

  myFunction();
  client.loop();

}

// put function definitions here:
void myFunction() {
  //Detects magnets with the hall sensor
  int hallValue = digitalRead(hallPin);
  if(hallValue == LOW){
    //Only sends a message if it detects a change
    if(lastHallValue == HIGH){
      // Change the meeple number to 1 for the second player
      client.publish("esp01/meeple0/result/hall", "Movement detected");
    }
  }
  lastHallValue = digitalRead(hallPin);
}