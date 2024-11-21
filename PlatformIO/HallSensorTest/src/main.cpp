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
  delay(10);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}

PubSubClient client(mqtt_server, 1880, espClient);

void reconnect() {
  while (!client.connected()) {
    if (client.connect("ESP01")) {
      // Subscribe to a topic
      client.subscribe("esp01/meeple0/dice/request");
    } else {
      delay(500);
    }
  }
  // client.subscribe("esp01/meeple0/dice/request", 0);
}

void callback(char* topic, byte* payload, unsigned int length){
  int dice_roll = random(1,7);
  client.publish("esp01/meeple0/dice/result", String(dice_roll).c_str());
}

void setup() {
  // put your setup code here, to run once:
  pinMode(hallPin, INPUT);
  pinMode(greenLedPin, OUTPUT);
  setup_wifi();
  client.setServer(mqtt_server, 1880);
  client.setCallback(callback);
  reconnect();
}



void loop() {
  // client.publish("Meeple", "Connected, starting loop");
  // put your main code here, to run repeatedly:
  // if (!client.connected()) {
  // reconnect();
  // }
  /* code */
  myFunction();
  // digitalWrite(greenLedPin, HIGH);
  // delay(1000);
  // digitalWrite(greenLedPin, LOW);
  // delay(1000);
  client.loop();

}

// put function definitions here:
void myFunction() {
  int hallValue = digitalRead(hallPin);
  if(hallValue == LOW){
    if(lastHallValue == HIGH){
      client.publish("esp01/meeple0/hall", "Movement detected");
    }
    digitalWrite(greenLedPin, HIGH);
  }
  else{
    digitalWrite(greenLedPin, LOW);
  }
  
  lastHallValue = digitalRead(hallPin);
}