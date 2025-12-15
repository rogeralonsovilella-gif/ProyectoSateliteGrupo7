#include <SoftwareSerial.h>
SoftwareSerial mySerial(10, 11); // RX, TX

const int led1 = 8;  // Verde: OK
const int led2 = 7;  // Rojo: error sensores
const int led3 = 6;  // Amarillo: error de comunicación
const int led4 = 5;  // Azul: modo parada
const int buzz = 2;  // Buzzer

const unsigned long tiempomax = 5000;
unsigned long ultimoDato = 0;

void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);

  pinMode(led1, OUTPUT);
  pinMode(led2, OUTPUT);
  pinMode(led3, OUTPUT);
  pinMode(led4, OUTPUT);
  pinMode(buzz, OUTPUT);

  digitalWrite(led1, LOW);
  digitalWrite(led2, LOW);
  digitalWrite(led3, LOW);
  digitalWrite(led4, LOW);
  digitalWrite(buzz, LOW);

  Serial.println("Estación intermedia lista");
  ultimoDato = millis();
}

void loop() {
  // --- Enviar comandos del PC al emisor ---
  if (Serial.available()) {
    String comando = Serial.readStringUntil('\n');
    comando.trim();
    mySerial.println(comando);
  }

  // --- Recibir datos del emisor ---
  if (mySerial.available()) {
    String data = mySerial.readStringUntil('\n');
    data.trim();
    Serial.println(data);
    ultimoDato = millis();

    if (data.startsWith("3")) { // error sensor
      tone(buzz, 1500);
      digitalWrite(led2, HIGH);
      delay(1000);
      digitalWrite(led2, LOW);
      noTone(buzz);
    } 
    else if (data.startsWith("4")) { // parada
      digitalWrite(led4, HIGH);
      delay(1000);
      digitalWrite(led4, LOW);
    } 
    else if(data.startsWith("1:")) {
      digitalWrite(led1, HIGH);
      delay(1000);
      digitalWrite(led1, LOW);
    }
  }

  // --- Control de pérdida de comunicación ---
  if (millis() - ultimoDato >= tiempomax) {
    digitalWrite(led3, HIGH);
    tone(buzz, 2000);
    delay(1000);
    digitalWrite(led3, LOW);
    noTone(buzz);
    ultimoDato = millis();
  }
}
