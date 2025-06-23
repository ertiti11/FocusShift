import sys
import json
import os
from PyQt5.QtWidgets import QApplication
from src.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Gestor de Perfiles de Programas")
    app.setApplicationVersion("1.0")
    
    # Crear directorio de datos si no existe
    data_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "ProgramProfileManager")
    os.makedirs(data_dir, exist_ok=True)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()