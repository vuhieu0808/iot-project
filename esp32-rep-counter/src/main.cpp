#include <WiFi.h>
#include <PubSubClient.h>
#include <SPI.h>
#include <MFRC522.h>
#include <LiquidCrystal_I2C.h>
#include <ArduinoJson.h>

const char* ssid = "Wokwi-GUEST";
const char* password = "";
const char* mqttServer = "broker.hivemq.com";
const int port = 1883;
const String MACHINE_ID = "CHEST_PRESS_MACHINE";

const char* requestTopic = "gymtag/repscounter/request";
const char* responseTopic = "gymtag/repscounter/response";
const char* resultTopic = "gymtag/repscounter/result";

const unsigned long TIMEOUT_MS = 60000;

#define SS_PIN  5
#define RST_PIN 4
#define TRIG_PIN 12
#define ECHO_PIN 14
#define upBtn_PIN 32
#define downBtn_PIN 33

MFRC522 rfid(SS_PIN, RST_PIN);
LiquidCrystal_I2C lcd(0x27, 20, 4);

WiFiClient espClient;
PubSubClient client(espClient);

enum State {
  IDLE,
  WATING_SERVER,
  LIFTING,
  FINISHED
};

State currentState = State::IDLE;
String currentUID = "";
unsigned int currentWeight = 0;
unsigned int currentRepsCnt = 0;
unsigned int lastWeight = 0;
unsigned int lastRepsCnt = 0;
bool isFirstRep = true;
bool isReadyForNextRep = false;
float maxDistance = 0;
float targetDistance = 0;

unsigned long lastActivityTime = 0;
unsigned long serverRequestTime = 0;

int lastUpBtnVal = LOW;
int lastDownBtnVal = LOW;

byte arrowRight[8] = {
    B10000,
    B11000,
    B11100,
    B11110,
    B11100,
    B11000,
    B10000,
    B00000
};

void wifiConnect() {
  Serial.print("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" Connected!");
}

void mqttReconnect() {
  if (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    String clientId = "GymTag_RepsCounter_" + String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str())) {
      Serial.println(" Connected!");
      client.subscribe(requestTopic);
      client.subscribe(responseTopic);
      client.subscribe(resultTopic);
    } else {
      Serial.printf(" Failed, rc=%d\r\n", client.state());
    }
  }
}

bool publishMQTT(const char* topic, const char* payload) {
  if (!client.connected()) {
    Serial.println("MQTT disconnected before publishing. Reconnecting...");
    mqttReconnect();
  }

  if (client.connected()) {
    bool success = client.publish(topic, payload);
    if (success) {
      Serial.printf("Published to %s successfully!\r\n", topic);
    } else {
      Serial.printf("Publish to %s failed!\r\n", topic);
    }
    return success;
  }

  Serial.println("Publish failed: Cannot establish MQTT connection!");
  return false;
}

void updateLCD();

void callback(char* topic, byte* message, unsigned int length) {
  String stMessage;
  for (int i = 0; i < length; i++) {
    stMessage += (char) message[i];
  }
  
  JsonDocument doc;
  DeserializationError error = deserializeJson(doc, stMessage);

  if (error) {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.c_str());
    return;
  }
  
  if (strcmp(responseTopic, topic) == 0 && doc["machine_id"] == MACHINE_ID && doc["card_id"] == currentUID) {
    lastWeight = currentWeight = doc["weight"];
    lastRepsCnt = doc["reps"];

    lcd.clear();

    lcd.setCursor(0, 0);
    lcd.print("Your last result");

    String weightStr = String(lastWeight) + " kg";
    lcd.setCursor(0, 1);
    lcd.print("Weight:");
    lcd.setCursor(20 - weightStr.length(), 1);
    lcd.print(weightStr);

    String repsStr = String(lastRepsCnt);
    lcd.setCursor(0, 2);
    lcd.print("Reps:");
    lcd.setCursor(20 - repsStr.length(), 2);
    lcd.print(repsStr);

    for (int i = 5; i >= 1; i--) {
      String msg = "Continue in " + String(i) + "s...";

      lcd.setCursor(0, 3);
      lcd.print("                    ");

      lcd.setCursor(20 - msg.length(), 3);
      lcd.print(msg);

      delay(1000);
    }

    lastActivityTime = millis();
    updateLCD();
    currentState = State::LIFTING;
  }
}

String getCardID() {
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    uid += String(rfid.uid.uidByte[i] < 0x10 ? "0" : "");
    uid += String(rfid.uid.uidByte[i], HEX);
  }
  return uid;
}

float getDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  return duration * 0.034 / 2;
}

void updateLCD() {
  lcd.clear();
  lcd.setCursor(17, 0);
  lcd.print("UP");
  lcd.setCursor(19, 0);
  lcd.write(byte(0));
  lcd.setCursor(0, 1);
  lcd.print("Weight: " + String(currentWeight) + " KG");
  lcd.setCursor(0, 2);
  lcd.print("Reps: " + String(currentRepsCnt));
  lcd.setCursor(15, 3);
  lcd.print("DOWN");
  lcd.setCursor(19, 3);
  lcd.write(byte(0));
}

void resetToStart() {
  currentUID = "";
  currentWeight = 0;
  currentRepsCnt = 0;
  lastWeight = 0;
  lastRepsCnt = 0;
  isFirstRep = true;
  isReadyForNextRep = false;
  maxDistance = 0;
  targetDistance = 0;

  lcd.clear();
  lcd.setCursor(3, 1);
  lcd.print("Tap your card");
  lcd.setCursor(3, 2);
  lcd.print("to start now!");
  
  currentState = State::IDLE;
}

void setup() {
  Serial.begin(115200);

  wifiConnect();

  client.setServer(mqttServer, port);
  client.setCallback(callback);

  pinMode(upBtn_PIN, INPUT);
  pinMode(downBtn_PIN, INPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  
  SPI.begin();
  rfid.PCD_Init();

  lcd.init();
  lcd.backlight();
  lcd.createChar(0, arrowRight);
  lcd.setCursor(3, 1);
  lcd.print("Tap your card");
  lcd.setCursor(3, 2);
  lcd.print("to start now!");
}

void loop() {
  if (!client.connected()) {
    mqttReconnect();
  }
  client.loop();

  switch (currentState) {
    case State::IDLE: {      
      if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
        currentUID = getCardID();
        
        JsonDocument doc;
        doc["card_id"] = currentUID;
        doc["machine_id"] = MACHINE_ID;

        char payload[128];
        serializeJson(doc, payload);
        publishMQTT(requestTopic, payload);

        serverRequestTime = millis();

        lcd.clear();
        lcd.setCursor(3, 1);
        lcd.print("Getting data");
        lcd.setCursor(3, 2);
        lcd.print("Please wait...");
        currentState = State::WATING_SERVER;

        rfid.PICC_HaltA();
      }
      break;
    } 
    case State::WATING_SERVER: {
      if (millis() - serverRequestTime > TIMEOUT_MS) {
        lcd.clear();
        lcd.setCursor(5, 0);
        lcd.print("TIMED OUT");
        lcd.setCursor(2, 1);
        lcd.print("Server took too");
        lcd.setCursor(2, 2);
        lcd.print("long to respond");
        for (int i = 5; i >= 1; i--) {
          String msg = "Continue in " + String(i) + "s...";

          lcd.setCursor(0, 3);
          lcd.print("                    ");

          lcd.setCursor(20 - msg.length(), 3);
          lcd.print(msg);

          delay(1000);
        }
        
        resetToStart();

        break;
      }
      break;
    }
    case State::LIFTING: {
      if (millis() - lastActivityTime > TIMEOUT_MS) {
        lcd.clear();
        lcd.setCursor(5, 0);
        lcd.print("TIMED OUT");
        lcd.setCursor(0, 1);
        lcd.print("No activity detected");
        for (int i = 5; i >= 1; i--) {
          String msg = "Continue in " + String(i) + "s...";

          lcd.setCursor(0, 3);
          lcd.print("                    ");

          lcd.setCursor(20 - msg.length(), 3);
          lcd.print(msg);

          delay(1000);
        }
        
        resetToStart();

        break;
      }

      int newValueUp = digitalRead(upBtn_PIN);
      int newValueDown = digitalRead(downBtn_PIN);
      
      if (newValueUp != lastUpBtnVal) {
        if (newValueUp == HIGH) {
          lastActivityTime = millis();
          currentWeight++;
          updateLCD();
        } else {
        }
        lastUpBtnVal = newValueUp;
      }

      if (newValueDown != lastDownBtnVal) {
        if (newValueDown == HIGH) {
          lastActivityTime = millis();
          currentWeight--;
          updateLCD();
        } else {
        }
        lastDownBtnVal = newValueDown;
      }

      float dist = getDistance();

      if (isFirstRep) {
        if (dist > maxDistance) {
          maxDistance = dist;
        } else if (maxDistance > 40.0 && (maxDistance - dist) > 20.0) { 
          lastActivityTime = millis();
          targetDistance = maxDistance;
          currentRepsCnt = 1;
          updateLCD();
          isFirstRep = false;
          isReadyForNextRep = true;
        }
      } else {
        if (dist >= (targetDistance - 2.0) && isReadyForNextRep) {
          lastActivityTime = millis();
          currentRepsCnt++;
          isReadyForNextRep = false;
          updateLCD();
        } else if (dist < (targetDistance - 20.0)) {
          isReadyForNextRep = true;
        }
      }

      if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
        JsonDocument doc;
        doc["card_id"] = currentUID;
        doc["machine_id"] = MACHINE_ID;
        doc["weight"] = currentWeight;
        doc["reps"] = currentRepsCnt;
        
        char payload[128];
        serializeJson(doc, payload);
        publishMQTT(resultTopic, payload);

        currentState = State::FINISHED;

        rfid.PICC_HaltA();
      }

      break;
    }
    case State::FINISHED: {
      lcd.clear();
      lcd.setCursor(6, 0);
      lcd.print("FINISHED");
      for (int i = 12; i >= 1; i--) {
        if (i == 12 || i == 8 || i == 4) {
          lcd.setCursor(0, 1);
          lcd.print("                    ");
          lcd.setCursor(0, 1);
          lcd.print("Last time:");
          lcd.setCursor(0, 2);
          lcd.print("                    ");
          lcd.setCursor(0, 2);
          lcd.print("W: " + String(lastWeight) + " kg | R: " + String(lastRepsCnt));
        } else if (i == 10 || i == 6 || i == 2) {
          lcd.setCursor(0, 1);
          lcd.print("                    ");
          lcd.setCursor(0, 1);
          lcd.print("This time:");
          lcd.setCursor(0, 2);
          lcd.print("                    ");
          lcd.setCursor(0, 2);
          lcd.print("W: " + String(currentWeight) + " kg | R: " + String(currentRepsCnt));
        }
        
        String msg = "Continue in " + String(i) + "s...";
        
        lcd.setCursor(0, 3);
        lcd.print("                    ");
        
        lcd.setCursor(20 - msg.length(), 3);
        lcd.print(msg);
        
        delay(1000);
      }
      
      resetToStart();
      
      break;
    }
  }

  delay(50);
}