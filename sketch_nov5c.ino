//Test of prototype no1
#include <Wire.h>

#define ADS1115_ADDRESS 0x48

//=================================================================================================================================
// VARIABLE DECLARATIONS
//=================================================================================================================================

// Define the pins of the Arduino ADC where the current sensor is measured
const int SensorPin = A1, RefPin = A2;

// NEW: Temp sensor and relay
const int TempPin = A3;     // LM35 V4 analog output
const int RelayPin = 13;    // relay input(low trigger)

// NEW: Temp control
float Tmin = 20.0;
float Tmax = 25.0;

// Define the data from the current sensor
const int Rshunt = 33.3;                // Resistance of the transformer: Model 50 A: 20 ohms, Model 30 A: 33.3 ohms
double n_trafo = 1000;                  // Number of turns between primary and secondary

// Variables to calculate every millisecond
unsigned long time_now = 0;
unsigned long time_ant = 0, dif_Time = 0, act_time = 0, reading_time = 0, dif_reading_time = 0, timer1 = 0, timer2 = 0;

// Define variables to calculate the RMS of a power cycle
double quadratic_sum_v = 0.0;
double quadratic_sum_rms = 0.0;       // This variable accumulates the quadratic sum of instantaneous currents
const int sampleDuration = 20;          // Number of samples that determine how often the RMS is calculated
int quadratic_sum_counter = 0;       // Counter of how many times values have been accumulated in the quadratic sum
double freq = 50.0;                     // Define the frequency of the power cycle


// Define variables to calculate an average of the current
double accumulated_current = 0.0;       // Accumulator of RMS values for averaging
const int sampleAverage = 250;          // Number of samples that determine how often the RMS average is calculated
int accumulated_counter = 0;             // Counter of how many times RMS values have been accumulated
bool first_run = true;
double v_calib_acum = 0;
double v_calib = 0;
int i = 0;
byte writeBuf[3];

//=================================================================================================================================
// Helper functions: Function created to partition the problem in smaller parts
//=================================================================================================================================
void config_i2c() {
  Wire.begin();// begin I2C

  // ASD1115
  // set config register and start conversion
  // ANC1 and GND, 4.096v, 128s/

  writeBuf[0] = 1;    // config register is 1
  
  writeBuf[1] = 0b11010010; // 0xC2 single shot off <== ORIGINAL - single conversion/ AIN1 & GND/ 4.096V/ Continuous (0)
  
  // bit 15 flag bit for single shot
  // Bits 14-12 input selection:
  // 100 ANC0; 101 ANC1; 110 ANC2; 111 ANC3
  // Bits 11-9 Amp gain. Default to 010 here 001 P19
  // Bit 8 Operational mode of the ADS1115.
  // 0 : Continuous conversion mode
  // 1 : Power-down single-shot mode (default)

  writeBuf[2] = 0b11100101; // bits 7-0  0x85 //869 SPS 
  
  // Bits 7-5 data rate default to 100 for 128SPS
  // Bits 4-0  comparator functions see spec sheet.

  // setup ADS1115
  Wire.beginTransmission(ADS1115_ADDRESS);  // ADC
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

// NEW: LM35 V4: 10mV/°C, Output Voltage 0~1.5V -> 0~150°C
float read_temperature() {
  int raw = analogRead(TempPin);
  float voltage = (raw / 4095.0) * 3.3; // ESP32 ADC 0~3.3V
  float tempC = voltage * 100.0;
  return tempC;
}

//=================================================================================================================================
// setup
//=================================================================================================================================
void setup() {
  Serial.begin(115200);
  config_i2c();

  pinMode(RelayPin, OUTPUT);
  digitalWrite(RelayPin, HIGH);  // relay default off
  delay(1000);
  Serial.println("System initialized.");
}

//=================================================================================================================================
// loop
//=================================================================================================================================
void loop() {
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

    // NEW: Control Logic(low trigger)
    if (tempC < Tmin) {
      digitalWrite(RelayPin, LOW);   // Heater ON
    } else if (tempC > Tmax) {
      digitalWrite(RelayPin, HIGH);  // Heater OFF
    }
  }
}