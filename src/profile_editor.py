from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QListWidget, QLabel, QLineEdit, QCheckBox, QSpinBox,
                             QComboBox, QGroupBox, QMessageBox, QSplitter,
                             QListWidgetItem, QWidget, QFormLayout, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import time
class ProfileEditor(QDialog):
    profile_saved = pyqtSignal()
    
    def __init__(self, profile_name, available_programs, profile_manager):
        super().__init__()
        self.profile_name = profile_name
        self.available_programs = available_programs
        self.profile_manager = profile_manager
        self.selected_programs = []
        
        self.init_ui()
        self.load_existing_profile()
        
    def init_ui(self):
        self.setWindowTitle(f"Editor de Perfil: {self.profile_name}")
        self.setGeometry(150, 150, 1200, 800)
        
        layout = QVBoxLayout(self)
        
        # Nombre del perfil
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Nombre del perfil:"))
        self.name_edit = QLineEdit(self.profile_name)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)
        
        # Splitter principal
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Panel izquierdo - Programas disponibles
        left_panel = self.create_available_programs_panel()
        splitter.addWidget(left_panel)
        
        # Panel derecho - Programas seleccionados
        right_panel = self.create_selected_programs_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([500, 700])
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("Guardar Perfil")
        save_btn.clicked.connect(self.save_profile)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
    def create_available_programs_panel(self):
        """Crear panel de programas disponibles"""
        group = QGroupBox("Programas Disponibles")
        layout = QVBoxLayout(group)
        
        # Buscador
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Buscar:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.filter_programs)
        search_layout.addWidget(self.search_edit)
        layout.addLayout(search_layout)
        
        # Lista de programas
        self.available_list = QListWidget()
        self.available_list.itemDoubleClicked.connect(self.add_program)
        layout.addWidget(self.available_list)
        
        # Botón agregar
        add_btn = QPushButton("Agregar Programa →")
        add_btn.clicked.connect(self.add_program)
        layout.addWidget(add_btn)
        
        # Cargar programas
        self.populate_available_programs()
        
        return group
        
    def create_selected_programs_panel(self):
        """Crear panel de programas seleccionados"""
        group = QGroupBox("Programas en el Perfil")
        layout = QVBoxLayout(group)
        
        # Lista de programas seleccionados
        self.selected_list = QListWidget()
        self.selected_list.itemClicked.connect(self.show_program_config)
        layout.addWidget(self.selected_list)
        
        # Botones de control
        buttons_layout = QHBoxLayout()
        
        remove_btn = QPushButton("Quitar")
        remove_btn.clicked.connect(self.remove_program)
        buttons_layout.addWidget(remove_btn)
        
        up_btn = QPushButton("↑ Subir")
        up_btn.clicked.connect(self.move_program_up)
        buttons_layout.addWidget(up_btn)
        
        down_btn = QPushButton("↓ Bajar")
        down_btn.clicked.connect(self.move_program_down)
        buttons_layout.addWidget(down_btn)
        
        layout.addLayout(buttons_layout)
        
        # Panel de configuración del programa
        self.config_panel = self.create_program_config_panel()
        layout.addWidget(self.config_panel)
        
        return group
        
    def create_program_config_panel(self):
        """Crear panel de configuración del programa"""
        group = QGroupBox("Configuración del Programa")
        group.setEnabled(False)
        
        scroll = QScrollArea()
        scroll_widget = QWidget()
        layout = QFormLayout(scroll_widget)
        
        # Monitor
        self.monitor_combo = QComboBox()
        self.monitor_combo.addItems(["Principal", "Secundario"])
        layout.addRow("Monitor:", self.monitor_combo)
        
        # Estado de la ventana
        self.window_state_combo = QComboBox()
        self.window_state_combo.addItems(["Normal", "Maximizada", "Minimizada"])
        self.window_state_combo.currentTextChanged.connect(self.on_window_state_changed)
        layout.addRow("Estado:", self.window_state_combo)
        
        # Posición y tamaño (solo si no está maximizada)
        self.position_group = QWidget()
        pos_layout = QFormLayout(self.position_group)
        
        self.x_spin = QSpinBox()
        self.x_spin.setRange(0, 9999)
        self.x_spin.setValue(100)
        pos_layout.addRow("Posición X:", self.x_spin)
        
        self.y_spin = QSpinBox()
        self.y_spin.setRange(0, 9999)
        self.y_spin.setValue(100)
        pos_layout.addRow("Posición Y:", self.y_spin)
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 9999)
        self.width_spin.setValue(800)
        pos_layout.addRow("Ancho:", self.width_spin)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 9999)
        self.height_spin.setValue(600)
        pos_layout.addRow("Alto:", self.height_spin)
        
        layout.addRow(self.position_group)
        
        # Opciones adicionales
        self.avoid_duplicates_check = QCheckBox("Evitar duplicados")
        self.avoid_duplicates_check.setChecked(True)
        layout.addRow(self.avoid_duplicates_check)
        
        # Conectar cambios
        for widget in [self.monitor_combo, self.window_state_combo, self.x_spin, 
                      self.y_spin, self.width_spin, self.height_spin, self.avoid_duplicates_check]:
            if hasattr(widget, 'currentTextChanged'):
                widget.currentTextChanged.connect(self.update_program_config)
            elif hasattr(widget, 'valueChanged'):
                widget.valueChanged.connect(self.update_program_config)
            elif hasattr(widget, 'toggled'):
                widget.toggled.connect(self.update_program_config)
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        
        group_layout = QVBoxLayout(group)
        group_layout.addWidget(scroll)
        
        return group
        
    def populate_available_programs(self):
        """Poblar lista de programas disponibles"""
        self.available_list.clear()
        for program in self.available_programs:
            item = QListWidgetItem(f"{program['name']}")
            item.setData(Qt.UserRole, program)
            self.available_list.addItem(item)
            
    def filter_programs(self):
        """Filtrar programas por texto de búsqueda"""
        search_text = self.search_edit.text().lower()
        
        for i in range(self.available_list.count()):
            item = self.available_list.item(i)
            program = item.data(Qt.UserRole)
            visible = search_text in program['name'].lower()
            item.setHidden(not visible)
            
    def add_program(self):
        """Agregar programa al perfil"""
        current_item = self.available_list.currentItem()
        if current_item:
            program = current_item.data(Qt.UserRole)
            
            # Verificar si ya está agregado
            for existing in self.selected_programs:
                if existing['path'] == program['path']:
                    QMessageBox.information(self, "Información", 
                                          "Este programa ya está en el perfil")
                    return
                    
            # Agregar configuración por defecto
            program_config = {
                'name': program['name'],
                'path': program['path'],
                'window_config': {
                    'monitor': 'primary',
                    'maximized': False,
                    'x': 100,
                    'y': 100,
                    'width': 800,
                    'height': 600
                },
                'start_minimized': False,
                'avoid_duplicates': True
            }
            
            self.selected_programs.append(program_config)
            self.update_selected_list()
            
    def remove_program(self):
        """Quitar programa del perfil"""
        current_row = self.selected_list.currentRow()
        if current_row >= 0:
            del self.selected_programs[current_row]
            self.update_selected_list()
            self.config_panel.setEnabled(False)
            
    def move_program_up(self):
        """Mover programa hacia arriba en la lista"""
        current_row = self.selected_list.currentRow()
        if current_row > 0:
            self.selected_programs[current_row], self.selected_programs[current_row - 1] = \
                self.selected_programs[current_row - 1], self.selected_programs[current_row]
            self.update_selected_list()
            self.selected_list.setCurrentRow(current_row - 1)
            
    def move_program_down(self):
        """Mover programa hacia abajo en la lista"""
        current_row = self.selected_list.currentRow()
        if current_row < len(self.selected_programs) - 1:
            self.selected_programs[current_row], self.selected_programs[current_row + 1] = \
                self.selected_programs[current_row + 1], self.selected_programs[current_row]
            self.update_selected_list()
            self.selected_list.setCurrentRow(current_row + 1)
            
    def update_selected_list(self):
        """Actualizar lista de programas seleccionados"""
        self.selected_list.clear()
        for program in self.selected_programs:
            self.selected_list.addItem(program['name'])
            
    def show_program_config(self):
        """Mostrar configuración del programa seleccionado"""
        current_row = self.selected_list.currentRow()
        if current_row >= 0:
            program = self.selected_programs[current_row]
            self.config_panel.setEnabled(True)
            
            # Cargar configuración en los controles
            config = program.get('window_config', {})
            
            monitor = 'Secundario' if config.get('monitor') == 'secondary' else 'Principal'
            self.monitor_combo.setCurrentText(monitor)
            
            if config.get('maximized', False):
                self.window_state_combo.setCurrentText('Maximizada')
            elif program.get('start_minimized', False):
                self.window_state_combo.setCurrentText('Minimizada')
            else:
                self.window_state_combo.setCurrentText('Normal')
                
            self.x_spin.setValue(config.get('x', 100))
            self.y_spin.setValue(config.get('y', 100))
            self.width_spin.setValue(config.get('width', 800))
            self.height_spin.setValue(config.get('height', 600))
            
            self.avoid_duplicates_check.setChecked(program.get('avoid_duplicates', True))
            
            self.on_window_state_changed()
            
    def on_window_state_changed(self):
        """Manejar cambio de estado de ventana"""
        state = self.window_state_combo.currentText()
        self.position_group.setEnabled(state == 'Normal')
        
    def update_program_config(self):
        """Actualizar configuración del programa actual"""
        current_row = self.selected_list.currentRow()
        if current_row >= 0:
            program = self.selected_programs[current_row]
            
            # Actualizar configuración
            monitor = 'secondary' if self.monitor_combo.currentText() == 'Secundario' else 'primary'
            state = self.window_state_combo.currentText()
            
            program['window_config'] = {
                'monitor': monitor,
                'maximized': state == 'Maximizada',
                'x': self.x_spin.value(),
                'y': self.y_spin.value(),
                'width': self.width_spin.value(),
                'height': self.height_spin.value()
            }
            
            program['start_minimized'] = state == 'Minimizada'
            program['avoid_duplicates'] = self.avoid_duplicates_check.isChecked()
            
    def load_existing_profile(self):
        """Cargar perfil existente si existe"""
        profiles = self.profile_manager.load_profiles()
        if self.profile_name in profiles:
            profile = profiles[self.profile_name]
            self.selected_programs = profile.get('programs', [])
            self.update_selected_list()
            
    def save_profile(self):
        """Guardar el perfil"""
        profile_name = self.name_edit.text().strip()
        if not profile_name:
            QMessageBox.warning(self, "Advertencia", "El nombre del perfil no puede estar vacío")
            return
            
        if not self.selected_programs:
            QMessageBox.warning(self, "Advertencia", "Debes agregar al menos un programa al perfil")
            return
            
        # Verificar si el nombre cambió y ya existe
        if profile_name != self.profile_name and self.profile_manager.profile_exists(profile_name):
            QMessageBox.warning(self, "Advertencia", "Ya existe un perfil con ese nombre")
            return
            
        profile_data = {
            'programs': self.selected_programs,
            'created_at': self.profile_manager.load_profiles().get(self.profile_name, {}).get('created_at', ''),
            'modified_at': str(int(time.time()))
        }
        
        # Si el nombre cambió, eliminar el perfil anterior
        if profile_name != self.profile_name:
            self.profile_manager.delete_profile(self.profile_name)
            
        if self.profile_manager.save_profile(profile_name, profile_data):
            QMessageBox.information(self, "Éxito", "Perfil guardado correctamente")
            self.profile_saved.emit()
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Error al guardar el perfil")