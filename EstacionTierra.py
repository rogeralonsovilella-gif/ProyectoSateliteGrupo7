# ===============================================================
# === LIBRERÍAS NECESARIAS ===
# ===============================================================
import serial
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import *
import numpy as np
import time
import tkinter as tk
import math
import threading


from datetime import date
from datetime import datetime
hora = str(datetime.now())
horadef = hora.split('.')
CN = open ("CAJANEGRA.txt", "w")
# ===============================================================
# === CONFIGURACIÓN SERIAL Y VARIABLES GLOBALES ===
# ===============================================================
device = "COM5"  # Puerto COM al que está conectado el Arduino
ser = serial.Serial(device, baudrate=9600, timeout=1)
datos = True
graficando = False
radarActivo = False
# Variables globales para mantener los datos de la gráfica
eje_x_global = []
humedades_global = []
temperaturas_global = []
i_global = 0
# Variables globales para el radar
angulos_radar = []
distancias_radar = []
angulo_actual_radar = 0
direccion_radar = 1

# ===============================================================
# === FUNCIONES PRINCIPALES DE CONTROL ===
# ===============================================================

def Cerrar():
    """Cierra la ventana, detiene la comunicación y libera el puerto serial."""
    print("Cerrando ventana...")
    CN.write(f"La ventana fue cerrada. FECHA/HORA -------> {horadef[0]}\n")
    CN.close()
    global graficando, datos, radarActivo
    graficando = False
    datos = False
    radarActivo = False
    if ser.is_open:
        ser.close()
    window.destroy()


def Mostrar():
    """Inicia la gráfica dinámica de temperatura y humedad."""
    CN.write(f"He mostrado la gráfica. FECHA/HORA -------> {horadef[0]}\n")
    global graficando, fig, ax, canvas, frameGrafica
    global eje_x_global, humedades_global, temperaturas_global, i_global
    if graficando:
        return
    graficando = True
    ser.write(b'4\n')  # Orden al Arduino para enviar datos

    # Crear figura dentro del frame
    fig, ax = plt.subplots(figsize=(6, 3))
    canvas = FigureCanvasTkAgg(fig, master=frameGrafica)
    canvas.get_tk_widget().pack(fill=BOTH, expand=True)

    # Configuración inicial del gráfico
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Muestras")
    ax.set_ylabel("Valor")
    ax.set_title("Lectura en tiempo real - Humedad y Temperatura")

    # Si ya hay datos, mostrarlos en la gráfica inicial
    if len(eje_x_global) > 0:
        ax.plot(eje_x_global, humedades_global, 'b-', label='Humedad (%)')
        ax.plot(eje_x_global, temperaturas_global, 'r-', label='Temperatura (°C)')
        ax.set_xlim(0, max(100, i_global))
        ax.legend(loc='upper right')
        canvas.draw()

    def actualizar():
        global i_global
        if graficando:
            # Intentar leer datos si hay disponibles
            if ser.in_waiting > 0:
                try:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    print (line)
                    if line:  # Solo procesar si la línea no está vacía
                        trozos = line.split(':')
                        if len(trozos) == 3 and trozos[0] == "1":
                            try:
                                humedad = float(trozos[1])
                                temperatura = float(trozos[2])
                                CN.write(f"Humedad registrada: {trozos[1]} Temperatura registrada: {trozos[2]}. FECHA/HORA -------> {horadef[0]}\n")
                                eje_x_global.append(i_global)
                                humedades_global.append(humedad)
                                temperaturas_global.append(temperatura)
                                ax.clear()
                                ax.plot(eje_x_global, humedades_global, 'b-', label='Humedad (%)')
                                ax.plot(eje_x_global, temperaturas_global, 'r-', label='Temperatura (°C)')
                                ax.set_xlim(0, max(100, i_global))
                                ax.set_ylim(0, 100)
                                ax.set_xlabel("Muestras")
                                ax.set_ylabel("Valor")
                                ax.set_title("Lectura en tiempo real - Humedad y Temperatura")
                                ax.legend(loc='upper right')
                                canvas.draw()
                                i_global += 1
                            except ValueError:
                                pass  # Ignorar errores de conversión
                except Exception as e:
                    print(f"Error leyendo datos: {e}")
            # Continuar el bucle independientemente de si hay datos o no
            window.after(100, actualizar)

    window.after(100, actualizar)


def Ocultar():
    """Oculta la gráfica de temperatura/humedad."""
    CN.write(f"La gráfica fue ocultada. FECHA/HORA -------> {horadef[0]}\n")
    global graficando, eje_x_global, humedades_global, temperaturas_global, i_global
    print("Ocultando gráfica...")
    graficando = False

    eje_x_global = []
    humedades_global = []
    temperaturas_global = []
    i_global = 0
    for widget in frameGrafica.winfo_children():
        widget.destroy()


def Reanudar():
    CN.write(f"Se reanudó la gráfica. FECHA/HORA -------> {horadef[0]}\n")
    print("Reanudando envío de datos...")
    
    global graficando
    # Asegurarnos de que la gráfica esté activa
    if not graficando:
        # Si la gráfica no está activa, iniciarla
        Mostrar()
    else:
        # Si ya está activa, limpiar el buffer serial para evitar procesar datos antiguos
        ser.reset_input_buffer()
        # Enviar el comando al Arduino para reanudar el envío de datos
        ser.write(b'4\n')
        print("Comando de reanudar enviado, buffer limpiado")
        # Pequeño delay para dar tiempo al Arduino de empezar a enviar datos
        # y forzar una actualización del canvas
        window.after(200, lambda: canvas.draw() if 'canvas' in globals() and canvas is not None else None)

    


def Parar():
    """Detiene temporalmente el envío de datos."""
    CN.write(f"Se paró el envío de datos. FECHA/HORA -------> {horadef[0]}\n")
    print("Parando datos...")
    ser.write(b'3\n')


def Radar():
    """Activa el modo radar (barrido con el sensor ultrasónico)."""
    CN.write(f"Se presenta el radar. FECHA/HORA -------> {horadef[0]}\n")
    global radarActivo
    print("Activando radar...")
    radarActivo = True
    ser.write(b'5\n')
    MostrarRadar()


def SeguirServo():
    """Reactiva el movimiento del servo."""
    CN.write(f"Se reactiva el servomotor. FECHA/HORA -------> {horadef[0]}\n")
    print("Parando servo...")
    ser.write(b'5\n')


def Tiempo():
    """Envía al Arduino el nuevo tiempo de muestreo (en segundos)."""
    tiempo = tiempoEntry.get().strip()
    try:
        tp = int(tiempo)
        ser.write(f"1:{tp}\n".encode())
        print(f"Tiempo enviado correctamente: {tp} s")
        CN.write(f"Se actualizó el tiempo a {tp}. FECHA/HORA -------> {horadef[0]}\n")
    except ValueError:
        print("❌ Error: lo que has introducido no es un número entero.")


def Angulo():
    """Envía al Arduino una orientación fija del servo (en grados)."""
    angulo = AnguloEntry.get().strip()
    try:
        ang = int(angulo)
        ser.write(f"2:{ang}\n".encode())
        print(f"Ángulo enviado correctamente: {ang}°")
        CN.write(f"Servomotor dirigido a {ang}º. FECHA/HORA -------> {horadef[0]}\n")
    except ValueError:
        print("❌ Error: lo que has introducido no es un número entero.")


# ===============================================================
# === FUNCIÓN DE GRÁFICA DEL RADAR ===
# ===============================================================

def MostrarRadar():
    """Muestra la gráfica polar del radar ultrasónico."""
    global figRadar, axRadar, canvasRadar, radarActivo, barrido
    global angulos_radar, distancias_radar, angulo_actual_radar, direccion_radar  
    CN.write(f"Mostré radar. FECHA/HORA -------> {horadef[0]}\n")
    for widget in frameRadar.winfo_children():
        widget.destroy()

    figRadar = plt.figure(figsize=(4, 3))
    axRadar = figRadar.add_subplot(111, polar=True)
    canvasRadar = FigureCanvasTkAgg(figRadar, master=frameRadar)
    canvasRadar.get_tk_widget().pack(fill=BOTH, expand=True)

    # Configurar la gráfica polar
    axRadar.set_theta_zero_location('E')
    axRadar.set_theta_direction(-1)
    axRadar.set_thetalim(0, np.pi)
    axRadar.set_rmax(50)
    axRadar.set_title("Radar de Ultrasonido")

    # Inicializar listas para acumular datos
    angulos_radar = []
    distancias_radar = []
    angulo_actual_radar = 0
    direccion_radar = 1

    def actualizarRadar():
        global angulos_radar, distancias_radar, angulo_actual_radar, direccion_radar 
        if radarActivo:
            # Leer datos del sensor si hay disponibles 
            if ser.in_waiting > 0:
                try:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    
                    if line == "D:Error":
                        axRadar.set_title("FALLO SENSOR", color='red')
                        canvasRadar.draw()
                        window.after(1000, lambda: axRadar.set_title("Radar de Ultrasonido"))
                    elif line.startswith("D:") or line.startswith("A:"):
                        print(line)
                        
                        # Procesar datos de distancia 
                        try:
                            distancia = float(line[2:])
                            
                            # Estimar ángulo basado en el barrido del servo 
                            # El servo barre de 0 a 180 grados, actualizamos el ángulo estimado
                            if len(angulos_radar) > 0:
                                # Si hay datos previos, estimar el siguiente ángulo basado en el patrón de barrido
                                angulo_actual_radar += direccion_radar * 5  # El servo se mueve en pasos de 5 grados
                                
                                if angulo_actual_radar >= 180:
                                    angulo_actual_radar = 180
                                    direccion_radar = -1
                                elif angulo_actual_radar <= 0:
                                    angulo_actual_radar = 0
                                    direccion_radar = 1
                            else:
                                angulo_actual_radar = 0
                            
                            # Agregar datos a las listas 
                            angulos_radar.append(angulo_actual_radar)
                            distancias_radar.append(distancia)
                            
                            # Limitar el número de puntos para evitar sobrecarga 
                            if len(angulos_radar) > 100:
                                angulos_radar.pop(0)
                                distancias_radar.pop(0)
                            
                            # Convertir ángulos a radianes y graficar 
                            if len(angulos_radar) > 0:
                                theta_rad = np.deg2rad(angulos_radar)
                                
                                # Limpiar y redibujar 
                                axRadar.clear()
                                axRadar.set_theta_zero_location('E')
                                axRadar.set_theta_direction(-1)
                                axRadar.set_thetalim(0, np.pi)
                                axRadar.set_rmax(50)
                                
                                # Graficar todos los puntos acumulados 
                                if line.startswith("A:"):
                                    # Alerta de proximidad en rojo 
                                    axRadar.scatter(theta_rad[-1], distancias_radar[-1], color='red', s=100, marker='o', label='Alerta')
                                    axRadar.set_title("Radar de Ultrasonido - ALERTA PROXIMIDAD", color='red')
                                else:
                                    # Distancia normal en verde 
                                    axRadar.scatter(theta_rad[-1], distancias_radar[-1], color='green', s=50, marker='o')
                                    axRadar.set_title("Radar de Ultrasonido", color='black')
                                
                                # Dibujar línea desde el centro hasta el último punto 
                                axRadar.plot([0, theta_rad[-1]], [0, distancias_radar[-1]], 'yellow', linewidth=2)
                                
                                # Graficar todos los puntos anteriores 
                                if len(angulos_radar) > 1:
                                    axRadar.scatter(theta_rad[:-1], distancias_radar[:-1], color='blue', s=30, marker='.', alpha=0.6)
                                
                                axRadar.legend(loc='upper right')
                                canvasRadar.draw()
                                
                                # Registrar en caja negra 
                                CN.write(f"Radar - Ángulo: {angulo_actual_radar}°, Distancia: {distancia}cm. FECHA/HORA -------> {horadef[0]}\n")
                                
                        except ValueError:
                            pass  # Ignorar errores de conversión
                except Exception as e:
                    print(f"Error leyendo datos del radar: {e}")
            
            window.after(100, actualizarRadar)

    window.after(100, actualizarRadar)


def OcultarRadar():
    """Detiene el modo radar y limpia la gráfica."""
    CN.write(f"Oculté radar. FECHA/HORA -------> {horadef[0]}\n")
    ser.write(b'6\n')

    global radarActivo, angulos_radar, distancias_radar  
    radarActivo = False
    angulos_radar = []
    distancias_radar = []
    for widget in frameRadar.winfo_children():
        widget.destroy()
def PararSensor():
    CN.write(f"Detuve sensor y servo. FECHA/HORA -------> {horadef[0]}\n")
    ser.write(b'6\n')
def Comando ():
    comando = comandoEntry.get().strip()
    CN.write(f"Comando: {comando}. FECHA/HORA -------> {horadef[0]}\n")





# ===============================================================
# === INTERFAZ TKINTER ===
# ===============================================================

window = Tk()
window.geometry("900x600")
window.title("INTERACCIÓN CON EL SATÉLITE")

# --- CONFIGURACIÓN DE LA CUADRÍCULA ---
for i in range(6):
    window.columnconfigure(i, weight=1)
for i in range(7):
    window.rowconfigure(i, weight=0)
window.rowconfigure(5, weight=1)

# --- TÍTULO ---
tituloLabel = Label(window, text="INTERACCIÓN CON EL SATÉLITE", font=("Courier", 20, "italic"))
tituloLabel.grid(row=0, column=0, columnspan=6, padx=5, pady=5, sticky=N+S+E+W)

# --- ENTRADAS DE DATOS ---
tiempoEntry = Entry(window)
tiempoEntry.grid(row=2, column=2, columnspan=2, padx=5, pady=5, sticky=N+S+E+W)
AnguloEntry = Entry(window)
AnguloEntry.grid(row=3, column=2, columnspan=2, padx=5, pady=5, sticky=N+S+E+W)
comandoEntry = Entry(window)
comandoEntry.grid(row=4, column=2, columnspan=2, padx=5, pady=5, sticky=N+S+E+W)
# --- BOTONES (MISMA DISTRIBUCIÓN) ---
Button(window, text="Cerrar", bg='red', fg="white", command=Cerrar).grid(row=6, column=3, padx=5, pady=5, sticky=N+S+E+W) #cierra la ventana
Button(window, text="Mostrar gráfica", bg='red', fg="white", command=Mostrar).grid(row=1, column=0, padx=5, pady=5, sticky=N+S+E+W) # muestra la grafica de tyh
Button(window, text="Ocultar gráfica", bg='yellow', fg="black", command=Ocultar).grid(row=1, column=1, padx=5, pady=5, sticky=N+S+E+W) # oculta la grafica de tyh
Button(window, text="Reanudar", bg='blue', fg="white", command=Reanudar).grid(row=1, column=2, padx=5, pady=5, sticky=N+S+E+W) # reanuda el envio de datos de tyh
Button(window, text="Parar", bg='green', fg="white", command=Parar).grid(row=1, column=3, padx=5, pady=5, sticky=N+S+E+W) # para el envio de datos de tyh
Button(window, text="Radar", bg='orange', fg="black", command=Radar).grid(row=2, column=0, padx=5, pady=5, sticky=N+S+E+W) # activa el radar, tanto el servo como la lectura
Button(window, text="Seguir servo", bg='pink', fg="black", command=SeguirServo).grid(row=3, column=0, padx=5, pady=5, sticky=N+S+E+W) # reanuda el servo, y los datos de lectura si no estan ya 
Button(window, text="Envia tiempo", bg='purple', fg="yellow", command=Tiempo).grid(row=2, column=3, padx=5, pady=5, sticky=N+S+E+W) # envia tiempo
Button(window, text="Envia ángulo", bg='red', fg="black", command=Angulo).grid(row=3, column=3, padx=5, pady=5, sticky=N+S+E+W) # envia angulo
Button(window, text="Ocultar radar", bg='gray', fg="white", command=OcultarRadar).grid(row=2, column=1, padx=5, pady=5, sticky=N+S+E+W) # oculta la grafica del radar
Button(window, text="Parar sensor", bg='red', fg="black", command=PararSensor).grid(row=3, column=1, padx=5, pady=5, sticky=N+S+E+W) # para el sensor 
Button(window, text="Envia comando", bg='red', fg="black", command=Comando).grid(row=4, column=3, padx=5, pady=5, sticky=N+S+E+W) # envia comando al txt

# --- FRAMES ---
frameGrafica = Frame(window, bg='white', relief=RIDGE, borderwidth=2)
frameGrafica.grid(row=5, column=0, columnspan=3, padx=10, pady=10, sticky=N+S+E+W)
frameRadar = Frame(window, bg='white', relief=RIDGE, borderwidth=2)
frameRadar.grid(row=5, column=3, columnspan=3, padx=10, pady=10, sticky=N+S+E+W)

window.mainloop()