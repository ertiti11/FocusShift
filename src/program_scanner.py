import os
import winreg
import psutil
from pathlib import Path
import subprocess
import json



class ProgramScanner:
    def __init__(self):
        self.cached_programs = []
        
    def scan_installed_programs(self):
        """Escanear programas instalados en Windows"""
        programs = []
        
        try:
            programs.extend(self._scan_registry())
            programs.extend(self._scan_common_folders())
            programs.extend(self._scan_modern_apps())  # <-- Esto debe existir y devolver lista
        except Exception as e:
            print(f"[!] Error escaneando programas: {e}")
        
        # Eliminar duplicados y ordenar
        unique_programs = self._remove_duplicates(programs)
        unique_programs.sort(key=lambda x: x['name'].lower())
        
        self.cached_programs = unique_programs
        return unique_programs
        

    
    def _scan_modern_apps(self):
        """Escanear aplicaciones modernas (Microsoft Store/UWP apps)"""
        programs = []
        try:
            # Ejecutar PowerShell para obtener lista de apps
            result = subprocess.run([
                "powershell", "-Command",
                "Get-StartApps | ConvertTo-Json"
            ], capture_output=True, text=True, check=True)

            apps = json.loads(result.stdout)

            if isinstance(apps, dict):  # Solo una app
                apps = [apps]

            for app in apps:
                name = app.get('Name')
                app_id = app.get('AppID')
                if name and app_id and not app_id.endswith('.exe'):
                    programs.append({
                        'name': name,
                        'path': app_id,
                        'source': 'modern'
                    })
        except subprocess.CalledProcessError as e:
            print(f"[!] Error al escanear apps modernas: {e}")

        return programs

    def _scan_registry(self):
        """Escanear el registro de Windows para programas instalados"""
        programs = []
        
        # Rutas del registro donde se almacenan los programas instalados
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        ]
        
        for hkey, path in registry_paths:
            try:
                with winreg.OpenKey(hkey, path) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                program = self._extract_program_info(subkey)
                                if program:
                                    programs.append(program)
                        except (OSError, FileNotFoundError):
                            continue
            except (OSError, FileNotFoundError):
                continue
                
        return programs
        
    def _extract_program_info(self, subkey):
        """Extraer información del programa desde el registro"""
        try:
            # Obtener nombre del programa
            try:
                name = winreg.QueryValueEx(subkey, "DisplayName")[0]
            except FileNotFoundError:
                return None
                
            # Obtener ruta del ejecutable
            exe_path = None
            try:
                # Intentar obtener la ruta del ejecutable
                install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                if install_location and os.path.exists(install_location):
                    # Buscar ejecutables en la carpeta de instalación
                    for file in os.listdir(install_location):
                        if file.lower().endswith('.exe'):
                            exe_path = os.path.join(install_location, file)
                            break
            except FileNotFoundError:
                pass
                
            # Si no encontramos la ruta, intentar con UninstallString
            if not exe_path:
                try:
                    uninstall_string = winreg.QueryValueEx(subkey, "UninstallString")[0]
                    if uninstall_string and '.exe' in uninstall_string:
                        # Extraer la ruta del ejecutable del string de desinstalación
                        parts = uninstall_string.split('.exe')
                        if parts:
                            potential_path = parts[0] + '.exe'
                            potential_path = potential_path.strip('"')
                            if os.path.exists(potential_path):
                                exe_path = potential_path
                except FileNotFoundError:
                    pass
                    
            if exe_path and os.path.exists(exe_path):
                return {
                    'name': name,
                    'path': exe_path,
                    'source': 'registry'
                }
                
        except Exception:
            pass
            
        return None
        
    def _scan_common_folders(self):
        """Escanear carpetas comunes donde se instalan programas"""
        programs = []
        
        common_folders = [
            r"C:\Program Files",
            r"C:\Program Files (x86)",
            os.path.join(os.path.expanduser("~"), "AppData", "Local", "Programs")
        ]
        
        for folder in common_folders:
            if os.path.exists(folder):
                programs.extend(self._scan_folder(folder))
                
        return programs
        
    def _scan_folder(self, folder_path, max_depth=2, current_depth=0):
        """Escanear una carpeta en busca de ejecutables"""
        programs = []
        
        if current_depth >= max_depth:
            return programs
            
        try:
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                
                if os.path.isfile(item_path) and item.lower().endswith('.exe'):
                    # Filtrar ejecutables del sistema y desinstaladores
                    if not self._is_system_executable(item.lower()):
                        programs.append({
                            'name': os.path.splitext(item)[0],
                            'path': item_path,
                            'source': 'folder'
                        })
                        
                elif os.path.isdir(item_path) and current_depth < max_depth - 1:
                    # Buscar recursivamente en subdirectorios
                    programs.extend(self._scan_folder(item_path, max_depth, current_depth + 1))
                    
        except (PermissionError, OSError):
            pass
            
        return programs
        
    def _is_system_executable(self, filename):
        """Verificar si un ejecutable es del sistema o desinstalador"""
        system_keywords = [
            'uninstall', 'uninst', 'setup', 'install', 'update', 'updater',
            'crash', 'error', 'debug', 'log', 'temp', 'cache'
        ]
        
        return any(keyword in filename for keyword in system_keywords)
        
    def _remove_duplicates(self, programs):
        """Eliminar programas duplicados"""
        seen = set()
        unique_programs = []
        
        for program in programs:
            # Usar el nombre y la ruta como clave única
            key = (program['name'].lower(), program['path'].lower())
            if key not in seen:
                seen.add(key)
                unique_programs.append(program)
                
        return unique_programs
        
    def get_cached_programs(self):
        """Obtener la lista de programas en caché"""
        return self.cached_programs