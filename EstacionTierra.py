import serial
import matplotlib.pyplot as plt
import time
from tkinter import *
import threading

device = "COM6"  # Ir cambiando dependiendo del puerto
ser = serial.Serial(device, baudrate=9600, timeout=1)
datos = True

def Cerrar():
    print("Cerrando ventana...")
    ser.close()
    window.destroy()

def Mostrar():
    global graficando
    graficando = True

    def hilo_grafica():
        plt.ion()
        fig, ax = plt.subplots()
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        ax.set_xlabel("Muestras")
        ax.set_ylabel("Valor")
        ax.set_title("Lectura en tiempo real - Humedad y Temperatura")

        eje_x = []
        humedades = []
        temperaturas = []
        i = 0

        while graficando:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                trozos = line.split(':')
                if len(trozos) == 2:
                    try:
                        humedad = float(trozos[0])
                        temperatura = float(trozos[1])
                    except ValueError:
                        continue

                    eje_x.append(i)
                    humedades.append(humedad)
                    temperaturas.append(temperatura)

                    ax.cla()
                    ax.plot(eje_x, humedades, 'b-', label='Humedad (%)')
                    ax.plot(eje_x, temperaturas, 'r-', label='Temperatura (°C)')
                    ax.set_xlim(0, max(100, i))
                    ax.set_ylim(0, 100)
                    ax.set_xlabel("Muestras")
                    ax.set_ylabel("Valor")
                    ax.set_title("Lectura en tiempo real - Humedad y Temperatura")
                    ax.legend(loc='upper right')

                    plt.draw()
                    plt.pause(0.1)
                    i += 1
            time.sleep(0.1)

        print("Gráfica detenida.")
        plt.ioff()
        plt.close(fig)

    # Lo ponemos en un thread para no bloquearlo
    threading.Thread(target=hilo_grafica, daemon=True).start()

def Ocultar():
    global graficando
    print("Ocultando gráfica...")
    graficando = False  # esto hace que el bucle en hilo_grafica se detenga

def Datos():
    global datos

    def hilo_datos():
        while datos:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                print("Dato recibido:", line)
            time.sleep(0.1)

    threading.Thread(target=hilo_datos, daemon=True).start()

def Parar():
    global datos
    print("Parando datos...")
    datos = False
window = Tk()
window.geometry("600x400")
window.rowconfigure(0, weight=1)
window.rowconfigure(1, weight=1)
window.rowconfigure(2, weight=1)
window.columnconfigure(0, weight=1)
window.columnconfigure(1, weight=1)
window.columnconfigure(2, weight=1)
window.columnconfigure(3, weight=1)

tituloLabel = Label(window, text = "INTERACIÓN CON EL SATELITE", font=("Courier", 20, "italic"))
tituloLabel.grid(row=0, column=0, columnspan=5, padx=5, pady=5, sticky=N + S + E + W)

Cerrarb = Button(window, text="Cerrar", bg='red', fg="white",command=Cerrar)
Cerrarb.grid(row=1, column=3, padx=5, pady=5, sticky=N + S + E + W)

Mostrarb = Button(window, text="Mostrar grafica", bg='red', fg="white",command= Mostrar)
Mostrarb.grid(row=2, column=0, padx=5, pady=5, sticky=N + S + E + W)
Ocultarb = Button(window, text="Ocultar grafica ", bg='yellow', fg="black", command= Ocultar)
Ocultarb.grid(row=2, column=1, padx=5, pady=5, sticky=N + S + E + W)
Datosb= Button(window, text = "Datos", bg = 'blue', fg = "white", command = Datos)
Datosb.grid(row=2, column=2, padx=5, pady=5, sticky=N + S + E + W)
Pararb= Button(window, text = "Parar", bg = 'green', fg = "white", command = Parar)
Pararb.grid(row=2, column=3, padx=5, pady=5, sticky=N + S + E + W)
window.mainloop()