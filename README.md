# 🛰️ Proyecto Satélite

---

## 📺 Demostraciones del Proyecto
A continuación, se presentan los videos que muestran la evolución del sistema a través de sus distintas fases de desarrollo:

* **Versión 1:** [Ver en YouTube](https://youtu.be/FvYb1tT8OKs?si=XKJNNCNUQifxHqa7)
* **Versión 2:** [Ver en YouTube](https://www.youtube.com/watch?v=Dm6qsgB5aiA)
* **Versión 3:** [Ver en YouTube](https://youtu.be/TAsdAOcMUDM)
* **Versión 4:** *(Próximamente)*

---

## 🚀 Versión 4: Nuevas Funcionalidades
En esta versión, el objetivo principal fue la integración de sistemas avanzados de control y visualización. Se han añadido cuatro características fundamentales:

### 1. Sistema de Monitoreo en Pantalla
Se ha implementado una pantalla para visualizar el estado operativo del sistema en tiempo real. Esta incluye:
* **Telemetría Avanzada:** Visualización en tiempo real de la velocidad del satélite y datos de distancia respecto a la estación de tierra.
* **Sensores Ambientales:** Monitorización constante de datos de humedad y temperatura.
* **Integridad de Datos:** Sistema de detección de errores mediante validación Checksum.
* **Alertas de Seguridad:** Notificaciones visuales sobre el estado del funcionamiento y posibles fallos.

### 2. Sistema de Refrigeración Activa
Simulación de control térmico mediante un mini ventilador DC:
* **Activación automática:** El sistema se enciende al superar el umbral de temperatura máxima definido por el usuario.
* **Desactivación:** Se detiene automáticamente cuando la temperatura regresa a niveles seguros.

### 3. Panel de Control de Órbita e Interfaz 3D
Se ha desarrollado una interfaz gráfica avanzada que incluye:
* **Simulación:** Representación 3D de la órbita y vista 2D complementaria.
* **Gráficas y Telemetría:** Indicadores de velocidad, nivel de combustible y Ground Track.
* **Control de Velocidad:** Ajustable mediante un control deslizante en la interfaz o a través de un potenciómetro físico en la estación de tierra.
* **Seguridad Orbital:** Si la velocidad excede los límites, el sistema activa alertas visuales (LED rojo) y sonoras (Buzzer). En caso de pérdida de órbita, se simula una pérdida total de comunicaciones.
* **Gestión de Combustible:** Si el combustible se agota, el satélite pierde estabilidad orbital hasta su reentrada atmosférica.

### 4. Sistema de Propulsión Simulado
Integración de un segundo ventilador que actúa como actuador de propulsión:
* **Control dinámico:** La velocidad de giro es proporcional a la velocidad orbital del satélite, simulando el empuje necesario para mantener la trayectoria.
