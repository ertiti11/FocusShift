import json
import os
import threading
import time
from pathlib import Path
from src.window_manager import launch_and_place_window

class ProfileManager:
    def __init__(self):
        self.data_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "ProgramProfileManager")
        self.profiles_file = os.path.join(self.data_dir, "profiles.json")
        os.makedirs(self.data_dir, exist_ok=True)
        
    def load_profiles(self):
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print(f"[ERROR] No se pudo leer el archivo de perfiles: {self.profiles_file}")
                return {}
        return {}
        
    def save_profiles(self, profiles):
        try:
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"[ERROR] No se pudo guardar el archivo de perfiles: {e}")
            return False
            
    def save_profile(self, profile_name, profile_data):
        profiles = self.load_profiles()
        profiles[profile_name] = profile_data
        saved = self.save_profiles(profiles)
        return saved
        
    def delete_profile(self, profile_name):
        profiles = self.load_profiles()
        if profile_name in profiles:
            del profiles[profile_name]
            return self.save_profiles(profiles)
        return False
        
    def profile_exists(self, profile_name):
        profiles = self.load_profiles()
        return profile_name in profiles

    def execute_profile(self, profile_name):
        """Ejecuta un perfil de programas en un hilo separado usando window_manager."""
        def run_program_threaded(program_config):
            try:
                self._launch_and_place_program(program_config)
            except Exception as e:
                print(f"Error al lanzar {program_config.get('name', 'programa')}: {e}")

        def run_profile_logic():
            profiles = self.load_profiles()
            if profile_name not in profiles:
                print(f"Perfil '{profile_name}' no encontrado")
                return

            profile = profiles[profile_name]
            threads = []
            for program_config in profile.get('programs', []):
                t = threading.Thread(target=run_program_threaded, args=(program_config,), daemon=True)
                t.start()
                threads.append(t)
            print(f"Programas lanzados para el perfil '{profile_name}': {len(threads)}")

        threading.Thread(target=run_profile_logic, daemon=True).start()

    def _launch_and_place_program(self, program_config):
        """Lanza y coloca el programa usando window_manager."""
        exe_path = program_config['path']
        window_cfg = program_config.get('window_config', {})
        fallback_title = program_config.get('window_title')
        maximize = window_cfg.get('maximized', False)
        minimize = window_cfg.get('minimized', False)
        width = window_cfg.get('width')
        height = window_cfg.get('height')
        x = window_cfg.get('x', 0)
        y = window_cfg.get('y', 0)
        monitor = window_cfg.get('monitor', 'primary')

        # ---
        # SOPORTE PARA monitor COMO ÍNDICE O COMO STRING ('primary'/'secondary')
        # Se recomienda guardar el monitor como número (0=primario, 1=secundario, ...)
        # Ejemplo de perfil recomendado:
        #   "window_config": { "monitor": 1, ... }
        # Si se usa 'primary' o 'secondary', se traduce a índice automáticamente.
        from screeninfo import get_monitors
        monitors = get_monitors()
        monitor_index = 0
        if isinstance(monitor, int):
            if 0 <= monitor < len(monitors):
                monitor_index = monitor
            else:
                print(f"[WARN] Monitor {monitor} fuera de rango, usando 0")
                monitor_index = 0
        elif isinstance(monitor, str):
            if monitor == 'secondary' and len(monitors) > 1:
                for idx, m in enumerate(monitors):
                    if not getattr(m, 'is_primary', False):
                        monitor_index = idx
                        break
                else:
                    monitor_index = 1
            elif monitor == 'primary':
                for idx, m in enumerate(monitors):
                    if getattr(m, 'is_primary', False):
                        monitor_index = idx
                        break
                else:
                    monitor_index = 0
            else:
                print(f"[WARN] Valor de monitor desconocido: {monitor}, usando 0")
                monitor_index = 0
        else:
            print(f"[WARN] Tipo de monitor no soportado: {type(monitor)}, usando 0")
            monitor_index = 0

        print(f"Configurando programa: {program_config['name']} en monitor {monitor_index} (valor original: {monitor})")
        hwnd = launch_and_place_window(
            exe_path=exe_path,
            monitor_index=monitor_index,
            width=width,
            height=height,
            x_offset=x,
            y_offset=y,
            maximize=maximize,
            minimize=minimize,
            fallback_title=fallback_title,
            timeout=10
        )
        if hwnd:
            print(f"Ventana configurada correctamente: {hwnd}")
            return True
        else:
            print("No se pudo configurar la ventana.")
            return False

    # ---
    # NOTA: Para máxima compatibilidad, guarda los perfiles con el monitor como número (0=primario, 1=secundario, ...)
    # Ejemplo:
    #   "window_config": { "monitor": 1, ... }
    # ---