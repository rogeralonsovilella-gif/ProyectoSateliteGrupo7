// Test unitario enviar
void setup() {
  #include <SoftwareSerial.h>
SoftwareSerial mySerial(10, 11); // RX, TX (en este Arduino)
void setup() {
  delay (5000)
  mySerial.begin(9600);
  // Inicialización del sensor
  dht.begin();
  Serial.println("Compravacion de comunicación: ");
  mySerial.print("Me recibes??")

}

void loop() {
 

}
