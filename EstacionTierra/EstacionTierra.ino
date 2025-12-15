#include <SoftwareSerial.h>
SoftwareSerial mySerial(10, 11); // RX, TX (azul, naranja)

const int led1 = 8;   // LED verde
const int led2 = 5;   // LED rojo
const int led3 = 2;   // LED azul
const int buzth = 5;  // buzzer th 
const int buzcom = 2; // buzzer com

const unsigned long tiempmax = 5000; // 5 segundos
unsigned long ultimoDato = 0;        
void setup() {
  Serial.begin(9600);
  Serial.println("Empezamos");
  mySerial.begin(9600);

  pinMode(led1, OUTPUT);
  pinMode(led2, OUTPUT);
  pinMode(led3, OUTPUT);
  pinMode(buzth, OUTPUT);
  pinMode(buzcom, OUTPUT);

  ultimoDato = millis(); // Inicia el temporizador
}

void loop() {
  digitalWrite(led1, LOW);

  
  if (mySerial.available()) {
    String data = mySerial.readString();
    Serial.print(data);
    ultimoDato = millis();  

    // Si el dato es "Error "
    if (data == "Error ") {
      tone(buzth, 1500);
      delay(500);
      digitalWrite(led2, HIGH);
      delay(1000);
      digitalWrite(led2, LOW);
      noTone(buzth);
    } else {
      noTone(buzth);
      digitalWrite(led1, HIGH);
      delay(1000);
    }
  }

  
  if (millis() - ultimoDato >= tiempmax) {
    digitalWrite(led3, HIGH);
    tone(buzcom, 2000);
    delay(2000);
    digitalWrite(led3, LOW);
    noTone(buzcom);
    ultimoDato = millis();  // Reinicia el contador 
  }
}
