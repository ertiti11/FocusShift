import subprocess
import time
import win32gui
import win32process
import psutil
import os
import win32con
from screeninfo import get_monitors
import re

def find_existing_pid(process_name):
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                return proc.info['pid']
        except Exception:
            pass
    return None

def find_hwnd_by_pid(pid):
    hwnds = []
    def callback(hwnd, hwnds_list):
        if win32gui.IsWindowVisible(hwnd):
            try:
                _, win_pid = win32process.GetWindowThreadProcessId(hwnd)
                if win_pid == pid:
                    hwnds_list.append(hwnd)
            except Exception:
                pass
        return True
    win32gui.EnumWindows(callback, hwnds)
    return hwnds

def find_hwnd_by_title(keyword):
    keyword = keyword.lower()
    words = [w for w in re.split(r'[\s\-_.]+', keyword) if w]
    hwnds = []
    scores = []

    def callback(hwnd, hwnds_list):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd).lower()
            # Coincidencia exacta
            if keyword in title:
                hwnds_list.append((hwnd, title, len(words)))
            else:
                # Coincidencia parcial: cuenta cuántas palabras de la keyword están en el título
                match_count = sum(1 for w in words if w in title)
                if match_count > 0:
                    hwnds_list.append((hwnd, title, match_count))
        return True


    win32gui.EnumWindows(callback, hwnds)
    if not hwnds:
        return []
    # Ordena por número de palabras coincidentes (mayor primero)
    hwnds.sort(key=lambda x: x[2], reverse=True)
    # Devuelve solo los hwnd (puedes devolver el título si quieres)
    return [hwnd for hwnd, title, score in hwnds]

# ...el resto de tu código igual...

# En launch_program_and_get_hwnd, la llamada a find_hwnd_by_title ya usará la nueva lógica.

def launch_program_and_get_hwnd(exe_path, real_process_name=None, timeout=10, fallback_title=None):
    """
    Lanza un ejecutable y devuelve el HWND de la ventana principal.
    Si ya está abierto, devuelve el hwnd de la ventana existente.
    Si no encuentra por PID, busca por palabra clave en el título de la ventana.
    """
    process_name = real_process_name if real_process_name else os.path.basename(exe_path)

    # 1. Buscar si ya está abierto
    existing_pid = find_existing_pid(process_name)
    if existing_pid:
        print(f"Ya está abierto: {process_name} (PID: {existing_pid})")
        hwnds = find_hwnd_by_pid(existing_pid)
        if hwnds:
            print(f"HWND(s) encontrados: {hwnds}")
            return hwnds[0]
        keyword = fallback_title if fallback_title else os.path.splitext(os.path.basename(exe_path))[0]
        hwnds = find_hwnd_by_title(keyword)
        if hwnds:
            print(f"HWND(s) encontrados por título: {hwnds}")
            return hwnds[0]
        print("No se encontró la ventana principal ni por PID ni por título.")
        return None

    # 2. Lanzar el ejecutable
    proc = subprocess.Popen([exe_path])
    print(f"Lanzado: {exe_path} (PID launcher: {proc.pid})")

    # 3. Esperar a que el proceso real aparezca y su ventana esté lista (máximo timeout segundos)
    start_time = time.time()
    target_pid = None
    hwnd = None
    keyword = fallback_title if fallback_title else os.path.splitext(os.path.basename(exe_path))[0]

    while time.time() - start_time < timeout:
        # Buscar PID real
        pid = find_existing_pid(process_name)
        if pid:
            target_pid = pid
            # Buscar ventana por PID
            hwnds = find_hwnd_by_pid(target_pid)
            if hwnds:
                print(f"HWND(s) encontrados: {hwnds}")
                hwnd = hwnds[0]
                break
        # Si no se encuentra por PID, buscar por título
        hwnds = find_hwnd_by_title(keyword)
        if hwnds:
            print(f"HWND(s) encontrados por título: {hwnds}")
            hwnd = hwnds[0]
            break
        time.sleep(0.05)  # Muy reactivo, revisa cada 50ms

    if hwnd:
        return hwnd

    print("No se encontró la ventana principal ni por PID ni por título.")
    return None

def move_window_to_monitor(hwnd, monitor_index=0, width=None, height=None, x_offset=0, y_offset=0, maximize=False, minimize=False):
    """
    Mueve y redimensiona una ventana dada su HWND al monitor especificado.
    """
    monitors = get_monitors()
    print("Monitores detectados:")
    for i, m in enumerate(monitors):
        print(f"{i}: ({m.x},{m.y}) {m.width}x{m.height}")
    if monitor_index >= len(monitors):
        print(f"Monitor {monitor_index} no encontrado. Hay {len(monitors)} monitores.")
        return

    m = monitors[monitor_index]
    x = m.x + x_offset
    y = m.y + y_offset
    w = width if width else m.width
    h = height if height else m.height

    # Siempre restaurar primero, mover y luego maximizar/minimizar si corresponde
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    time.sleep(0.05)
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOP, x, y, w, h, 0)
    print(f"Ventana movida a monitor {monitor_index} en ({x},{y}) tamaño {w}x{h}")

    if maximize:
        time.sleep(0.05)
        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
        print(f"Ventana maximizada en monitor {monitor_index}")
    elif minimize:
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        print(f"Ventana minimizada en monitor {monitor_index}")

def launch_and_place_window(
    exe_path,
    monitor_index=0,
    width=None,
    height=None,
    x_offset=0,
    y_offset=0,
    maximize=False,
    minimize=False,
    real_process_name=None,
    timeout=10,
    fallback_title=None
):
    """
    Lanza un programa y lo coloca en el monitor y posición/tamaño deseados.
    """
    hwnd = launch_program_and_get_hwnd(
        exe_path,
        real_process_name=real_process_name,
        timeout=timeout,
        fallback_title=fallback_title
    )
    if hwnd:
        move_window_to_monitor(
            hwnd,
            monitor_index=monitor_index,
            width=width,
            height=height,
            x_offset=x_offset,
            y_offset=y_offset,
            maximize=maximize,
            minimize=minimize
        )
        return hwnd
    else:
        print("No se pudo lanzar o encontrar la ventana.")
        return None

# Ejemplo de uso:
# hwnd = launch_and_place_window(
#     r"C:\Windows\System32\notepad.exe",
#     monitor_index=0,   # Cambia a 0 para primario, 1 para secundario, etc.
#     width=800,
#     height=600,
#     x_offset=100,
#     y_offset=100,
#     maximize=False,
#     minimize=False
# )

