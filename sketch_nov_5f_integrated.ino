/*
  Rui Santos
  Complete project details at https://RandomNerdTutorials.com/telegram-control-esp32-esp8266-nodemcu-outputs/
  
  Project created using Brian Lough's Universal Telegram Bot Library: https://github.com/witnessmenow/Universal-Arduino-Telegram-Bot
  Example based on the Universal Arduino Telegram Bot Library: https://github.com/witnessmenow/Universal-Arduino-Telegram-Bot/blob/master/examples/ESP8266/FlashLED/FlashLED.ino
  
  Integrated with temperature monitoring and control system
*/

#ifdef ESP32
  #include <WiFi.h>
#else
  #include <ESP8266WiFi.h>
#endif
#include <WiFiClientSecure.h>
#include <UniversalTelegramBot.h>   // Universal Telegram Bot Library written by Brian Lough: https://github.com/witnessmenow/Universal-Arduino-Telegram-Bot
#include <ArduinoJson.h>
#include <Wire.h>

#define ADS1115_ADDRESS 0x48

// Replace with your network credentials
const char* ssid = "ard-citcea";
const char* password = "ax1ohChooli0quof";

// Initialize Telegram BOT
#define BOTtoken "8545156862:AAFPlOr1shU_FAjywbT7KHxgxCVoMo55dHY"  // your Bot Token (Get from Botfather)

// Use @myidbot to find out the chat ID of an individual or a group
// Also note that you need to click "start" on a bot before it can
// message you
#define CHAT_ID "826125187"  // Replace with your Telegram Chat ID

#ifdef ESP8266
  X509List cert(TELEGRAM_CERTIFICATE_ROOT);
#endif

WiFiClientSecure client;
UniversalTelegramBot bot(BOTtoken, client);

// Checks for new messages every 1 second.
int botRequestDelay = 1000;
unsigned long lastTimeBotRan;

const int ledPin = 9;
bool ledState = LOW;

const int relayPin = 13;
bool relayState = HIGH;
bool temperatureControlActive = false;

// Temperature monitoring and control variables
const int TempPin = A3;     // LM35 V4 analog output
float Tmin = 20.0;
float Tmax = 25.0;

// Current sensor variables
const int SensorPin = A1, RefPin = A2;
const int Rshunt = 33.3;
double n_trafo = 1000;

// Timing variables
unsigned long time_now = 0;
unsigned long time_ant = 0, dif_Time = 0, act_time = 0;

// RMS calculation variables
double quadratic_sum_rms = 0.0;
const int sampleDuration = 20;
int quadratic_sum_counter = 0;
double freq = 50.0;

// Current averaging variables
double accumulated_current = 0.0;
const int sampleAverage = 250;
int accumulated_counter = 0;

byte writeBuf[3];

//=================================================================================================================================
// Helper functions for temperature monitoring
//=================================================================================================================================
void config_i2c() {
  Wire.begin();// begin I2C

  // ASD1115
  // set config register and start conversion
  writeBuf[0] = 1;    // config register is 1
  writeBuf[1] = 0b11010010; // single conversion/ AIN1 & GND/ 4.096V/ Continuous (0)
  writeBuf[2] = 0b11100101; // 869 SPS 
  
  // setup ADS1115
  Wire.beginTransmission(ADS1115_ADDRESS);
  Wire.write(writeBuf[0]);
  Wire.write(writeBuf[1]);
  Wire.write(writeBuf[2]);
  Wire.endTransmission();
  delay(500);
}

float read_voltage() {
  Wire.beginTransmission(ADS1115_ADDRESS);
  Wire.write(0x00);
  Wire.endTransmission();
  Wire.requestFrom(ADS1115_ADDRESS, 2);
  int16_t result = Wire.read() << 8 | Wire.read();
  Wire.endTransmission();
  return result * 4.096 / 32768.0;
}

// LM35 V4: 10mV/°C, Output Voltage 0~1.5V -> 0~150°C
float read_temperature() {
  int raw = analogRead(TempPin);
  float voltage = (raw / 4095.0) * 3.3; // ESP32 ADC 0~3.3V
  float tempC = voltage * 100.0;
  return tempC;
}

void temperatureControl() {
  if (!temperatureControlActive) return;
  
  act_time = micros();
  dif_Time = act_time - time_ant;

  if (dif_Time >= 1000) {
    time_ant = act_time;
    double Vinst  = read_voltage() - 1.65;
    double Iinst = Vinst * 30;
    quadratic_sum_rms += (Iinst * Iinst * (dif_Time / 1000000.0));
    quadratic_sum_counter++;
  }

  if (quadratic_sum_counter >= 20) {
    double Irms = sqrt(50 * quadratic_sum_rms);
    quadratic_sum_counter = 0;
    quadratic_sum_rms = 0;
    if (Irms <= 0.1) Irms = 0;
    accumulated_current += Irms;
    accumulated_counter++;
  }

  if (accumulated_counter >= 250) {
    double Irms_filt = accumulated_current / ((double)accumulated_counter);
    accumulated_counter = 0;
    accumulated_current = 0;

    float tempC = read_temperature();
    Serial.print("Temp: ");
    Serial.print(tempC);
    Serial.print(" °C | ");
    Serial.print("Irms: ");
    Serial.println(Irms_filt, 5);

    // Temperature control logic (low trigger)
    if (tempC < Tmin) {
      digitalWrite(relayPin, LOW);   // Heater ON
    } else if (tempC > Tmax) {
      digitalWrite(relayPin, HIGH);  // Heater OFF
    }
  }
}

// Handle what happens when you receive new messages
void handleNewMessages(int numNewMessages) {
  Serial.println("handleNewMessages");
  Serial.println(String(numNewMessages));

  for (int i=0; i<numNewMessages; i++) {
    // Chat id of the requester
    String chat_id = String(bot.messages[i].chat_id);
    if (chat_id != CHAT_ID){
      bot.sendMessage(chat_id, "Unauthorized user", "");
      continue;
    }
    
    // Print the received message
    String text = bot.messages[i].text;
    Serial.println(text);

    String from_name = bot.messages[i].from_name;

    if (text == "/start") {
      String welcome = "Welcome, " + from_name + ".\n";
      welcome += "Use the following commands to control your outputs.\n\n";
      welcome += "/relay_on to turn RELAY ON (enables temp control)\n";
      welcome += "/relay_off to turn RELAY OFF (disables temp control)\n";
      welcome += "/state to request current status \n";
      welcome += "/temp to get current temperature \n";
      bot.sendMessage(chat_id, welcome, "");
    }
    
    if (text == "/relay_off") {
      bot.sendMessage(chat_id, "Relay and temperature control disabled", "");
      temperatureControlActive = false;
      relayState = HIGH;
      digitalWrite(relayPin, relayState);
      ledState = LOW;
      digitalWrite(ledPin, ledState);
      // Reset monitoring variables
      quadratic_sum_counter = 0;
      accumulated_counter = 0;
      quadratic_sum_rms = 0;
      accumulated_current = 0;
    }
    
    if (text == "/relay_on") {
      bot.sendMessage(chat_id, "Relay and temperature control enabled", "");
      temperatureControlActive = true;
      ledState = HIGH;
      digitalWrite(ledPin, ledState);
      // Temperature control will manage relay state
      time_ant = micros(); // Initialize timing
    }
    
    if (text == "/state") {
      String status = "Status:\n";
      status += "LED: " + String(digitalRead(ledPin) ? "ON" : "OFF") + "\n";
      status += "Relay: " + String(digitalRead(relayPin) ? "OFF" : "ON") + "\n";
      status += "Temp Control: " + String(temperatureControlActive ? "ACTIVE" : "INACTIVE");
      bot.sendMessage(chat_id, status, "");
    }
    
    if (text == "/temp") {
      float tempC = read_temperature();
      String tempMsg = "Current Temperature: " + String(tempC, 2) + " °C\n";
      tempMsg += "Target Range: " + String(Tmin, 1) + " - " + String(Tmax, 1) + " °C";
      bot.sendMessage(chat_id, tempMsg, "");
    }
  }
}

void setup() {
  Serial.begin(115200);

  #ifdef ESP8266
    configTime(0, 0, "pool.ntp.org");      // get UTC time via NTP
    client.setTrustAnchors(&cert); // Add root certificate for api.telegram.org
  #endif

  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, ledState);
  
  pinMode(relayPin, OUTPUT);
  digitalWrite(relayPin, relayState);
  
  // Initialize I2C and ADS1115 for current monitoring
  config_i2c();
  
  // Connect to Wi-Fi
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  #ifdef ESP32
    client.setCACert(TELEGRAM_CERTIFICATE_ROOT); // Add root certificate for api.telegram.org
  #endif
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi..");
  }
  // Print ESP32 Local IP Address
  Serial.println(WiFi.localIP());
  Serial.println("System initialized with temperature monitoring capability.");
}

void loop() {
  // Run temperature control loop continuously when active
  temperatureControl();
  
  // Check for Telegram messages
  if (millis() > lastTimeBotRan + botRequestDelay)  {
    int numNewMessages = bot.getUpdates(bot.last_message_received + 1);

    while(numNewMessages) {
      Serial.println("got response");
      handleNewMessages(numNewMessages);
      numNewMessages = bot.getUpdates(bot.last_message_received + 1);
    }
    lastTimeBotRan = millis();
  }
}