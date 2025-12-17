#include <DHT.h>
#include <SoftwareSerial.h>
#include <Servo.h>
#include <stdbool.h>

#define DHTPIN 2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);
SoftwareSerial mySerial(10, 11);

Servo miServo;

// === CHECKSUM + VALIDACIÓN ===
uint8_t CheckSum(String msg) {
  uint16_t suma = 0;
  for (int i = 0; i < msg.length(); i++) suma += (uint8_t)msg[i];
  return suma % 256;
}

bool validarMensaje(const String &mensaje, String &contenido) {
  int pos = mensaje.indexOf('|');
  if (pos < 0) return false;
  String cuerpo = mensaje.substring(0, pos);
  int chkRecibido = mensaje.substring(pos + 1).toInt();
  int chkCalculado = CheckSum(cuerpo);
  if (chkRecibido == chkCalculado) {
    contenido = cuerpo;
    return true;
  }
  return false;
}

// === Pines ===
const int led1 = 3;
const int led2 = 4;
const int trigPin = 9;
const int echoPin = 7;
const int servoPin = 8;
const int fanPin = 6; // en teoria son distintos pero solo tenemos un ventilador
const int fanPinvel = 6;

int radarActivo = 0;
int velocidadGiro = 25;
int posActual = 0;
int direccion = 1;
int tiempo = 3000;

int n = 0;
float temp = 0.0;
float hum = 0.0;
float tempmax = 25.00;
float valvel = 0;
float vel = 0;
int cantmedias = 4;


unsigned long proxtiempo = 0;
unsigned long led1tiempo = 0;
unsigned long led2tiempo = 0;
unsigned long tiempolect = 0;
unsigned long tiempoventvel=0;

String data = "";

int controlth = 0;
int servomotor = 0;
int leer = 0;

bool mediaensatelite = true;
bool velactiva = false;

void setup() {
  mySerial.begin(9600);
  Serial.begin(9600);
  dht.begin();

  pinMode(led1, OUTPUT);
  pinMode(led2, OUTPUT);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(fanPin, OUTPUT);
  pinMode(fanPinvel, OUTPUT);


  miServo.attach(servoPin);
  miServo.write(posActual);
  Serial.println("Controlador iniciado.");
}

void loop() {

  // ============================================
  // RECEPCIÓN CON VALIDACIÓN CHECKSUM
  // ============================================
  if (mySerial.available()) {
    data = mySerial.readStringUntil('\n');
    data.trim();

    String contenido = "";
    if (!validarMensaje(data, contenido)) {
      return;  // ignorar comando corrupto
    }
    data = contenido;  // usar el cuerpo limpio
  }

  // ====== COMANDOS DE CONTROL ======
  if (data.startsWith("1:")) {
    tiempo = (1000 * data.substring(2).toInt());
    controlth = 1;
    // modifica el tiempo de lectura de datos de tyh
  }

  if (data.startsWith("2:")) {
    int ang = data.substring(2).toInt();
    miServo.write(ang);
    posActual = ang;
    radarActivo = 1;
    servomotor = 0;
    // Mueve el servo a un angulo especifico
  }

  if (data == "3") {
    controlth = 0;
    data = "";
    // para el envio de tyh
  }

  if (data == "4") {
    controlth = 1;
    proxtiempo = millis() + tiempo;
    data = "";
    // reanuda el envio de tyh
  }
  if (data.startsWith("8:")) {
      tempmax = (data.substring(2).toFloat());
      controlth = true; 
      // modificamos la temp max
    }
  // ============================================
  // ENVÍO PERIÓDICO T/H CON CHECKSUM
  // ============================================
  if (controlth == 1 && millis() >= proxtiempo) {

    float h = dht.readHumidity();
    float t = dht.readTemperature();

    if (isnan(h) || isnan(t)) {

      String cuerpo = "3";
      uint8_t chk = CheckSum(cuerpo);
      mySerial.print(cuerpo); mySerial.print("|"); mySerial.println(chk);

      digitalWrite(led2, HIGH);
      led2tiempo = millis();
    // hacemos que en cuanto haga un error de lectura informe a tierra
    } else {

      if (mediaensatelite == false) {

        String cuerpo = "1:" + String(h) + ":" + String(t);
        uint8_t chk = CheckSum(cuerpo);
        mySerial.print(cuerpo); mySerial.print("|"); mySerial.println(chk);

        digitalWrite(led1, HIGH);
        led1tiempo = millis();

      } else {

        temp += t;
        hum += h;
        n++;

        if (n == cantmedias) {
          // calcula las medias 
          // si la media de temp es mayor a lo deseado enciende el refrigerador
          float avgTemp = temp / (float)cantmedias;
          float avgHum = hum / (float)cantmedias;
          if (avgTemp >= tempmax){
              digitalWrite(fanPin, HIGH); 
          } if (avgTemp < tempmax){
              digitalWrite(fanPin, LOW); 
          }

          String cuerpo = "M:" + String(avgHum) + ":" + String(avgTemp);
          uint8_t chk = CheckSum(cuerpo);
          mySerial.print(cuerpo); mySerial.print("|"); mySerial.println(chk);

          temp = 0.0;
          hum = 0.0;
          n = 0;
          digitalWrite(led1, HIGH);
          led1tiempo = millis();

          
        }
        
      }
    }

    proxtiempo = millis() + tiempo;
  }

  if (data.startsWith("S")) {
    mediaensatelite = true;
    controlth = true;
    // media en satelite
  }
  if (data.startsWith("T")) {
    mediaensatelite = false;
    digitalWrite(fanPin, LOW); 
    controlth = true;
    // media en tierra, apaga el refrigerador, a partir de ahora lo maneja tierra
  }
  if (data.startsWith("G")){
    // simula que hemos perdido el satelite asi que lo apagamos todo
    digitalWrite(fanPin, LOW); 
    digitalWrite(fanPinvel, LOW); 
    digitalWrite(led2, LOW);
    digitalWrite(led1, LOW);
    while (true) {
      // generamos un bucle infinito para simular que hemos perdido el satelite
      // ahora responderá a ningun mensaje, ahora mismo no tiene ninguna utilidad
    }


  }
  
  if(data.startsWith("F")){
    digitalWrite(fanPin, HIGH); // Fan encendido, desde tierra
  }
  if(data.startsWith("N:") || controlth == false ){
    digitalWrite(fanPin, LOW); // Fan apagado, desde tierra
  }
  if (data.startsWith("V:") || velactiva == true) {
    velactiva = true;
    vel = (data.substring(2).toInt());
    valvel = (vel*25); // restamos 25 para ajustar las inexactitudes del potenciometro (no interpreta bien la vel = 0)
    digitalWrite(fanPinvel, valvel); // Fan encendido
  } 
  if (data.startsWith("P:") || data.startsWith("G")){
    velactiva = false;
    digitalWrite(fanPinvel, 0); // Fanvel  apagado, desde tierra
  }
  // controles de tiempo para los leds
  if (led1tiempo != 0 && (millis() - led1tiempo >= 1000)) {
    digitalWrite(led1, LOW);
    led1tiempo = 0;
  }

  if (led2tiempo != 0 && (millis() - led2tiempo >= 1000)) {
    digitalWrite(led2, LOW);
    led2tiempo = 0;
  }

  if (data == "5") {
    radarActivo = 1;
    servomotor = 1;
    // activamos el radar con el barrido
  }

  if (data == "6") {
    servomotor = 0;
    radarActivo = 0;
    // desactivamos el radar y el barrido

  }

  // ============================================
  // RADAR CON CHECKSUM (A: y D:)
  // ============================================
  if (radarActivo){
    if (millis() - tiempolect >= 3000) {

      if (servomotor == 1) {
      miServo.write(posActual);
      }
      int anguloLectura = posActual;
      
      digitalWrite(trigPin, LOW);
      delayMicroseconds(2);
      digitalWrite(trigPin, HIGH);
      delayMicroseconds(10);
      digitalWrite(trigPin, LOW);

      long duracion = pulseIn(echoPin, HIGH, 20000);
      long distancia = (duracion == 0) ? -1 : duracion / 58;

      if (distancia == -1) {

        String cuerpo = "D:Error";
        uint8_t chk = CheckSum(cuerpo);
        mySerial.print(cuerpo); mySerial.print("|"); mySerial.println(chk);

      } else {

        if (distancia <= 10) {// hacemos que procese aqui si hay algo muy cerca
          String cuerpo = "A:" + String(anguloLectura) + ":" + String(distancia);
          uint8_t chk = CheckSum(cuerpo); 
          mySerial.print(cuerpo); mySerial.print("|"); mySerial.println(chk);
        } else {
          String cuerpo = "D:" + String(anguloLectura) + ":" + String(distancia);
          uint8_t chk = CheckSum(cuerpo);
          mySerial.print(cuerpo); mySerial.print("|"); mySerial.println(chk);
        }
      }

      if (servomotor == 1) {
      // ajustamos el servomotor
        posActual += direccion;

        if (posActual >= 180) {
          posActual = 180;
          direccion = -1;
          
        }
        else if (posActual <= 0) {
          posActual = 0;
          direccion = 1;
        }
      }

      tiempolect = millis();
    }
  }
}
