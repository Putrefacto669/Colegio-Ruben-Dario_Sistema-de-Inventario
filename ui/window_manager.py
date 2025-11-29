"""
Gestor de ventanas del sistema
"""

import tkinter as tk
from tkinter import Toplevel
from typing import Dict, Any

class GestorVentanas:
    """Gestor centralizado de ventanas"""
    
    _ventanas_abiertas: Dict[str, Toplevel] = {}
    _ventana_activa: Toplevel = None
    
    @classmethod
    def abrir_ventana(cls, root, clase_ventana, titulo: str, *args, **kwargs) -> Toplevel:
        """Abre una ventana si no está ya abierta"""
        if titulo in cls._ventanas_abiertas:
            # Traer ventana existente al frente
            ventana_existente = cls._ventanas_abiertas[titulo]
            try:
                ventana_existente.lift()
                ventana_existente.focus_force()
                cls._ventana_activa = ventana_existente
                return ventana_existente
            except:
                cls._ventanas_abiertas.pop(titulo, None)
        
        # Crear nueva ventana
        nueva_ventana = Toplevel(root)
        nueva_ventana.title(titulo)
        nueva_ventana.geometry("900x600")
        nueva_ventana.transient(root)  # Hacerla dependiente de la principal
        nueva_ventana.grab_set()  # Modal
        
        # Configurar cierre
        nueva_ventana.protocol("WM_DELETE_WINDOW", 
                             lambda: cls.cerrar_ventana(titulo))
        
        # Centrar ventana
        cls._centrar_ventana(nueva_ventana, root)
        
        # Registrar ventana
        cls._ventanas_abiertas[titulo] = nueva_ventana
        cls._ventana_activa = nueva_ventana
        
        # Crear contenido
        try:
            clase_ventana(nueva_ventana, *args, **kwargs)
        except Exception as e:
            print(f"Error al crear ventana {titulo}: {e}")
            nueva_ventana.destroy()
            cls._ventanas_abiertas.pop(titulo, None)
        
        return nueva_ventana

    @classmethod
    def cerrar_ventana(cls, titulo: str):
        """Cierra una ventana específica"""
        if titulo in cls._ventanas_abiertas:
            try:
                cls._ventanas_abiertas[titulo].destroy()
            except:
                pass
            finally:
                cls._ventanas_abiertas.pop(titulo, None)

    @classmethod
    def cerrar_todas(cls):
        """Cierra todas las ventanas abiertas"""
        for titulo in list(cls._ventanas_abiertas.keys()):
            cls.cerrar_ventana(titulo)

    @classmethod
    def get_ventana_activa(cls) -> Toplevel:
        """Obtiene la ventana activa actual"""
        return cls._ventana_activa

    @classmethod
    def _centrar_ventana(cls, ventana: Toplevel, padre=None):
        """Centra una ventana en la pantalla"""
        ventana.update_idletasks()
        
        if padre:
            # Centrar respecto a la ventana padre
            x = padre.winfo_x() + (padre.winfo_width() // 2) - (ventana.winfo_width() // 2)
            y = padre.winfo_y() + (padre.winfo_height() // 2) - (ventana.winfo_height() // 2)
        else:
            # Centrar en la pantalla
            screen_width = ventana.winfo_screenwidth()
            screen_height = ventana.winfo_screenheight()
            x = (screen_width - ventana.winfo_width()) // 2
            y = (screen_height - ventana.winfo_height()) // 2
        
        ventana.geometry(f"+{x}+{y}")

    @classmethod
    def ventana_abierta(cls, titulo: str) -> bool:
        """Verifica si una ventana está abierta"""
        return titulo in cls._ventanas_abiertas

    @classmethod
    def listar_ventanas_abiertas(cls) -> list:
        """Lista todas las ventanas abiertas"""
        return list(cls._ventanas_abiertas.keys())
