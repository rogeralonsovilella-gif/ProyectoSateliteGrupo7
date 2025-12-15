#include <SoftwareSerial.h>
SoftwareSerial mySerial(10, 11); // RX, TX (azul, naranja)
unsigned long nextMillis = 3000;
const int led1 = 8;  // LED en el pin 13 (verde)

void setup() {
   Serial.begin(9600);
   Serial.println("Empezamos la recepción");
   mySerial.begin(9600);
}
void loop() {
   digitalWrite(led1, LOW);

   if (mySerial.available()) {
      String data = mySerial.readString();
      Serial.print(data);
      digitalWrite(led1, HIGH);
      delay (1000);

      // hacemos que independientemente del resultado se encienda un led
   }
}
