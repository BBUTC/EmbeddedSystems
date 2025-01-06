#include <Arduino.h>
#include <LiquidCrystal_I2C.h>
#include <WiFi.h>
#include <string> 

LiquidCrystal_I2C lcd(0x27, 16, 2); // I2C address 0x27, 16 column and 2 rows

#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/gpio.h"
#include <Wire.h>
#include "PubSubClient.h"

int I2C_SDA = 32; 
int I2C_SCL = 33;
int buttonPin = 25;
const char* ssid = "ben partage";
const char* wifi_password = "jaifaittopzero";
xQueueHandle screenQueue;
const char* mqtt_server = "192.168.43.208";
int port = 1880;
int moveCounter = 0;

WiFiClient espClient;
PubSubClient client(espClient);

TaskHandle_t buttonHandle = NULL;
TaskHandle_t mqttHandle = NULL;


void callback(char* topic, byte* message, unsigned int length) {
  //Reads the received message and its topic to act accordingly
  Serial.print("Message arrived on topic: ");
  Serial.print(topic);
  Serial.print(". Message: ");
  String stMessage;
  String stMessage2 = "";
  
  for (int i = 0; i < length; i++) {
    Serial.print((char)message[i]);
    stMessage += (char)message[i];
  }
  Serial.println();

  //Screen display request
  if (String(topic) == "board/request/display") {
    if(length >16){
      stMessage2 = stMessage.substring(16);
    }
    Serial.print("Displaying message");
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print(stMessage);
    lcd.setCursor(0, 1);
    lcd.print(stMessage2);
  }

  //Rock Paper Scissor numbers request
  if (String(topic) == "board/request/rps") {
    String rps_result = "0,0";
    rps_result[0] = String(random(1,4))[0];
    rps_result[2] = String(random(1,4))[0];
    client.publish("board/result/rps", rps_result.c_str());
  }

}

void setup_wifi(){
  //Setup for the Wifi
  int wifi_check = 1;
  WiFi.begin(ssid, wifi_password);
  while (WiFi.status() != WL_CONNECTED) {
    vTaskDelay(100);
  }
  // xQueueSend(screenQueue, &wifi_check, 0);
  lcd.clear();
  lcd.setCursor(0, 0);      // move cursor to   (0, 0)
  lcd.print("Connected");
}

void reconnect(){
  //Connects to the mqtt broker
  while(!client.connected()){
    client.connect("ESP32");
    vTaskDelay(1000);
  }
  client.subscribe("board/request/#");
}

void button_detection(void *pvParameter){
  //Detect if the button is pressed, sends a message if it is
  bool precedentRead = false;
  while (1)
  {
    if(digitalRead(buttonPin) == 1 && !precedentRead){
      client.publish("board/result/button", "activated");
      precedentRead = true;
    }
    else if(digitalRead(buttonPin) == 0) precedentRead = false;
  }
}

void mqtt_task(void *pvParameter){
  // Reconnects if the connection is lost
  while(1){
    if(!client.connected()){
      reconnect();
    }
    //Ensures that the mqtt loop is called regularly
    client.loop();
    vTaskDelay(100);
  }
}


void setup()
{
  Serial.begin(115200);
  Serial.println("Serial Okk");

  //Sets the I2C protocol for the screen
  Wire.begin(I2C_SDA, I2C_SCL);
  pinMode(buttonPin, INPUT_PULLDOWN);
  lcd.init(); // initialize the lcd
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);      // move cursor to   (0, 0)
  lcd.print("Starting");
  setup_wifi();
  Serial.println("WiFi connected");
  lcd.clear();
  lcd.setCursor(0, 0);      // move cursor to   (0, 0)
  lcd.print("Connected");

  //Sets the mqtt broker and the callback function
  client.setServer(mqtt_server, port);
  client.setCallback(callback);
  // Publish a healtcheck status
  client.publish("board/healthcheck", "OK");

  //Launches the tasks for FreeRTOS

  //Mqtt loop and reconnect
  xTaskCreate(
    &mqtt_task,
    "mqtttask",
    2048,
    NULL,
    1,
    &mqttHandle
  );

  //Button detection
   xTaskCreate(
    &button_detection,
    "buttondetection",
    2048,
    NULL,
    1,
    &buttonHandle
  );
}

void loop() {

}