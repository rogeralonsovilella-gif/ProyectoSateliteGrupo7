// ESTACIÓN DE TIERRA – RECEPTOR Y VALIDADOR DE CHECKSUM (CON AUTO-TEST)

String contenido;

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
  } else {
    return false;
  }
}

void enviarMensajeDePrueba(String texto) {
  uint8_t chk = CheckSum(texto);

  Serial.print("Texto: ");
  Serial.println(texto);

  Serial.print("Checksum calculado: ");
  Serial.println(chk);

  Serial.print("Mensaje generado (correcto): ");
  Serial.print(texto);
  Serial.print("|");
  Serial.println(chk);
  
  Serial.println();
}

void hacerPruebas() {
  Serial.println("=== PRUEBAS AUTOMÁTICAS CHECKSUM ===");

  String msg1 = "HOLA MUNDO";
  enviarMensajeDePrueba(msg1);

  // Enviar un mensaje correcto
  uint8_t chk_ok = CheckSum(msg1);
  String mensaje_ok = msg1 + "|" + String(chk_ok);

  // Mensaje corrupto
  String mensaje_mal = msg1 + "|999";

  Serial.println("Probando mensaje válido:");
  Serial.println(mensaje_ok);
  Serial.println(validarMensaje(mensaje_ok, contenido) ? "VALIDO" : "CORRUPTO");

  Serial.println("\nProbando mensaje corrupto:");
  Serial.println(mensaje_mal);
  Serial.println(validarMensaje(mensaje_mal, contenido) ? "VALIDO" : "CORRUPTO");

  Serial.println("=== FIN DE PRUEBAS ===\n");
}

void setup() {
  Serial.begin(9600);
  delay(1000);

  // Ejecutar pruebas automáticas al iniciar
  hacerPruebas();

  Serial.println("Ahora puedes enviar mensajes manualmente por el monitor serial.");
  Serial.println("Formato:  texto|checksum\n");
}

void loop() {
  if (Serial.available()) {
    String recibido = Serial.readStringUntil('\n');
    recibido.trim();

    if (validarMensaje(recibido, contenido)) {
      Serial.print("VALIDO    → ");
      Serial.println(contenido);
    } else {
      Serial.print("CORRUPTO  → ");
      Serial.println(recibido);
    }
  }
}


