from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QLabel, QMessageBox,
                             QInputDialog, QSplitter, QGroupBox, QScrollArea)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont
from .program_scanner import ProgramScanner
from .profile_manager import ProfileManager
from .profile_editor import ProfileEditor
from .hotkey_manager import HotkeyManager
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.program_scanner = ProgramScanner()
        self.profile_manager = ProfileManager()
        self.hotkey_manager = HotkeyManager()
        self.profile_editor = None
        
        self.init_ui()
        self.load_profiles()
        self.scan_programs()
        self.hotkey_manager.hotkey_pressed.connect(self.execute_profile_by_name)
        self.hotkey_manager.start_monitoring()
        
    def init_ui(self):
        self.setWindowTitle("Gestor de Perfiles de Programas")
        self.setGeometry(100, 100, 1000, 700)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter para dividir la ventana
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Panel izquierdo - Lista de perfiles
        left_panel = self.create_profiles_panel()
        splitter.addWidget(left_panel)
        
        # Panel derecho - Programas instalados
        right_panel = self.create_programs_panel()
        splitter.addWidget(right_panel)
        
        # Configurar proporciones del splitter
        splitter.setSizes([400, 600])
        
        # Barra de estado
        self.statusBar().showMessage("Listo")
    def execute_profile_by_name(self, profile_name):
        if self.profile_manager.profile_exists(profile_name):
            self.statusBar().showMessage(f"Hotkey ejecuta: {profile_name}")
            self.profile_manager.execute_profile(profile_name)
        else:
            self.statusBar().showMessage(f"Perfil no encontrado: {profile_name}")        
    def create_profiles_panel(self):
        """Crear panel de perfiles guardados"""
        group = QGroupBox("Perfiles Guardados")
        layout = QVBoxLayout(group)
        
        # Lista de perfiles
        self.profiles_list = QListWidget()
        self.profiles_list.itemDoubleClicked.connect(self.execute_profile)
        layout.addWidget(self.profiles_list)
        
        # Botones de perfiles
        buttons_layout = QHBoxLayout()
        
        self.new_profile_btn = QPushButton("Nuevo Perfil")
        self.new_profile_btn.clicked.connect(self.create_new_profile)
        buttons_layout.addWidget(self.new_profile_btn)
        
        self.edit_profile_btn = QPushButton("Editar")
        self.edit_profile_btn.clicked.connect(self.edit_selected_profile)
        self.edit_profile_btn.setEnabled(False)
        buttons_layout.addWidget(self.edit_profile_btn)
        
        self.delete_profile_btn = QPushButton("Eliminar")
        self.delete_profile_btn.clicked.connect(self.delete_selected_profile)
        self.delete_profile_btn.setEnabled(False)
        buttons_layout.addWidget(self.delete_profile_btn)
        
        layout.addLayout(buttons_layout)
        
        # Botón ejecutar perfil
        self.execute_btn = QPushButton("Ejecutar Perfil")
        self.execute_btn.clicked.connect(self.execute_profile)
        self.execute_btn.setEnabled(False)
        self.execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        layout.addWidget(self.execute_btn)
        
        # Conectar selección de perfil
        self.profiles_list.itemSelectionChanged.connect(self.on_profile_selection_changed)
        
        return group
        
    def create_programs_panel(self):
        """Crear panel de programas instalados"""
        group = QGroupBox("Programas Instalados")
        layout = QVBoxLayout(group)
        
        # Botón para escanear programas
        self.scan_btn = QPushButton("Escanear Programas")
        self.scan_btn.clicked.connect(self.scan_programs)
        layout.addWidget(self.scan_btn)
        
        # Lista de programas
        self.programs_list = QListWidget()
        layout.addWidget(self.programs_list)
        
        # Label de información
        self.info_label = QLabel("Haz doble clic en un perfil para ejecutarlo")
        self.info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.info_label)
        
        return group
        
    def scan_programs(self):
        """Escanear programas instalados"""
        self.statusBar().showMessage("Escaneando programas...")
        self.scan_btn.setEnabled(False)
        
        # Usar QTimer para no bloquear la UI
        QTimer.singleShot(100, self._do_scan)
        
    def _do_scan(self):
        """Realizar el escaneo real"""
        try:
            programs = self.program_scanner.scan_installed_programs()
            self.programs_list.clear()
            
            for program in programs:
                self.programs_list.addItem(f"{program['name']} - {program['path']}")
                
            self.statusBar().showMessage(f"Encontrados {len(programs)} programas")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al escanear programas: {str(e)}")
            self.statusBar().showMessage("Error al escanear")
            
        finally:
            self.scan_btn.setEnabled(True)
            
    def load_profiles(self):
        """Cargar perfiles guardados"""
        profiles = self.profile_manager.load_profiles()
        self.profiles_list.clear()
        
        for profile_name in profiles.keys():
            self.profiles_list.addItem(profile_name)
            
    def create_new_profile(self):
        """Crear un nuevo perfil"""
        name, ok = QInputDialog.getText(self, "Nuevo Perfil", "Nombre del perfil:")
        if ok and name:
            if self.profile_manager.profile_exists(name):
                QMessageBox.warning(self, "Advertencia", "Ya existe un perfil con ese nombre")
                return
                
            self.open_profile_editor(name)
            
    def edit_selected_profile(self):
        """Editar el perfil seleccionado"""
        current_item = self.profiles_list.currentItem()
        if current_item:
            profile_name = current_item.text()
            self.open_profile_editor(profile_name)
            
    def open_profile_editor(self, profile_name):
        """Abrir el editor de perfiles"""
        programs = self.program_scanner.get_cached_programs()
        if not programs:
            QMessageBox.information(self, "Información", 
                                  "Primero debes escanear los programas instalados")
            return
            
        self.profile_editor = ProfileEditor(profile_name, programs, self.profile_manager)
        self.profile_editor.profile_saved.connect(self.on_profile_saved)
        self.profile_editor.show()
        
    def delete_selected_profile(self):
        """Eliminar el perfil seleccionado"""
        current_item = self.profiles_list.currentItem()
        if current_item:
            profile_name = current_item.text()
            reply = QMessageBox.question(self, "Confirmar", 
                                       f"¿Eliminar el perfil '{profile_name}'?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.profile_manager.delete_profile(profile_name)
                self.load_profiles()
                
    def execute_profile(self):
        """Ejecutar el perfil seleccionado"""
        current_item = self.profiles_list.currentItem()
        if current_item:
            profile_name = current_item.text()
            try:
                self.statusBar().showMessage(f"Ejecutando perfil: {profile_name}")
                success_count = self.profile_manager.execute_profile(profile_name)
                self.statusBar().showMessage(
                    f"Perfil ejecutado: {success_count} programas iniciados"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al ejecutar perfil: {str(e)}")
                self.statusBar().showMessage("Error al ejecutar perfil")
                
    def on_profile_selection_changed(self):
        """Manejar cambio de selección de perfil"""
        has_selection = bool(self.profiles_list.currentItem())
        self.edit_profile_btn.setEnabled(has_selection)
        self.delete_profile_btn.setEnabled(has_selection)
        self.execute_btn.setEnabled(has_selection)
        
    def on_profile_saved(self):
        self.load_profiles()

        # Registra la hotkey del perfil recién guardado
        profile_name = self.profile_editor.profile_name
        profiles = self.profile_manager.load_profiles()
        profile = profiles.get(profile_name)
        if profile:
            hotkey = profile.get('hotkey')
            if hotkey:
                self.hotkey_manager.register_hotkey(hotkey, profile_name)
        
    def closeEvent(self, event):
        """Manejar cierre de la aplicación"""
        self.hotkey_manager.cleanup()
        event.accept()