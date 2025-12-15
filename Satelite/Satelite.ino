// Definiciones necesarias
#include <DHT.h>
#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);
const int led1 = 8;  // LED en el pin 8 (verde)
const int led2 = 5;  // LED en el pin 5 (Rojo)
// cambiar los numeros dependiendo de en que pin lo pongamos
#include <SoftwareSerial.h>
SoftwareSerial mySerial(10, 11); // RX, TX (en este Arduino)
void setup() {
   mySerial.begin(9600);
   // Inicialización del sensor
   dht.begin();
   mySerial.println("Empezamos temperatura y humedad");
   
}
void loop() {
   delay (3000);
   float h = dht.readHumidity();
   float t = dht.readTemperature();
   // no hace falta esto si no queremos que aparezca nada en el monitor serie
   // mySerial.println("Envío: ");
   digitalWrite(led2, LOW);
   

   if (isnan(h) || isnan(t)){
      // esto si ya que queremos avisar a la estacion tierra si hay algun error
      mySerial.print("Error ");
      digitalWrite(led2, HIGH);
   }


   else {
      
      mySerial.print(h);
      mySerial.print(':');
      mySerial.println(t);
      digitalWrite(led1, HIGH);
      delay (1500);
      digitalWrite(led1, LOW);
      
      
      // hacemos que el led se encienda cada vez que envia
      
   
   }
}
