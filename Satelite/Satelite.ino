#include <DHT.h>
#include <SoftwareSerial.h>
#include <Servo.h>

#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

const int led1 = 6;
const int led2 = 5;
SoftwareSerial mySerial(10, 11);
const int trigPin = 9;
const int echoPin = 7;
const int servoPin = 8;
int albaricoque = 1;
int cereza = 0;
int aguacate = 0;

Servo miServo;

int radarActivo = 0;
int velocidadGiro = 25;
int posActual = 0;
int direccion = 1;
int tiempo = 3000;
String data = "";

// --- Prototipos de funciones ---
void barridoServo();
void leerUltrasonidos();

void setup() {
  mySerial.begin(9600);
  Serial.begin(9600);
  dht.begin();

  pinMode(led1, OUTPUT);
  pinMode(led2, OUTPUT);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  miServo.attach(servoPin);
  miServo.write(posActual);
  Serial.println("Controlador iniciado.");
}

// ============================
// LOOP PRINCIPAL
// ============================
void loop() {
  
  if (mySerial.available()) {
    data = mySerial.readStringUntil('\n');
    data.trim();
  }

  // --- Cambiar tiempo ---
  if (data.startsWith("1:")) {
    tiempo = (1000*data.substring(2).toInt());
    aguacate = 1;
    delay(tiempo);
    
  }

  // --- Cambiar ángulo manual ---
  if (data.startsWith("2:")) {
    int ang = data.substring(2).toInt();
    cereza = 1;
    if ((ang >= 0 && ang <= 180) && cereza == 1) {
      miServo.write(ang);
      leerUltrasonidos();
    }
    delay(100);
  }
  if (data.startsWith("7")){
   cereza = 0;

  }

  // --- Parar envío ---
  if (data == "3") {
    mySerial.println("4");
    delay(tiempo);
    aguacate = 0;
  }
  // --- Enviar temperatura/humedad ---
  if ((data == "4" || aguacate == 1)) {
    float h = dht.readHumidity();
    if (data != "8"){
    float t = dht.readTemperature();
    }else if (data == "4" && data == "9"){
      int t = random(30,51);
    }
    if (isnan(h) || isnan(t)) {
      mySerial.println("3");
      digitalWrite(led2, HIGH);
      delay(tiempo / 2);
      digitalWrite(led2, LOW);
    } else {
      mySerial.print("1:");
      mySerial.print(h);
      mySerial.print(":");
      mySerial.println(t);
      digitalWrite(led1, HIGH);
      delay(tiempo / 2);
      digitalWrite(led1, LOW);
    }
    delay(tiempo / 2);
  }

  if (data == "8"){
    int temperatura = random(30,51);
    mySerial.println("1:" + string(temperatura));

  }

  // --- Modo radar ---
  if (data == "5" ) {
    radarActivo = 1;
    barridoServo();
    albaricoque = 0;
  }

  if (data == "6") {
   Serial.print(data);
   radarActivo = 0;
   Serial.print(radarActivo);
   delay(2000);

  }
}

// ============================
// FUNCIONES
// ============================

// Barrido del servo con medición ultrasónica
void barridoServo() {
  while (radarActivo == 1|| albaricoque == 0) {
    miServo.write(posActual);
    delay(velocidadGiro);

    // Leer distancia cada 5 grados
    if (posActual % 5 == 0) {
      leerUltrasonidos();
    }

    // Actualizar posición del servo
    posActual += direccion;

    // Evitar que se pase de los límites
    if (posActual >= 180) {
      posActual = 180;
      direccion = -1;
    } else if (posActual <= 0) {
      posActual = 0;
      direccion = 1;
    }
    if (mySerial.available()) {
    data = mySerial.readStringUntil('\n');
    data.trim();
   if (data == "6")
   albaricoque = 1;
   if (data != "5") {
   break;  }
 }
  }
}

// Lectura del sensor ultrasónico
void leerUltrasonidos() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duracion = pulseIn(echoPin, HIGH, 20000);
  if (duracion == 0) {
    mySerial.println("D:Error");
    return;
  }

  long distancia = duracion / 58; // Conversión aproximada a cm
  mySerial.print("D:");
  mySerial.println(distancia);
}
