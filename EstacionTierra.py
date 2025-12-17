# ===============================================================
# === LIBRERÍAS NECESARIAS ===
# ===============================================================
import serial
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import *
import numpy as np
import threading
from queue import Queue, Empty
from datetime import datetime
import time  # <-- FALTABA

# ===============================================================
# === CONFIGURACIÓN SERIAL Y VARIABLES GLOBALES ===
# ===============================================================
device = "COM7"
ser = serial.Serial(device, baudrate=9600, timeout=1)

p = 0

datos = True
graficando = False
radarActivo = False

tempmax_limit = 25.0

q_graph = Queue()
q_radar = Queue()
q_other = Queue()
q_vel = Queue()  # <-- NUEVO: cola para V: (velocidad)

eje_x_global = []
humedades_global = []
temperaturas_global = []
i_global = 0

angulos_radar = []
distancias_radar = []
angulo_actual_radar = 0

cantmax = 10
acumulando = []

# control velocidad pot
velocidad_pot = True
ultima_linea = ""

# valor que usa Posi() (siempre definido)
velocidad_objetivo_externa = {"val": 1.0}

# Caja negra
CN = open("CAJANEGRA.txt", "w", buffering=1)  # line-buffered

def log_event(tag: str, payload: str):
    CN.write(f"{tag} -> {payload}. FECHA/HORA -------> {datetime.now()}\n")
    CN.flush()

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

# ===============================================================
# === HILO LECTOR SERIAL: LOGUEA ALERTAS/FALLOS SIEMPRE ===
#     (ÚNICO hilo que lee del puerto serie)
# ===============================================================
def serial_reader():
    global datos, ultima_linea
    while datos:
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line:
                continue

            ultima_linea = line

            # -------------------------
            # VEL (V:...) -> cola + update global
            # -------------------------
            if line.startswith("V:"):
                try:
                    # Arduino manda float (ej "V:3.45")
                    v = float(line[2:])
                    v = clamp(v, 0.1, 10.0)
                    velocidad_objetivo_externa["val"] = v
                    q_vel.put(v)
                except ValueError:
                    pass
                continue

            # -------------------------
            # ALERTAS / FALLOS (a caja negra)
            # -------------------------
            if line.startswith("T:"):
                log_event("ALERTA TEMP MAX", line)
                q_graph.put(line)
                continue

            if line == "3":
                log_event("ERROR SENSOR TYH", "DHT sin lectura (3)")
                q_graph.put(line)
                continue

            if line == "D:Error":
                log_event("ERROR SENSOR RADAR", "D:Error")
                q_radar.put(line)
                continue

            if line.startswith("A:"):
                log_event("ALERTA RADAR PROX", line)
                q_radar.put(line)
                continue

            if line.startswith("E:CHECKSUM"):
                log_event("ERROR CHECKSUM ENLACE", line)
                continue

            if line.startswith("E:COMMS"):
                log_event("ERROR COMUNICACION", line)
                continue

            # -------------------------
            # Ruteo normal (no es alerta)
            # -------------------------
            if line.startswith("D:"):
                q_radar.put(line)
            elif line.startswith("1:") or line.startswith("M:"):
                q_graph.put(line)
            else:
                q_other.put(line)

        except Exception:
            continue

t_reader = threading.Thread(target=serial_reader, daemon=True)
t_reader.start()

# ===============================================================
# === FUNCIONES PRINCIPALES ===
# ===============================================================
def Cerrar():
    global graficando, datos, radarActivo
    log_event("INFO", "Ventana cerrada")
    graficando = False
    datos = False
    radarActivo = False
    try:
        if ser.is_open:
            ser.close()
    except Exception:
        pass
    CN.close()
    window.destroy()

def Mostrar():
    global graficando, fig, ax, canvas, frameGrafica
    global eje_x_global, humedades_global, temperaturas_global, i_global
    global acumulando, cantmax, tempmax_limit

    log_event("INFO", "Mostrar grafica TYH")

    if graficando:
        return

    graficando = True
    ser.write(b'4\n')

    fig, ax = plt.subplots(figsize=(6, 3))
    canvas = FigureCanvasTkAgg(fig, master=frameGrafica)
    canvas.get_tk_widget().pack(fill=BOTH, expand=True)

    def actualizar():
        global i_global, acumulando, cantmax, tempmax_limit

        if not graficando:
            return

        for _ in range(30):
            try:
                line = q_graph.get_nowait()
            except Empty:
                break

            if not line:
                continue

            trozos = line.split(':')

            # T:<temp> ya logueado
            if len(trozos) == 2 and trozos[0] == "T":
                continue

            if len(trozos) == 3 and trozos[0] == "M":
                try:
                    humedad = float(trozos[1])
                    temperatura = float(trozos[2])
                except ValueError:
                    continue

                eje_x_global.append(i_global)
                humedades_global.append(humedad)
                temperaturas_global.append(temperatura)
                i_global += 1

            elif len(trozos) == 3 and trozos[0] == "1":
                try:
                    humedad = float(trozos[1])
                    temperatura = float(trozos[2])
                except ValueError:
                    continue

                acumulando.append((humedad, temperatura))
                if len(acumulando) >= cantmax:
                    media_h = sum(v[0] for v in acumulando) / len(acumulando)
                    media_t = sum(v[1] for v in acumulando) / len(acumulando)

                    eje_x_global.append(i_global)
                    humedades_global.append(media_h)
                    temperaturas_global.append(media_t)
                    i_global += 1
                    acumulando = []

        # FIFO
        fifo_max = 10
        while len(humedades_global) > fifo_max:
            humedades_global.pop(0)
            temperaturas_global.pop(0)
            eje_x_global.pop(0)
           

        ax.clear()
        ax.plot(eje_x_global, humedades_global, label='Humedad (%)')
        ax.plot(eje_x_global, temperaturas_global, label='Temperatura (°C)')
        ax.axhline(tempmax_limit, color='red', linestyle='--', linewidth=2, label='Temp Max')

        if len(eje_x_global) > 1:
            ax.set_xlim(eje_x_global[0], eje_x_global[-1])

        ax.set_ylim(0, 100)
        ax.set_xlabel("Muestras")
        ax.set_ylabel("Valor")
        ax.set_title("Lectura en tiempo real - Humedad y Temperatura")
        ax.legend(loc='upper right')
        canvas.draw_idle()


        window.after(100, actualizar)

    window.after(100, actualizar)

def Ocultar():
    global graficando, eje_x_global, humedades_global, temperaturas_global, i_global
    log_event("INFO", "Ocultar grafica TYH")
    graficando = False
    eje_x_global = []
    humedades_global = []
    temperaturas_global = []
    i_global = 0
    for widget in frameGrafica.winfo_children():
        widget.destroy()

def Reanudar():
    log_event("INFO", "Reanudar TYH")
    global graficando
    if not graficando:
        Mostrar()
    else:
        ser.reset_input_buffer()
        ser.write(b'4\n')

def Parar():
    log_event("INFO", "Parar TYH")
    ser.write(b'3\n')

def Radar():
    global radarActivo
    log_event("INFO", "Mostrar radar")
    radarActivo = True
    ser.write(b'5\n')
    MostrarRadar()

def SeguirServo():
    log_event("INFO", "Seguir servo")
    ser.write(b'5\n')

def Tiempo():
    tiempo = tiempoEntry.get().strip()
    try:
        tp = int(tiempo)
        ser.write(f"1:{tp}\n".encode())
        log_event("INFO", f"Tiempo muestreo {tp}s")
    except ValueError:
        pass

def Angulo():
    angulo = AnguloEntry.get().strip()
    try:
        ang = int(angulo)
        ser.write(f"2:{ang}\n".encode())
        log_event("INFO", f"Angulo servo {ang}")
    except ValueError:
        pass

def Tempmax():
    global tempmax_limit
    txt = valormax.get().strip()
    try:
        tempdef = float(txt)
        tempmax_limit = tempdef
        ser.write(f"8:{tempdef}\n".encode())
        log_event("INFO", f"Temp max set {tempdef}C")
    except ValueError:
        pass

# ===============================================================
# === RADAR ===
# ===============================================================
def MostrarRadar():
    global figRadar, axRadar, canvasRadar, radarActivo
    global angulos_radar, distancias_radar, angulo_actual_radar

    for widget in frameRadar.winfo_children():
        widget.destroy()

    figRadar = plt.figure(figsize=(4, 3))
    axRadar = figRadar.add_subplot(111, polar=True)
    canvasRadar = FigureCanvasTkAgg(figRadar, master=frameRadar)
    canvasRadar.get_tk_widget().pack(fill=BOTH, expand=True)

    axRadar.set_theta_zero_location('E')
    axRadar.set_theta_direction(-1)
    axRadar.set_thetalim(0, np.pi)
    axRadar.set_rmax(50)
    axRadar.set_title("Radar de Ultrasonido")

    angulos_radar = []
    distancias_radar = []
    angulo_actual_radar = 0

    def actualizarRadar():
        global angulos_radar, distancias_radar, angulo_actual_radar

        if radarActivo:
            for _ in range(40):
                try:
                    line = q_radar.get_nowait()
                except Empty:
                    break

                if line == "D:Error":
                    axRadar.clear()
                    axRadar.set_theta_zero_location('E')
                    axRadar.set_theta_direction(-1)
                    axRadar.set_thetalim(0, np.pi)
                    axRadar.set_rmax(50)
                    axRadar.set_title("FALLO SENSOR RADAR")
                    canvasRadar.draw()
                    continue

                if line.startswith("D:") or line.startswith("A:"):
                    try:
                        _, angulo_str, distancia_str = line.split(":")
                        angulo_actual_radar = float(angulo_str)
                        distancia = float(distancia_str)
                    except ValueError:
                        continue

                    angulos_radar.append(angulo_actual_radar)
                    distancias_radar.append(distancia)

                    if len(angulos_radar) > 100:
                        angulos_radar.pop(0)
                        distancias_radar.pop(0)

                    theta_rad = np.deg2rad(angulos_radar)

                    axRadar.clear()
                    axRadar.set_theta_zero_location('E')
                    axRadar.set_theta_direction(-1)
                    axRadar.set_thetalim(0, np.pi)
                    axRadar.set_rmax(50)

                    if line.startswith("A:"):
                        axRadar.scatter(theta_rad[-1], distancias_radar[-1], color='red', s=100, marker='o', label='Alerta')
                        axRadar.set_title("Radar - ALERTA PROXIMIDAD")
                    else:
                        axRadar.scatter(theta_rad[-1], distancias_radar[-1], color='green', s=50, marker='o')
                        axRadar.set_title("Radar de Ultrasonido")

                    axRadar.plot([0, theta_rad[-1]], [0, distancias_radar[-1]], 'yellow', linewidth=2)

                    if len(angulos_radar) > 1:
                        axRadar.scatter(theta_rad[:-1], distancias_radar[:-1], color='blue', s=30, marker='.', alpha=0.6)

                    canvasRadar.draw()

            window.after(100, actualizarRadar)

    window.after(100, actualizarRadar)

def OcultarRadar():
    global radarActivo, angulos_radar, distancias_radar
    log_event("INFO", "Ocultar radar")
    ser.write(b'6\n')
    radarActivo = False
    angulos_radar = []
    distancias_radar = []
    for widget in frameRadar.winfo_children():
        widget.destroy()

def PararSensor():
    log_event("INFO", "Detuve sensor y servo")
    ser.write(b'6\n')

# ===============================================================
# === POSICIÓN (SOLO ARREGLOS PARA QUE FUNCIONE) ===
# ===============================================================
def Posi():
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    from matplotlib.widgets import Slider
    from mpl_toolkits.mplot3d import Axes3D
    import matplotlib.image as mpimg
    from matplotlib.patches import Rectangle, Circle, Wedge

    # Activar envío de velocidad desde Arduino Tierra
    ser.write(b'V:\n')

    R_TIERRA = 6371.0
    ALTURA_ORBITA = 500.0
    R_ORBITA_BASE = R_TIERRA + ALTURA_ORBITA
    INCLINACION = np.deg2rad(55)

    T_ORBITA_BASE = 90 * 60
    OMEGA_ORBITA_BASE = 2 * np.pi / T_ORBITA_BASE

    T_TIERRA = 23.9345 * 3600
    OMEGA_TIERRA = 2 * np.pi / T_TIERRA

    FUEL_MAX = 2000.0
    CONSUMO_BASE = 0.02
    VEL_CAIDA = 0.4

    def angulo_cobertura(r):
        return np.degrees(np.arccos(R_TIERRA / r))

    def set_equal_aspect_3d(ax, radius):
        ax.set_box_aspect([1, 1, 1])
        ax.set_xlim(-radius, radius)
        ax.set_ylim(-radius, radius)
        ax.set_zlim(-radius, radius)

    def crear_simulacion_completa():
        fig = plt.figure(figsize=(14, 7))

        # Cuando cierres la ventana de Posi, parar la velocidad
        def _on_close(evt):
            try:
                ser.write(b'P:\n')
            except Exception:
                pass

        fig.canvas.mpl_connect("close_event", _on_close)

        gs = fig.add_gridspec(2, 3, width_ratios=[1.2, 1.2, 0.5], height_ratios=[1, 1])

        ax2d = fig.add_subplot(gs[0, 0])
        ax3d = fig.add_subplot(gs[0, 1], projection='3d')
        axmap = fig.add_subplot(gs[1, 0:2])
        fuel_ax = fig.add_subplot(gs[1, 2])
        speed_ax = fig.add_subplot(gs[0, 2])

        ang = np.linspace(0, 2 * np.pi, 400)
        x_tierra_2d = R_TIERRA * np.cos(ang)
        y_tierra_2d = R_TIERRA * np.sin(ang)
        ax2d.fill(x_tierra_2d, y_tierra_2d, alpha=0.3)

        x_orb_2d = R_ORBITA_BASE * np.cos(ang)
        y_orb_2d = R_ORBITA_BASE * np.sin(ang)
        orb2d_line, = ax2d.plot(x_orb_2d, y_orb_2d, "--", color="green", alpha=0.5)

        sat2d_trail, = ax2d.plot([], [], color="green", lw=1.5)
        sat2d_point, = ax2d.plot([], [], "o", color="red", ms=6)
        trail2d_x, trail2d_y = [], []

        max_r = R_ORBITA_BASE * 3
        ax2d.set_xlim(-max_r, max_r)
        ax2d.set_ylim(-max_r, max_r)
        ax2d.set_aspect("equal", "box")
        ax2d.set_xlabel("x (km)")
        ax2d.set_ylabel("y (km)")
        ax2d.set_title("Órbita vista desde arriba")

        u = np.linspace(0, 2 * np.pi, 60)
        v = np.linspace(0, np.pi, 30)
        u, v = np.meshgrid(u, v)
        x_tierra_3d = R_TIERRA * np.cos(u) * np.sin(v)
        y_tierra_3d = R_TIERRA * np.sin(u) * np.sin(v)
        z_tierra_3d = R_TIERRA * np.cos(v)
        ax3d.plot_surface(x_tierra_3d, y_tierra_3d, z_tierra_3d, alpha=0.5, linewidth=0)

        sat3d_point, = ax3d.plot([R_ORBITA_BASE], [0], [0], "o", ms=6, color="red")
        set_equal_aspect_3d(ax3d, R_ORBITA_BASE * 3)
        ax3d.set_xlabel("x (km)")
        ax3d.set_ylabel("y (km)")
        ax3d.set_zlabel("z (km)")
        ax3d.set_title("Órbita 3D")

        img = mpimg.imread("mapa.png")
        axmap.imshow(img, extent=[-180, 180, -90, 90], aspect="auto")

        axmap.set_xlim(-180, 180)
        axmap.set_ylim(-90, 90)
        axmap.set_xlabel("Longitud (°)")
        axmap.set_ylabel("Latitud (°)")
        axmap.set_title("Traza sobre la Tierra")

        axmap.set_xticks(np.arange(-180, 181, 30))
        axmap.set_yticks(np.arange(-90, 91, 15))
        axmap.grid(True, linestyle="--", lw=0.5)

        track_line, = axmap.plot([], [], color="green", lw=1.5)
        sat_point, = axmap.plot([], [], "o", color="red", ms=6)
        lons, lats = [], []

        night_patch = Rectangle((-90, -90), 180, 180, color="black", alpha=0.25)
        axmap.add_patch(night_patch)

        footprint = Circle((0, 0), 10, edgecolor="cyan", facecolor="cyan", alpha=0.25)
        axmap.add_patch(footprint)

        warning_text = axmap.text(
            0.02, 0.02, "", transform=axmap.transAxes,
            ha="left", va="bottom", fontsize=10, color="orange",
            bbox=dict(boxstyle="round", facecolor="black", alpha=0.4)
        )

        fuel_ax.set_xlim(0, 1)
        fuel_ax.set_ylim(0, 1)
        fuel_ax.set_xticks([])
        fuel_ax.set_yticks([])
        fuel_ax.set_title("Fuel")

        fuel_bar = fuel_ax.bar(0.5, 1.0, width=0.8)[0]
        fuel_text = fuel_ax.text(0.5, -0.05, "100%", ha="center", va="top")

        speed_ax.set_xlim(-1.2, 1.2)
        speed_ax.set_ylim(-0.2, 1.2)
        speed_ax.set_xticks([])
        speed_ax.set_yticks([])
        for spine in speed_ax.spines.values():
            spine.set_visible(False)
        speed_ax.set_title("Velocidad")

        gauge_bg = Wedge((0, 0), 1.0, -90, 90, facecolor="lightgray", edgecolor="black")
        speed_ax.add_patch(gauge_bg)

        speed_needle, = speed_ax.plot([0, 0], [0, 0.9], lw=2, color="red")

        speed_value_text = speed_ax.text(
            0.5, 0.65, "1.00x",
            ha="center", va="center",
            transform=speed_ax.transAxes, fontsize=12
        )

        speed_label_text = speed_ax.text(
            0.5, 0.1, "",
            ha="center", va="center",
            transform=speed_ax.transAxes, fontsize=9, color="orange"
        )

        slider_ax = fig.add_axes([0.2, 0.02, 0.6, 0.03])
        slider_vel = Slider(
            ax=slider_ax,
            label="Velocidad objetivo",
            valmin=0.1,
            valmax=10.0,
            valinit=velocidad_objetivo_externa["val"],  # arranca con la última leída
            valstep=0.1,
        )

        dt = 20.0

        velocidad = {"actual": 1.0, "objetivo": 1.0}
        estado = {
            "t_rot": 0.0,
            "nu": 0.0,
            "alt_factor": 1.0,
            "modo": "normal",
            "reentry_vel": 1.0,
            "comms_ok": True,
            "speed_display": 1.0
        }
        fuel = {"nivel": FUEL_MAX}

        def actualizar_velocidad_objetivo(val):
            velocidad["objetivo"] = val

        slider_vel.on_changed(actualizar_velocidad_objetivo)

        def poner_destruido():
            sat2d_trail.set_color("gray")
            sat2d_point.set_color("gray")
            orb2d_line.set_color("gray")
            track_line.set_color("gray")
            sat_point.set_color("gray")
            sat3d_point.set_color("gray")

        def actualizar_aguja_velocidad(speed_factor):
            s = max(0.1, min(speed_factor, 10.0))
            angle_deg = -90 + (s - 0.1) / (10.0 - 0.1) * 180
            angle = np.deg2rad(angle_deg)
            x_end = np.cos(angle) * 0.9
            y_end = np.sin(angle) * 0.9
            speed_needle.set_data([0, x_end], [0, y_end])

        def init():
            trail2d_x.clear()
            trail2d_y.clear()
            lons.clear()
            lats.clear()

            sat2d_trail.set_data([], [])
            sat2d_point.set_data([], [])
            track_line.set_data([], [])
            sat_point.set_data([], [])

            orb2d_line.set_color("green")
            sat2d_trail.set_color("green")
            sat2d_point.set_color("red")
            sat3d_point.set_color("red")
            track_line.set_color("green")
            sat_point.set_color("red")

            fuel["nivel"] = FUEL_MAX
            fuel_bar.set_height(1.0)
            fuel_text.set_text("100%")

            velocidad["actual"] = velocidad["objetivo"] = slider_vel.val
            estado["t_rot"] = 0.0
            estado["nu"] = 0.0
            estado["alt_factor"] = 1.0
            estado["modo"] = "normal"
            estado["reentry_vel"] = velocidad["actual"]
            estado["comms_ok"] = True
            estado["speed_display"] = velocidad["actual"]

            warning_text.set_text("")
            speed_value_text.set_text(f"{estado['speed_display']:.2f}x")
            speed_label_text.set_text("")
            actualizar_aguja_velocidad(estado["speed_display"])

            return (sat2d_trail, sat2d_point, sat3d_point,
                    track_line, sat_point,
                    fuel_bar, fuel_text, warning_text,
                    night_patch, footprint,
                    speed_needle, speed_value_text, speed_label_text)

        def update(frame):
            # velocidad objetivo desde el potenciómetro (cola/último valor)
            velocidad["objetivo"] = velocidad_objetivo_externa["val"]

            modo = estado["modo"]

            if modo == "normal":
                alpha_vel = 0.05
                velocidad["actual"] += (velocidad["objetivo"] - velocidad["actual"]) * alpha_vel

                k_alt = 0.3
                target_alt_factor = 1 + k_alt * (velocidad["actual"] - 1)
                target_alt_factor = max(0.5, min(target_alt_factor, 3.0))

                alpha_alt = 0.05
                estado["alt_factor"] += (target_alt_factor - estado["alt_factor"]) * alpha_alt

                estado["t_rot"] += dt * velocidad["actual"]
                r_temp = R_ORBITA_BASE * estado["alt_factor"]
                omega_eff = OMEGA_ORBITA_BASE * (R_ORBITA_BASE / r_temp) ** 1.5
                estado["nu"] += omega_eff * dt * velocidad["actual"]

                fuel["nivel"] -= dt * (velocidad["actual"] ** 2) * CONSUMO_BASE
                if fuel["nivel"] <= 0:
                    fuel["nivel"] = 0
                    estado["modo"] = "reentry"
                    estado["reentry_vel"] = max(velocidad["actual"], 0.5)

                if estado["modo"] == "normal" and velocidad["actual"] < VEL_CAIDA:
                    estado["modo"] = "reentry"
                    estado["reentry_vel"] = max(velocidad["actual"], 0.3)

            elif modo == "reentry":
                vel = estado["reentry_vel"] * 0.995
                estado["reentry_vel"] = vel
                estado["t_rot"] += dt * vel

                alt_min_factor = R_TIERRA / R_ORBITA_BASE
                alpha_alt = 0.02
                estado["alt_factor"] += (alt_min_factor - estado["alt_factor"]) * alpha_alt

                r_temp = R_ORBITA_BASE * estado["alt_factor"]
                omega_eff = OMEGA_ORBITA_BASE * (R_ORBITA_BASE / r_temp) ** 1.5
                estado["nu"] += omega_eff * dt * vel

                r_now = R_ORBITA_BASE * estado["alt_factor"]
                alt_now = r_now - R_TIERRA
                if alt_now < 50:
                    estado["modo"] = "impacto"
                    poner_destruido()

            elif modo == "impacto":
                poner_destruido()

            r = R_ORBITA_BASE * estado["alt_factor"]
            t_rot = estado["t_rot"]
            nu = estado["nu"]

            x_orb = r * np.cos(nu)
            y_orb = r * np.sin(nu)

            x_eci = x_orb
            y_eci = y_orb * np.cos(INCLINACION)
            z_eci = y_orb * np.sin(INCLINACION)

            theta_t = OMEGA_TIERRA * t_rot
            x_ecef = x_eci * np.cos(-theta_t) - y_eci * np.sin(-theta_t)
            y_ecef = x_eci * np.sin(-theta_t) + y_eci * np.cos(-theta_t)
            z_ecef = z_eci

            r_norm = np.sqrt(x_ecef**2 + y_ecef**2 + z_ecef**2)
            lat = np.degrees(np.arcsin(z_ecef / r_norm))
            lon = np.degrees(np.arctan2(y_ecef, x_ecef))

            if estado["modo"] != "impacto":
                trail2d_x.append(x_eci)
                trail2d_y.append(y_eci)
                
            sat2d_trail.set_data(trail2d_x, trail2d_y)
            sat2d_point.set_data([x_eci], [y_eci])

            sat3d_point.set_data([x_eci], [y_eci])
            sat3d_point.set_3d_properties([z_eci])

            if estado["modo"] != "impacto":
                if lons and abs(lon - lons[-1]) > 180:
                    lons.append(np.nan)
                    lats.append(np.nan)
                lons.append(lon)
                lats.append(lat)

            track_line.set_data(lons, lats)
            sat_point.set_data([lon], [lat])

            psi_deg = angulo_cobertura(r)
            footprint.center = (lon, lat)
            footprint.set_radius(psi_deg)

            lon_sun = (t_rot / 3600.0) * 15.0
            lon_sun = ((lon_sun + 180) % 360) - 180
            lon_night_center = lon_sun + 180
            lon_night_center = ((lon_night_center + 180) % 360) - 180
            x0 = lon_night_center - 90
            night_patch.set_x(x0)
            night_patch.set_width(180)

            frac_fuel = fuel["nivel"] / FUEL_MAX
            fuel_bar.set_height(frac_fuel)
            fuel_text.set_text(f"{frac_fuel * 100:3.0f}%")

            if estado["comms_ok"]:
                current_speed = velocidad["actual"] if estado["modo"] == "normal" else estado["reentry_vel"]
                estado["speed_display"] = current_speed

            speed_value_text.set_text(f"{estado['speed_display']:.2f}x")
            actualizar_aguja_velocidad(estado["speed_display"])

            msg = ""
            color = "orange"
            alt_now = r - R_TIERRA

            if estado["modo"] == "normal" and fuel["nivel"] > 0:
                if velocidad["actual"] > 6:
                    msg = "CONSUMIENDO DEMASIADO"
                if velocidad["actual"] > 8:
                    msg = "RIESGO DE SALIR DE ORBITA"
                    color = "red"
            elif estado["modo"] == "reentry":
                if alt_now > 200:
                    msg = "PERDIDA DE CONTROL Y COMUNICACIONES"
                    color = "red"
                    ser.write(f"G\n".encode())

                    if estado["comms_ok"]:
                        estado["comms_ok"] = False
                else:
                    msg = "COLISION INMINENTE"
                    color = "red"
            elif estado["modo"] == "impacto":
                msg = "IMPACTO"
                color = "red"

            warning_text.set_text(msg)
            warning_text.set_color(color)

            speed_label_text.set_text("Ultimo dato registrado" if not estado["comms_ok"] else "")

            return (sat2d_trail, sat2d_point, sat3d_point,
                    track_line, sat_point,
                    fuel_bar, fuel_text, warning_text,
                    night_patch, footprint,
                    speed_needle, speed_value_text, speed_label_text)

        ani = FuncAnimation(fig, update, frames=2000, init_func=init, interval=30, blit=False)
        plt.tight_layout(rect=[0, 0.06, 1, 1])
        plt.show()

    crear_simulacion_completa()

def leer_velocidad_pot():
    """Ahora NO lee del puerto serie. Solo consume q_vel (evita conflicto)."""
    global velocidad_pot
    while velocidad_pot:
        try:
            v = q_vel.get(timeout=0.2)
            # ya actualizamos velocidad_objetivo_externa en serial_reader()
        except Empty:
            pass

def Parar_velocidad_pot():
    global velocidad_pot
    velocidad_pot = False
    ser.write(b'P:\n')
    log_event("INFO", "Parar velocidad")

def Tierra():
    log_event("INFO", "Medias en tierra")
    ser.write(b'T\n')

def Satelite():
    log_event("INFO", "Medias en satelite")
    ser.write(b'S\n')
def Comando():
    comando = comandoEntry.get().strip()
    log_event("COMANDO", comando)

# ===============================================================
# === INTERFAZ TKINTER ===
# ===============================================================
window = Tk()
window.geometry("1500x800")
window.title("INTERACCIÓN CON EL SATÉLITE")

for i in range(6):
    window.columnconfigure(i, weight=1)
for i in range(8):
    window.rowconfigure(i, weight=0)
window.rowconfigure(6, weight=1)

tituloLabel = Label(window, text="INTERACCIÓN CON EL SATÉLITE", font=("Courier", 20, "italic"))
tituloLabel.grid(row=0, column=0, columnspan=6, padx=5, pady=5, sticky=N+S+E+W)

tiempoEntry = Entry(window)
tiempoEntry.grid(row=2, column=3, padx=5, pady=5, sticky=N+S+E+W)

valormax = Entry(window)
valormax.grid(row=1, column=3, padx=5, pady=5, sticky=N+S+E+W)

AnguloEntry = Entry(window)
AnguloEntry.grid(row=3, column=2, padx=5, pady=5, sticky=N+S+E+W)

comandoEntry = Entry(window)
comandoEntry.grid(row=4, column=2, padx=5, pady=5, sticky=N+S+E+W)

# row 1
Button(window, text="Mostrar gráfic tyh", bg='red', fg="white", command=Mostrar).grid(row=1, column=0, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Ocultar gráfica tyh", bg='yellow', fg="black", command=Ocultar).grid(row=1, column=1, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Reanudar tyh", bg='blue', fg="white", command=Reanudar).grid(row=1, column=2, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Enviar temp max", bg='red', fg="white", command=Tempmax).grid(row=1, column=4, padx=5, pady=5, sticky=N+S+E+W)

# row 2
Button(window, text="Medias en tierra", bg='red', fg="white", command=Tierra).grid(row=2, column=0, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Medias en satelite", bg='red', fg="white", command=Satelite).grid(row=2, column=1, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Parar tyh", bg='green', fg="white", command=Parar).grid(row=2, column=2, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Envia tiempo", bg='purple', fg="yellow", command=Tiempo).grid(row=2, column=4, padx=5, pady=5, sticky=N+S+E+W)

# row 3
Button(window, text="Mostrar radar", bg='orange', fg="black", command=Radar).grid(row=3, column=0, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Ocultar radar", bg='gray', fg="white", command=OcultarRadar).grid(row=3, column=1, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Envia ángulo", bg='red', fg="black", command=Angulo).grid(row=3, column=3, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Mostrar Posición", bg='red', fg="black", command=Posi).grid(row=3, column=4, padx=5, pady=5, sticky=N+S+E+W)

# row 4
Button(window, text="Seguir servo", bg='pink', fg="black", command=SeguirServo).grid(row=4, column=0, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Parar sensor", bg='red', fg="black", command=PararSensor).grid(row=4, column=1, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Envia comando", bg='red', fg="black", command=Comando).grid(row=4, column=3, padx=5, pady=5, sticky=N+S+E+W)
Button(window, text="Parar velocidad", bg='blue', fg="white", command=Parar_velocidad_pot).grid(row=4, column=4, padx=5, pady=5, sticky=N+S+E+W)

# row 7
Button(window, text="Cerrar", bg='red', fg="white", command=Cerrar).grid(row=7, column=5, padx=5, pady=5, sticky=N+S+E+W)

frameGrafica = Frame(window, bg='white', relief=RIDGE, borderwidth=2)
frameGrafica.grid(row=6, column=0, columnspan=3, padx=10, pady=10, sticky=N+S+E+W)

frameRadar = Frame(window, bg='white', relief=RIDGE, borderwidth=2)
frameRadar.grid(row=6, column=3, columnspan=3, padx=10, pady=10, sticky=N+S+E+W)

framePosi = Frame(window, bg='white', relief=RIDGE, borderwidth=2)
framePosi.grid(row=6, column=6, columnspan=3, padx=10, pady=10, sticky=N+S+E+W)

threading.Thread(target=leer_velocidad_pot, daemon=True).start()

window.mainloop()