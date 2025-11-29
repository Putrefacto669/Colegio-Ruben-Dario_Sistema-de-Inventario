#!/usr/bin/env python3
"""
Sistema de Gestión Académica - Instituto Rubén Darío
Punto de entrada principal
"""

import sys
import os
import logging

# Agregar el directorio raíz al path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import crear_db_y_schema
from config.config_manager import ConfigManager
from ui.theme_manager import FondoManager, CreadorGifsEjemplo
from modules.login import Login
from tkinter import Tk, messagebox

def setup_logging():
    """Configura el sistema de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('sistema_asistencia.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def main():
    """Función principal de la aplicación"""
    try:
        logger = setup_logging()
        logger.info("🚀 Iniciando Sistema de Gestión Académica")
        
        # Crear base de datos y esquema
        crear_db_y_schema()
        
        # Inicializar configuración
        config_manager = ConfigManager()
        
        # Crear GIFs de ejemplo si no existen
        try:
            from PIL import Image, ImageSequence
            CreadorGifsEjemplo.crear_gifs_ejemplo()
            logger.info("✅ GIFs de ejemplo creados/verificados")
        except ImportError:
            logger.warning("⚠️ PIL no disponible - Los GIFs no funcionarán")
        
        # Mostrar información del sistema
        logger.info(f"📋 Sistema: {config_manager.get('instituto.nombre')}")
        logger.info(f"🎯 Versión: {config_manager.get('system.version', '2.0.0')}")
        
        # Iniciar aplicación
        root = Tk()
        app = Login(root)
        
        # Configurar cierre seguro
        def on_closing():
            try:
                if hasattr(app, 'fondo_manager'):
                    app.fondo_manager.limpiar()
                root.destroy()
            except Exception as e:
                logger.error(f"Error en cierre: {e}")
            finally:
                logger.info("👋 Sistema cerrado")
                sys.exit(0)
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
        
    except Exception as e:
        logger.critical(f"❌ Error fatal iniciando sistema: {e}")
        messagebox.showerror("Error Crítico", 
                           f"No se pudo iniciar el sistema:\n{str(e)}\n\n"
                           "Contacte al administrador del sistema.")

if __name__ == "__main__":
    main()
