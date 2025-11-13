// Test unitario recibo
#include <SoftwareSerial.h>
SoftwareSerial mySerial(10, 11); // RX, TX (azul, naranja)
void setup() {
  Serial.begin(9600);
   Serial.println("Empezamos");
   mySerial.begin(9600);
}

void loop() {
  if (mySerial.available()) {
      print("Te escucho mozo");

}
