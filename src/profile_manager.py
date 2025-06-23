import json
import os
import subprocess
import time
import win32gui
import win32con
import win32process
import psutil
from pathlib import Path

class ProfileManager:
    def __init__(self):
        self.data_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "ProgramProfileManager")
        self.profiles_file = os.path.join(self.data_dir, "profiles.json")
        os.makedirs(self.data_dir, exist_ok=True)
        
    def load_profiles(self):
        """Cargar perfiles desde archivo JSON"""
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
        
    def save_profiles(self, profiles):
        """Guardar perfiles en archivo JSON"""
        try:
            with open(self.profiles_file, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False
            
    def save_profile(self, profile_name, profile_data):
        """Guardar un perfil específico"""
        profiles = self.load_profiles()
        profiles[profile_name] = profile_data
        return self.save_profiles(profiles)
        
    def delete_profile(self, profile_name):
        """Eliminar un perfil"""
        profiles = self.load_profiles()
        if profile_name in profiles:
            del profiles[profile_name]
            return self.save_profiles(profiles)
        return False
        
    def profile_exists(self, profile_name):
        """Verificar si existe un perfil"""
        profiles = self.load_profiles()
        return profile_name in profiles
        
    def execute_profile(self, profile_name):
        """Ejecutar un perfil completo"""
        profiles = self.load_profiles()
        if profile_name not in profiles:
            raise ValueError(f"Perfil '{profile_name}' no encontrado")
            
        profile = profiles[profile_name]
        success_count = 0
        
        for program_config in profile.get('programs', []):
            try:
                if self._launch_program(program_config):
                    success_count += 1
            except Exception as e:
                print(f"Error al lanzar {program_config.get('name', 'programa')}: {e}")
                
        return success_count
        
    def _launch_program(self, program_config):
        """Lanzar un programa individual con su configuración"""
        program_path = program_config['path']
        
        # Verificar si el programa ya está ejecutándose
        if program_config.get('avoid_duplicates', True):
            if self._is_program_running(program_path):
                print(f"El programa {program_config['name']} ya está ejecutándose")
                return True
                
        try:
            # Lanzar el programa
            if program_config.get('start_minimized', False):
                # Iniciar minimizado
                process = subprocess.Popen([program_path], 
                                         creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                process = subprocess.Popen([program_path])
                
            # Esperar un poco para que el programa se inicie
            time.sleep(2)
            
            # Configurar la ventana si es necesario
            if not program_config.get('start_minimized', False):
                self._configure_window(program_config, process.pid)
                
            return True
            
        except Exception as e:
            print(f"Error al lanzar programa: {e}")
            return False
            
    def _is_program_running(self, program_path):
        """Verificar si un programa está ejecutándose"""
        program_name = os.path.basename(program_path).lower()
        
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                if proc.info['exe'] and os.path.basename(proc.info['exe']).lower() == program_name:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        return False
        
    def _configure_window(self, program_config, pid):
        """Configurar la ventana del programa"""
        # Buscar la ventana del proceso
        windows = []
        
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                if window_pid == pid:
                    windows.append(hwnd)
            return True
            
        # Intentar varias veces ya que la ventana puede tardar en aparecer
        for attempt in range(10):
            windows.clear()
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            if windows:
                break
                
            time.sleep(0.5)
            
        if not windows:
            print("No se pudo encontrar la ventana del programa")
            return
            
        hwnd = windows[0]  # Usar la primera ventana encontrada
        
        # Configurar posición y tamaño
        if 'window_config' in program_config:
            config = program_config['window_config']
            
            # Maximizar si es necesario
            if config.get('maximized', False):
                win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            else:
                # Configurar posición y tamaño personalizados
                x = config.get('x', 100)
                y = config.get('y', 100)
                width = config.get('width', 800)
                height = config.get('height', 600)
                
                win32gui.SetWindowPos(hwnd, 0, x, y, width, height, 0)
                
            # Configurar monitor si se especifica
            monitor = config.get('monitor', 'primary')
            if monitor == 'secondary':
                self._move_to_secondary_monitor(hwnd)
                
    def _move_to_secondary_monitor(self, hwnd):
        """Mover ventana al monitor secundario"""
        try:
            # Obtener información de monitores
            monitors = win32gui.EnumDisplayMonitors()
            
            if len(monitors) > 1:
                # Obtener el segundo monitor
                secondary_monitor = monitors[1][2]  # (left, top, right, bottom)
                
                # Mover la ventana al monitor secundario
                win32gui.SetWindowPos(hwnd, 0, 
                                    secondary_monitor[0] + 100,  # x
                                    secondary_monitor[1] + 100,  # y
                                    0, 0,  # width, height (mantener actual)
                                    win32con.SWP_NOSIZE)
        except Exception as e:
            print(f"Error al mover ventana al monitor secundario: {e}")