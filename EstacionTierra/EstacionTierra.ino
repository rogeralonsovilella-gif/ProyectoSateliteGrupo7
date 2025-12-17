#include <SoftwareSerial.h>
#include <stdbool.h>
#include <LiquidCrystal.h>
SoftwareSerial mySerial(10, 11);  // RX, TX

// === CHECKSUM + VALIDACIÓN ===
uint8_t CheckSum(String msg) {
  uint16_t suma = 0;
  for (int i = 0; i < msg.length(); i++) {
    suma += (uint8_t)msg[i];
  }
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

// === LEDs y buzzer ===
const int led1 = 7;  
const int led2 = 6;  
const int led3 = 5;  
const int led4 = 4;  
const int led5 = 3;  
const int buzz = 2;  
const int pinPot = A0;

unsigned long led1tiempo = 0;
unsigned long led2tiempo = 0;
unsigned long led3tiempo = 0;
unsigned long led4tiempo = 0;
unsigned long led5tiempo = 0;


bool standby = false;
bool led1control = false;
bool led2control = false;
bool led3control = false;
bool led4control = false;
bool led5control = false;
bool ledencendido = false;
bool mediaentierra = false;
bool errorChecksum = false;
bool controlvelocidad = false;
bool fanencendido = false;
bool perdida = false;


bool standbytyh = true;
bool standbylector = true;

unsigned long buzzerTiempo = 0;
bool buzzerControl = false;

unsigned long ahora = 0;
unsigned long ultimavel = 0;
const unsigned long tiempomax = 35000;
unsigned long ultimoDato = 0;
const int cantmedias = 10;
float t = 0.0;
float temp = 0.0;
int n = 0;
float tempmax = 25.0;
// RS, E, D4, D5, D6, D7
LiquidCrystal lcd(8, A1, A2, A3, A4, A5);

void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);
  lcd.begin(16,2);
  lcd.setCursor(4,0);
  lcd.print("Estacion");
  lcd.setCursor(4,1);
  lcd.print("Operativa");
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
  ahora = millis();
  // ============================================
  // PC → ESTACIÓN → SATÉLITE  (ENVÍO CON CHECKSUM)
  // ============================================
  if (Serial.available()) {

    String comando = Serial.readStringUntil('\n');
    comando.trim();

    // --- Añadir checksum ---
    String cuerpoTX = comando;
    uint8_t chkTX = CheckSum(cuerpoTX);
    mySerial.print(cuerpoTX);
    mySerial.print("|");
    mySerial.println(chkTX);

    Serial.println(comando);

    if (comando.startsWith("3")){
      standbytyh = true;
      lcd.clear();
      lcd.setCursor(3,0);
      lcd.print("Stand by:");
      lcd.setCursor(2,1);
      lcd.print("Temp. y hum.");
       
    }
    if (comando.startsWith("6")){
      standbylector = true;
      lcd.clear();
      lcd.setCursor(3,0);
      lcd.print("Stand by:");
      lcd.setCursor(5,1);
      lcd.print("Radar");
       

    
    }
    if (comando.startsWith("2") || comando.startsWith("5")) {
      standbylector = false;
      lcd.clear();
      lcd.setCursor(4,0);
      lcd.print("Activo:");
      lcd.setCursor(5,1);
      lcd.print("Radar");
       

      
    }
    if (comando.startsWith("1")) {
      int tiempomax = (comando.substring(2).toInt()*1000*15); // este x15 es pq el mayor numero de medias de temp que hemos usado es 10, generosamente le hemos añadido 5 mas por posibles fallos del lora
      lcd.clear();
      lcd.setCursor(3,0);
      lcd.print("Tiempo de");
      lcd.setCursor(5,1);
      lcd.print("envio:");
      lcd.print(comando.substring(2));
       

    }
    if (comando.startsWith("V:")) {
      controlvelocidad = true;
      
      lcd.clear();
      lcd.setCursor(3,0);
      lcd.print("Grafica");
      lcd.setCursor(4,1);
      lcd.print("vel. on");
    }
    if (comando.startsWith("S")) {
      lcd.clear();
      lcd.setCursor(1,0);
      lcd.print("Medias");
      lcd.setCursor(1,1);
      lcd.print("en Satelite");
    }
    if (comando.startsWith("T")) {
      lcd.clear();
      lcd.setCursor(1,0);
      lcd.print("Medias");
      lcd.setCursor(1,1);
      lcd.print("en Tierra");
    }
    if(comando.startsWith("G")){
          perdida = true;
          controlvelocidad = false;

        }
    if (comando.startsWith("P:")){
      controlvelocidad = false;
      lcd.clear();
      lcd.setCursor(3,0);
      lcd.print("Grafica");
      lcd.setCursor(4,1);
      lcd.print("vel. off");
       
      String cuerpo = "P";
      uint8_t chk = CheckSum(cuerpo);
      mySerial.print(cuerpo); mySerial.print("|"); mySerial.println(chk);
    }
    if(comando.startsWith("8")){
      tempmax = (comando.substring(2).toFloat());
      lcd.clear();
      lcd.setCursor(3,0);
      lcd.print("Temp. max:");
      lcd.setCursor(5,1);
      
      lcd.print(comando.substring(2));
       

    }
      
  }
  if ((ahora - ultimavel >= 1500) && controlvelocidad == true) {
    ultimavel = ahora;

    int valor = analogRead(pinPot);// 0–1023
    float val = (valor / 102.30)  ; 
    if (val>=0.5){ 
      lcd.clear();
      Serial.print("V:");
      Serial.println(val);  
      lcd.setCursor(2,0);
      lcd.print("Vel. enviada:");
      lcd.setCursor(5,1);
      lcd.print(val);
                // → PC (Python)
       
      String cuerpo = "V:" + String(val);
      uint8_t chk = CheckSum(cuerpo);
      mySerial.print(cuerpo); mySerial.print("|"); mySerial.println(chk);
    }
  }
  if (perdida == true){
    
      lcd.clear();
      lcd.setCursor(1,0);
      lcd.print("!! ALERTA !!");
      lcd.setCursor(1,1);
      lcd.print("PERDIDA TOTAL");
       
      led2control = true;
      led2tiempo = millis();
      digitalWrite(led1, LOW);
      digitalWrite(led3, LOW);
      digitalWrite(led4, LOW);
      digitalWrite(led5, LOW);

      String cuerpo = "G";
      uint8_t chk = CheckSum(cuerpo);
      mySerial.print(cuerpo); mySerial.print("|"); mySerial.println(chk);
      while (true) {
        digitalWrite(led2, HIGH);
        tone(buzz,2000);
        delay(1000);
        digitalWrite(led2, LOW);
        noTone(buzz);
        delay(1000); // Esta parte del codigo es un bucle infinito que solo se efectuara cuando el satelite entre en perdida
      }

      
    
  }
  

  // ======================================
  // SATÉLITE → ESTACIÓN (VALIDAR CHECKSUM)
  // ======================================
  if (mySerial.available() > 0) {

    String data = mySerial.readStringUntil('\n');
    data.trim();

    String contenido = "";
    if (!validarMensaje(data, contenido) && data != "") {
      errorChecksum = true;
      lcd.clear();
      lcd.setCursor(5,0);
      lcd.print("Error:");
      lcd.setCursor(5,1);
      lcd.print("Checksum");
       

      return;
    }


    data = contenido;
    Serial.println(data);

    if (data.length() > 0) {
      ultimoDato = millis();
      errorChecksum = false;   // ← apaga error inmediatamente
      digitalWrite(led3, LOW);
      noTone(buzz);
      led3control = false;
      digitalWrite(led4, LOW);

      lcd.clear();

    }


    if (data.startsWith("1:") || data.startsWith("M:")) {

      standbytyh = false;

      led1control = true;
      led1tiempo = millis();
      digitalWrite(led1, HIGH);

      led2control = false;
      digitalWrite(led2, LOW);
      noTone(buzz);
     
      lcd.setCursor(1,0);
      lcd.print("Datos recibidos:");
      lcd.setCursor(2,1);
      lcd.print("Temp. y hum.");
       
      if(data.startsWith("1:")){
        int p1 = data.indexOf(':');
        int p2 = data.indexOf(':', p1 + 1);
        float t = data.substring(p2 + 1).toFloat();
        temp += t;
        n++;

        if (n == cantmedias) {

          float avgTemp = temp / (float)cantmedias;
          if (avgTemp >= tempmax){
              fanencendido=true;
              String cuerpo = "F:";
              uint8_t chk = CheckSum(cuerpo);
              mySerial.print(cuerpo); mySerial.print("|"); mySerial.println(chk);
              lcd.clear();
              lcd.setCursor(1,0);
              lcd.print("TEMP ALTA");
              lcd.setCursor(2,1);
              lcd.print("FAN ON");
              led2control = true;
              led2tiempo = millis();
              digitalWrite(led2, HIGH);
              tone(buzz, 1500);
               
          } 
          if(avgTemp < tempmax && fanencendido == true){
              fanencendido=false;
              String cuerpo = "N:";
              uint8_t chk = CheckSum(cuerpo);
              mySerial.print(cuerpo); mySerial.print("|"); mySerial.println(chk);
              lcd.clear();
              lcd.setCursor(1,0);
              lcd.print("TEMP OK");
              lcd.setCursor(2,1);
              lcd.print("FAN OFF");
              led2control = false;
              led2tiempo = millis();
              digitalWrite(led2, LOW);
              noTone(buzz);
              
          }

      

          temp = 0.0;
          n = 0;
        }
      }
      if (data.startsWith("M:")) {
        int p1 = data.indexOf(':');
        int p2 = data.indexOf(':', p1 + 1);

        float t = data.substring(p2 + 1).toFloat();         
        if (t >=tempmax){
          fanencendido=true;
          String cuerpo = "F";
          uint8_t chk = CheckSum(cuerpo);
          mySerial.print(cuerpo); mySerial.print("|"); mySerial.println(chk);
          lcd.clear();
          lcd.setCursor(1,0);
          lcd.print("TEMP ALTA");
          lcd.setCursor(2,1);
          lcd.print("FAN ON");
          led2control = true;
          led2tiempo = millis();
          digitalWrite(led2, HIGH);
          tone(buzz, 1500);
         }
        if(t < tempmax && fanencendido == true){
          fanencendido=false;
          String cuerpo = "N:";
          uint8_t chk = CheckSum(cuerpo);
          mySerial.print(cuerpo); mySerial.print("|"); mySerial.println(chk);
          lcd.clear();
          lcd.setCursor(1,0);
          lcd.print("TEMP OK");
          lcd.setCursor(2,1);
          lcd.print("FAN OFF");
          led2control = false;
          led2tiempo = millis();
          digitalWrite(led2, LOW);
          noTone(buzz);  
          }
      }   

    }

    if (data.startsWith("3")) {

      standbytyh = false;

      led2control = true;
      led2tiempo = millis();
      digitalWrite(led2, HIGH);

      led1control = false;
      digitalWrite(led1, LOW);

      tone(buzz, 2000);
      lcd.setCursor(2,0);
      lcd.print("!! ALERTA !!");
      lcd.setCursor(2,1);
      lcd.print("SENSOR TYH");
       


    }


    if (data.startsWith("A:")) {
      standbylector = false;

      led5control = true;
      led5tiempo = millis();
      digitalWrite(led5, HIGH);
      tone(buzz, 2000);
      
      lcd.setCursor(2,0);
      lcd.print("!! ALERTA !!");
      lcd.setCursor(5,1);
      lcd.print("RADAR");
       

    }
    
    if (data.startsWith("D:")) {
      standbylector = false;
      lcd.setCursor(1,0);
      lcd.print("Datos recibidos:");
      lcd.setCursor(5,1);
      lcd.print("Radar");
       

    }

    ledencendido = (led1control || led2control || led5control || led4control);
  }

  // === Timers leds ===
  if (led1control && (millis() - led1tiempo >= 1000)) {
    digitalWrite(led1, LOW);
    led1control = false;
    ledencendido = (led2control || led5control || led4control);
  }

  if (led2control && (millis() - led2tiempo >= 1000)) {
    digitalWrite(led2, LOW);
    led2control = false;
    noTone(buzz);
    ledencendido = (led1control || led5control || led4control);
  }

  if (led5control && (millis() - led5tiempo >= 1000)) {
    digitalWrite(led5, LOW);
    led5control = false;
    noTone(buzz);
  }

  if (standbylector == true && standbytyh == true) {
    if (millis() - led4tiempo >= 1000) {
      
      if (led4control) {
      digitalWrite(led4, LOW);
      }
      else {
      digitalWrite(led4, HIGH);
      }
      led4tiempo = millis();
      led4control = !led4control;
    }
  }

  if (millis() - ultimoDato >= tiempomax &&
      ((standbylector == false || standbytyh == false))) {
    lcd.clear();
    lcd.setCursor(2,0);
    lcd.print("!! ERROR !!");
    lcd.setCursor(2,1);
    lcd.print("Comunicacion");
     
    


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
  // === Parpadeo LED3 por error de checksum ===
  if (errorChecksum && (standbylector == false || standbytyh == false)) {
    if (millis() - led3tiempo >= 1000) {
      led3control = !led3control;
      digitalWrite(led3, led3control ? HIGH : LOW);
      tone(buzz, 2000);
      led3tiempo = millis();
      lcd.clear();
      lcd.setCursor(2,0);
      lcd.print("!! ERROR !!");
      lcd.setCursor(4,1);
      lcd.print("CHECKSUM");
       

    }
  }
 
  

}
