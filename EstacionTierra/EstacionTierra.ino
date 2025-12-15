#include <SoftwareSerial.h>
#include <stdbool.h>

SoftwareSerial mySerial(10, 11);  // RX, TX

const int led1 = 2;  // Verde: OK
const int led2 = 3;  // Rojo: error sensores
const int led3 = 4;  // Azul: error de comunicación
const int led4 = 5;  // Amarillo: modo parada
const int led5 = 6;  // Blanco: alerta de proximidad
const int buzz = 7;  // Buzzer

// --- VARIABLES NECESARIAS PARA CONTROL CON MILLIS() ---
unsigned long led1tiempo = 0;
unsigned long led2tiempo = 0;
unsigned long led3tiempo = 0;
unsigned long led4tiempo = 0;
unsigned long led5tiempo = 0;

bool standby = false;
bool led1control = false; // ahora usado como "led1 ON por temporizador"
bool led2control = false; // ahora usado como "led2 ON por temporizador"
bool led3control = false;
bool led4control = false;
bool led5control = false;
bool ledencendido = false;

// Variables que faltaban
bool standbytyh = true;
bool standbylector = true;
unsigned long buzzerTiempo = 0;
bool buzzerControl = false;

const unsigned long tiempomax = 5000;
unsigned long ultimoDato = 0;

void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);

  pinMode(led1, OUTPUT);
  pinMode(led2, OUTPUT);
  pinMode(led3, OUTPUT);
  pinMode(led4, OUTPUT);
  pinMode(led5, OUTPUT);
  pinMode(buzz, OUTPUT);

  digitalWrite(led1, LOW);
  digitalWrite(led2, LOW);
  digitalWrite(led3, LOW);
  digitalWrite(led4, LOW);
  digitalWrite(led5, LOW);
  digitalWrite(buzz, LOW);

  Serial.println("Estación intermedia lista");
  ultimoDato = millis();
}

void loop() {

  // --- Enviar comandos PC al emisor ---
  if (Serial.available()) {
    String comando = Serial.readStringUntil('\n');
    comando.trim();
    mySerial.println(comando);
    Serial.println(comando);

    if (comando.startsWith("3")){ 
      standbytyh = true; 
    }
    if (comando.startsWith("6")){ 
      standbylector = true;
    }
    
    if (comando.startsWith("2") || comando.startsWith("5")){
      standbylector = false; 
    }
  }

  // --- Recibir datos del emisor ---
  if (mySerial.available() > 0) {

    String data = mySerial.readStringUntil('\n');
    data.trim();
    Serial.println(data);
    // hacemos que en cuanto retorne la comunicacion el led3 se apague
    if (data.length() > 0) {
        ultimoDato = millis();
        digitalWrite(led3, LOW);
        noTone(buzz);
        led3control = false;
    }

    // === NUEVA LÓGICA para led1 y led2 (solo activación, sin toggles dentro) ===
    // Si llega "1:" -> encender led1 durante 1 segundo (y asegurar led2 apagado)
    if (data.startsWith("1:")) {
          
      standbytyh = false;

      // activar led1 1s
      led1control = true;
      led1tiempo = millis();
      digitalWrite(led1, HIGH);

      // asegurar que led2 esté apagado y sin temporizador
      led2control = false;
      digitalWrite(led2, LOW);
      noTone(buzz); // led1 no usa buzzer según tu lógica original
    }

    // Si llega "3" -> encender led2 durante 1 segundo (y asegurar led1 apagado)
    if (data.startsWith("3")) {
      standbytyh = false;

      // activar led2 1s
      led2control = true;
      led2tiempo = millis();
      digitalWrite(led2, HIGH);

      // asegurar que led1 esté apagado y sin temporizador
      led1control = false;
      digitalWrite(led1, LOW);

      // buzzer asociado al error T/H
      tone(buzz, 2000);
    }
    if (data.startsWith("4")){
      standbytyh = true; // lo pones aqui para asegurarnos que el satelite ha parado el dato de tyh
    }
    
    
    // --- ALERTA proximidad → LED5 + buzzer ---
    if (data.startsWith("A:")) {
      standbylector = false;

      // activar led5 1s 
      led5control = true;
      led5tiempo = millis();
      digitalWrite(led5, HIGH);

      // buzzer asociado a la alerta de proximidad 
      tone(buzz, 2000);
    }
    
    // mantener indicador general
    ledencendido = (led1control || led2control || led5control || led4control);
  }

  // --- GESTIÓN TEMPORAL: apagar led1/led2 tras 1 segundo ---
  if (led1control && (millis() - led1tiempo >= 1000UL)) {
    digitalWrite(led1, LOW);
    led1control = false;
    // noTone(buzz); // no hace falta, led1 no activó buzzer
    ledencendido = (led1control || led2control || led5control || led4control);
  }

  if (led2control && (millis() - led2tiempo >= 1000UL)) {
    digitalWrite(led2, LOW);
    led2control = false;
    noTone(buzz); // detener buzzer asociado a error sensor
    ledencendido = (led1control || led2control || led5control || led4control);
  }

  // --- GESTIÓN TEMPORAL: apagar led5 tras 1 segundo ---
  if (led5control && (millis() - led5tiempo >= 1000UL)) {
    digitalWrite(led5, LOW);
    led5control = false;
    noTone(buzz); // detener buzzer asociado a alerta de proximidad 
    ledencendido = (led1control || led2control || led5control || led4control);
  }

  // --- PARPADEO LED4 ---
  if (standbylector == true && standbytyh == true) {

    if (millis() - led4tiempo >= 1000) {

      if (led4control) digitalWrite(led4, LOW);
      else digitalWrite(led4, HIGH);

      led4tiempo = millis();
      led4control = !led4control;
    }

  } else {
    // Se sale del modo standby → apagar LED4 y reiniciar estado
    led4control = false;
    digitalWrite(led4, LOW);
  }

  // --- PÉRDIDA de comunicación ---
  if (millis() - ultimoDato >= tiempomax && ((standbylector == false || standbytyh == false))) {

    if (millis() - led3tiempo >= 1000) {

      if (led3control == true) {
        digitalWrite(led3, LOW);
        noTone(buzz);
      }
      if (led3control == false) {
        digitalWrite(led3, HIGH);
        tone(buzz, 2000);
      }
      led3tiempo = millis();
      led3control = !led3control;
    }
  }

} // cierre del loop
