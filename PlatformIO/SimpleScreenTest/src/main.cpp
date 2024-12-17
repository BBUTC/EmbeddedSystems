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

  if (String(topic) == "board/request/rps") {
    String rps_result = "0,0";
    rps_result[0] = String(random(1,4))[0];
    rps_result[2] = String(random(1,4))[0];
    client.publish("board/result/rps", rps_result.c_str());
  }

}

void setup_wifi(){
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
  while(!client.connected()){
    client.connect("ESP32");
    vTaskDelay(1000);
  }
  client.subscribe("board/request/#");
}

void button_detection(void *pvParameter){
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
  while(1){
    if(!client.connected()){
      reconnect();
    }
    client.loop();
    vTaskDelay(100);
  }
}


void setup()
{
  Serial.begin(115200);
  Serial.println("Serial Okk");

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
  client.setServer(mqtt_server, port);
  client.setCallback(callback);
  client.publish("board/healthcheck", "OK");

  xTaskCreate(
    &mqtt_task,
    "mqtttask",
    2048,
    NULL,
    1,
    &mqttHandle
  );

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