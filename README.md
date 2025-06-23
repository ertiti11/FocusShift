# Gestor de Perfiles de Programas para Windows

Una aplicación de escritorio para Windows que permite crear y gestionar perfiles de disposición de programas, automatizando la apertura y posicionamiento de múltiples aplicaciones con un solo clic.

## Características

- **Escaneo automático de programas**: Detecta todos los programas instalados en el sistema
- **Perfiles personalizables**: Crea perfiles con múltiples programas y configuraciones específicas
- **Control de ventanas**: Configura posición, tamaño, monitor y estado de cada ventana
- **Evitar duplicados**: Opción para no abrir programas que ya están ejecutándose
- **Interfaz intuitiva**: Editor visual para crear y modificar perfiles fácilmente
- **Almacenamiento local**: Los perfiles se guardan en formato JSON

## Requisitos del Sistema

- Windows 10 o superior
- Python 3.7 o superior

## Instalación

1. Clona o descarga este repositorio
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

1. Ejecuta la aplicación:
   ```bash
   python main.py
   ```

2. **Escanear programas**: Haz clic en "Escanear Programas" para detectar todas las aplicaciones instaladas

3. **Crear un perfil**:
   - Haz clic en "Nuevo Perfil"
   - Ingresa un nombre para el perfil
   - Agrega programas desde la lista de disponibles
   - Configura cada programa (monitor, posición, tamaño, estado)
   - Guarda el perfil

4. **Ejecutar un perfil**:
   - Selecciona un perfil de la lista
   - Haz clic en "Ejecutar Perfil" o doble clic en el perfil

## Configuración de Programas

Para cada programa en un perfil puedes configurar:

- **Monitor**: Principal o Secundario
- **Estado de ventana**: Normal, Maximizada o Minimizada
- **Posición**: Coordenadas X e Y personalizadas
- **Tamaño**: Ancho y alto de la ventana
- **Evitar duplicados**: No abrir si ya está ejecutándose

## Estructura del Proyecto

```
├── main.py                 # Punto de entrada de la aplicación
├── requirements.txt        # Dependencias de Python
├── src/
│   ├── __init__.py
│   ├── main_window.py      # Ventana principal
│   ├── program_scanner.py  # Escáner de programas instalados
│   ├── profile_manager.py  # Gestor de perfiles y ejecución
│   ├── profile_editor.py   # Editor de perfiles
│   └── hotkey_manager.py   # Gestor de atajos de teclado (básico)
└── README.md
```

## Almacenamiento de Datos

Los perfiles se guardan en:
```
%USERPROFILE%\AppData\Local\ProgramProfileManager\profiles.json
```

## Limitaciones Actuales

- El sistema de atajos de teclado globales está implementado de forma básica
- La detección de programas puede no incluir todas las aplicaciones (especialmente las de la Microsoft Store)
- Algunas aplicaciones pueden no responder correctamente al posicionamiento automático

## Posibles Mejoras Futuras

- Implementación completa de atajos de teclado globales usando la API de Windows
- Soporte para aplicaciones de la Microsoft Store
- Detección más robusta de ventanas de aplicaciones
- Interfaz para configurar atajos de teclado
- Exportar/importar perfiles
- Programación de ejecución automática
- Soporte para múltiples monitores con configuración avanzada

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue para discutir cambios importantes antes de crear un pull request.

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo LICENSE para más detalles.