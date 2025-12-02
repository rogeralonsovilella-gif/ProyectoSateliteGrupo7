#include <SoftwareSerial.h>

SoftwareSerial mySerial(10, 11);  // RX, TX
int i = 0;
void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);

  Serial.println("Arduino envio listo)");
}

void loop() {
  mySerial.print("¿Me recibes?");
  mySerial.print(i);
  Serial.println("Mensaje enviado: ¿Me recibes?");
  delay(2000);
  i = i+1;
}
