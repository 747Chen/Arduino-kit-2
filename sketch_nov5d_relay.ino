// ============================================================
// Simple Relay Test Program for FireBeetle ESP32
// 控制引脚：GPIO13
// 目标：每隔 1 秒切换继电器状态
// ============================================================

#define RELAY_PIN 13  // 继电器信号线连接到 GPIO13

void setup() {
  Serial.begin(115200);
  Serial.println("Relay Test Starting...");
  
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH);  // 初始设为关闭（多数模块为低电平触发）
  delay(1000);
}

void loop() {
  Serial.println("Relay ON");
  digitalWrite(RELAY_PIN, LOW);   // 吸合（低电平触发）
  delay(1000);                    // 保持 1 秒

  Serial.println("Relay OFF");
  digitalWrite(RELAY_PIN, HIGH);  // 释放
  delay(1000);                    // 保持 1 秒
}
