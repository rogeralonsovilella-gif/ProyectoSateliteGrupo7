#include <DHT.h>
#include <SoftwareSerial.h>
#include <Servo.h>

#define DHTPIN 2
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);
SoftwareSerial mySerial(10, 11);

const int led1 = 3;
const int led2 = 4;

const int trigPin = 9;
const int echoPin = 7;
const int servoPin = 8;

Servo miServo;

int radarActivo = 0;
int velocidadGiro = 25;
int posActual = 0;
int direccion = 1;
int tiempo = 3000;
unsigned long proxtiempo = 0;
unsigned long led1tiempo = 0;
unsigned long led2tiempo = 0;
unsigned long tiempolect = 0;

int led1control = 0;
int led2control = 0;
String data = "";

// Controles
int controlth = 0;
int servomotor = 0;
int leer = 0;

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
// LOOP PRINCIPAL
void loop() {

  if (mySerial.available()) {
    data = mySerial.readStringUntil('\n');
    data.trim();
  } // leer los datos que llegan

  if (data.startsWith("1:")){
    tiempo = (1000 * data.substring(2).toInt());
    controlth = 1; 
  } // cambia el tiempo de lectura

  if (data.startsWith("2:")){
    int ang = data.substring(2).toInt();
    miServo.write(ang);
    radarActivo = 1;
    servomotor = 0;
  } // mover el angulo del servo

  if ((data == "3")&&(controlth == 1)){
    mySerial.println("4");
    controlth = 0;  
  } // parar el envio de th

  if (data == "4" || controlth == 1){
    controlth=1;
    if (millis() >= proxtiempo){

      float h = dht.readHumidity();
      float t = dht.readTemperature();

      if (isnan(h) || isnan(t)) {
        mySerial.println("3");
        digitalWrite(led2, HIGH);
        led2control = 1;
        led2tiempo = millis();
        proxtiempo = millis() + tiempo;

      } else {

        mySerial.print("1:");
        mySerial.print(h);
        mySerial.print(":");
        mySerial.println(t);
        digitalWrite(led1, HIGH);
        digitalWrite(led2, LOW);
        led1control = 1;
        led1tiempo = millis();
        proxtiempo = millis() + tiempo;
      }
    }
  }

  // funciones para que los leds se enciendan cada 1 seg sin afectar el resto de codigo
  if (led1control == 1 && (millis() - led1tiempo >= 1000)){
    led1control = 0;
    digitalWrite(led1, LOW);
  }

  if (led2control == 1 && (millis() - led2tiempo >= 1000)){
    led2control = 0;
    digitalWrite(led2, LOW);
  }

  if (data == "5"){
    radarActivo = 1;
    servomotor = 1;
  }

  if (data == "6"){
    servomotor = 0;
    radarActivo = 0;
  }
  if (millis()- tiempolect >=3000){
  if (servomotor == 1){

    miServo.write(posActual);

    if (posActual % 5 == 0){
      radarActivo = 1; // Hace que solo lea cada 5 grados
    } 
    else {
      while(posActual% 5 != 0){
        posActual += 1;
      }
      radarActivo= 1;
      }

    // Actualiza la posicion del servo 
    posActual += direccion;

    if (posActual >= 180) {
      posActual = 180;
      direccion = -5;

    } else if (posActual <= 0) {
      posActual = 0;
      direccion = 5;
    }
  }

  if (radarActivo == 1){
    tiempolect = millis();
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
    // Aqui hacemos que si la distancia es menor a 10 cm ya envie la alerta desde el mismo satelite
    long distancia = duracion / 58; // Conversión aproximada a cm
    if (distancia <= 10 ){
    mySerial.print("A:");
    mySerial.println(distancia);
    }
    else if (distancia > 10) {
    mySerial.print("D:");
    mySerial.println(distancia);
    }
  }
  }
}
