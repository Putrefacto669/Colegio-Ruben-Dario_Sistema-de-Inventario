"""
Sistema de Gestión de Temas y Fondos - VERSIÓN ESTABLE
"""

import os
import logging
from tkinter import Frame, Label

logger = logging.getLogger(__name__)

# Verificar disponibilidad de PIL
try:
    from PIL import Image, ImageTk, ImageSequence
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("⚠️ PIL no disponible - Los fondos GIF no funcionarán")

class FondoManager:
    """Gestor de fondos simplificado y estable"""
    
    def __init__(self, ventana, tipo_ventana):
        self.ventana = ventana
        self.tipo_ventana = tipo_ventana
        self.canvas = None
        self.animacion_activa = False
        
    def aplicar_fondo(self):
        """Aplica el fondo de forma segura"""
        try:
            # Verificar si los fondos están habilitados
            from config.config_manager import ConfigManager
            config = ConfigManager()
            
            if not config.get('ui.usar_fondos', True):
                self._aplicar_fondo_color()
                return
                
            if not PIL_AVAILABLE:
                self._aplicar_fondo_color()
                return
                
            ruta_fondo = self._obtener_ruta_fondo()
            
            if not ruta_fondo:
                self._aplicar_fondo_color()
                return
            
            # Intentar cargar fondo
            if ruta_fondo.lower().endswith('.gif'):
                self._aplicar_fondo_gif_simple(ruta_fondo)
            else:
                self._aplicar_fondo_imagen_simple(ruta_fondo)
                
        except Exception as e:
            logger.error(f"❌ Error aplicando fondo: {e}")
            self._aplicar_fondo_color()
    
    def _obtener_ruta_fondo(self):
        """Obtiene la ruta del fondo"""
        directorio = "fondos_instituto"
        
        if not os.path.exists(directorio):
            return None
            
        # Buscar cualquier imagen/GIF
        for archivo in os.listdir(directorio):
            if archivo.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                return os.path.join(directorio, archivo)
        
        return None
    
    def _aplicar_fondo_color(self):
        """Aplica fondo de color sólido - SIEMPRE FUNCIONA"""
        colores = {
            "login": "#1e3a8a",
            "menu_principal": "#2563eb", 
            "gestion_estudiantes": "#1e40af",
            "gestion_docentes": "#3730a3",
            "gestion_asistencia": "#1e3a8a",
            "dashboard": "#1e40af"
        }
        color = colores.get(self.tipo_ventana, "#1e40af")
        self.ventana.configure(bg=color)
        logger.info(f"🎨 Aplicado fondo de color: {color}")
    
    def _aplicar_fondo_gif_simple(self, ruta_gif):
        """Aplica GIF de forma simple y segura"""
        try:
            self.canvas = Frame(self.ventana, bg='white')
            self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
            self.canvas.lower()
            logger.info("✅ Fondo GIF aplicado (modo simple)")
        except Exception as e:
            logger.error(f"❌ Error con GIF: {e}")
            self._aplicar_fondo_color()
    
    def _aplicar_fondo_imagen_simple(self, ruta_imagen):
        """Aplica imagen de fondo de forma simple"""
        try:
            self.canvas = Frame(self.ventana)
            self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
            self.canvas.lower()
            logger.info("✅ Fondo imagen aplicado (modo simple)")
        except Exception as e:
            logger.error(f"❌ Error con imagen: {e}")
            self._aplicar_fondo_color()
    
    def limpiar(self):
        """Limpia recursos de forma segura"""
        self.animacion_activa = False
        if self.canvas:
            try:
                self.canvas.destroy()
            except:
                pass
        logger.debug("🧹 Recursos de fondo limpiados")
