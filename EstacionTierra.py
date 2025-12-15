import serial
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import *
import numpy as np
import time

# === CONFIGURACIÓN SERIAL Y VARIABLES GLOBALES ===

device = "COM7"  # Puerto COM al que está conectado el Arduino
ser = serial.Serial(device, baudrate=9600, timeout=1)
datos = True
graficando = False
radarActivo = False

# === FUNCIONES PRINCIPALES DE CONTROL ===

def Cerrar():
    """Cierra la ventana, detiene la comunicación y libera el puerto serial."""
    print("Cerrando ventana...")
    global graficando, datos, radarActivo
    graficando = False
    datos = False
    radarActivo = False
    if ser.is_open:
        ser.close()
    window.destroy()


def Mostrar():
    """Inicia la gráfica dinámica de temperatura y humedad."""
    global graficando, fig, ax, canvas, frameGrafica
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

    eje_x, humedades, temperaturas = [], [], []
    i = 0

    def actualizar():
        nonlocal i
        if graficando and ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            trozos = line.split(':')
            if len(trozos) == 3:
                try:
                    humedad = float(trozos[1])
                    temperatura = float(trozos[2])
                except ValueError:
                    window.after(100, actualizar)
                    return
                eje_x.append(i)
                humedades.append(humedad)
                temperaturas.append(temperatura)
                ax.clear()
                ax.plot(eje_x, humedades, 'b-', label='Humedad (%)')
                ax.plot(eje_x, temperaturas, 'r-', label='Temperatura (°C)')
                ax.set_xlim(0, max(100, i))
                ax.set_ylim(0, 100)
                ax.set_xlabel("Muestras")
                ax.set_ylabel("Valor")
                ax.set_title("Lectura en tiempo real - Humedad y Temperatura")
                ax.legend(loc='upper right')
                canvas.draw()
                i += 1
        if graficando:
            window.after(100, actualizar)

    window.after(100, actualizar)


def Ocultar():
    """Oculta la gráfica de temperatura/humedad."""
    global graficando
    print("Ocultando gráfica...")
    graficando = False
    for widget in frameGrafica.winfo_children():
        widget.destroy()


def Reanudar():
    """Reanuda el envío de datos desde el Arduino."""
    print("Reanudando envío de datos...")
    ser.write(b'4\n')


def Parar():
    """Detiene temporalmente el envío de datos."""
    print("Parando datos...")
    ser.write(b'3\n')


def Radar():
    """Activa el modo radar (barrido con el sensor ultrasónico)."""
    global radarActivo
    print("Activando radar...")
    radarActivo = True
    ser.write(b'5\n')
    MostrarRadar()


def PararServo():
    """Detiene el movimiento del servo."""
    print("Parando servo...")
    ser.write(b'6\n')


def Tiempo():
    """Envía al Arduino el nuevo tiempo de muestreo (en segundos)."""
    tiempo = tiempoEntry.get().strip()
    try:
        tp = int(tiempo)
        ser.write(f"1:{tp}\n".encode())
        print(f"Tiempo enviado correctamente: {tp} s")
    except ValueError:
        print("Error: lo que has introducido no es un número entero.")


def Angulo():
    """Envía al Arduino una orientación fija del servo (en grados)."""
    angulo = AnguloEntry.get().strip()
    try:
        ang = int(angulo)
        ser.write(f"2:{ang}\n".encode())
        print(f"Ángulo enviado correctamente: {ang}°")
    except ValueError:
        print("Error: lo que has introducido no es un número entero.")


# === FUNCIÓN DE GRÁFICA DEL RADAR ===

def MostrarRadar():
    """Muestra la gráfica polar del radar ultrasónico."""
    global figRadar, axRadar, canvasRadar, radarActivo

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

    linea, = axRadar.plot([], [], color='yellow', linewidth=2)
    punto, = axRadar.plot([], [], 'go')

    def actualizarRadar():
        if radarActivo and ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()

            if line == "D:Error":
                axRadar.set_title("FALLO SENSOR", color='red')
                canvasRadar.draw()
                window.after(1000, lambda: axRadar.set_title("Radar de Ultrasonido"))
            elif line.startswith("D:"):
                try:
                    distancia = float(line[2:])
                    angulo = time.time() * 50 % 180  # simula ángulo de barrido
                except ValueError:
                    window.after(100, actualizarRadar)
                    return
                theta = np.deg2rad(angulo)
                linea.set_data([theta, theta], [0, distancia])
                punto.set_data([theta], [distancia])
                canvasRadar.draw()

        if radarActivo:
            window.after(100, actualizarRadar)

    window.after(100, actualizarRadar)


def OcultarRadar():
    """Detiene el modo radar y limpia la gráfica."""
    global radarActivo
    radarActivo = False
    for widget in frameRadar.winfo_children():
        widget.destroy()
def PararSensor():
    ser.write(b'7\n')
def ValoresAleatorios():
    ser.write(b'8\n')
def ValoresReales():
    ser.write(b'9\n')

# === INTERFAZ TKINTER ===

window = Tk()
window.geometry("900x600")
window.title("INTERACCIÓN CON EL SATÉLITE")

# --- CONFIGURACIÓN DE LA CUADRÍCULA ---
for i in range(6):
    window.columnconfigure(i, weight=1)
for i in range(6):
    window.rowconfigure(i, weight=0)
window.rowconfigure(4, weight=1)

# --- TÍTULO ---
tituloLabel = Label(window, text="INTERACCIÓN CON EL SATÉLITE", font=("Courier", 20, "italic"))
tituloLabel.grid(row=0, column=0, columnspan=6, padx=5, pady=5, sticky=N+S+E+W)

# --- ENTRADAS DE DATOS ---
tiempoEntry = Entry(window)
tiempoEntry.grid(row=2, column=2, columnspan=2, padx=5, pady=5, sticky=N+S+E+W)
AnguloEntry = Entry(window)
AnguloEntry.grid(row=3, column=2, columnspan=2, padx=5, pady=5, sticky=N+S+E+W)

# --- BOTONES ---
Button(window, text="Cerrar", bg='red', fg="white", command=Cerrar).grid(row=5, column=3, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Mostrar gráfica", bg='red', fg="white", command=Mostrar).grid(row=1, column=0, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Ocultar gráfica", bg='yellow', fg="black", command=Ocultar).grid(row=1, column=1, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Reanudar", bg='blue', fg="white", command=Reanudar).grid(row=1, column=2, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Parar", bg='green', fg="white", command=Parar).grid(row=1, column=3, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Radar", bg='orange', fg="black", command=Radar).grid(row=2, column=0, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Parar servo", bg='pink', fg="black", command=PararServo).grid(row=3, column=0, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Envia tiempo", bg='purple', fg="yellow", command=Tiempo).grid(row=2, column=3, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Envia ángulo", bg='red', fg="black", command=Angulo).grid(row=3, column=3, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Ocultar radar", bg='gray', fg="white", command=OcultarRadar).grid(row=2, column=1, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Parar sensor", bg='red', fg="black", command=PararSensor).grid(row=3, column=1, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Parar sensor", bg='red', fg="black", command=ValoresAleatorios).grid(row=3, column=1, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Parar sensor", bg='red', fg="black", command=ValoresReales).grid(row=3, column=1, padx=5, pady=5, sticky=N+S+E+W)

# --- FRAMES ---
frameGrafica = Frame(window, bg='white', relief=RIDGE, borderwidth=2)
frameGrafica.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky=N+S+E+W)
frameRadar = Frame(window, bg='white', relief=RIDGE, borderwidth=2)
frameRadar.grid(row=4, column=3, columnspan=3, padx=10, pady=10, sticky=N+S+E+W)

window.mainloop()