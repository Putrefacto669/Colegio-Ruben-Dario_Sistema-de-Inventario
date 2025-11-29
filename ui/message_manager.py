"""
Gestor mejorado de mensajes
"""

import tkinter.messagebox as messagebox
from tkinter import Tk

class MessageManager:
    """Gestor mejorado de mensajes que mantiene el foco en las ventanas correctas"""
    
    @staticmethod
    def show_info(parent, title: str, message: str):
        """Muestra mensaje informativo manteniendo el foco"""
        parent.update_idletasks()  # Forzar actualización de la UI
        result = messagebox.showinfo(title, message, parent=parent)
        parent.focus_force()  # Recuperar el foco
        parent.lift()  # Traer al frente
        return result
    
    @staticmethod
    def show_warning(parent, title: str, message: str):
        """Muestra advertencia manteniendo el foco"""
        parent.update_idletasks()
        result = messagebox.showwarning(title, message, parent=parent)
        parent.focus_force()
        parent.lift()
        return result
    
    @staticmethod
    def show_error(parent, title: str, message: str):
        """Muestra error manteniendo el foco"""
        parent.update_idletasks()
        result = messagebox.showerror(title, message, parent=parent)
        parent.focus_force()
        parent.lift()
        return result
    
    @staticmethod
    def ask_yesno(parent, title: str, message: str) -> bool:
        """Pregunta sí/no manteniendo el foco"""
        parent.update_idletasks()
        result = messagebox.askyesno(title, message, parent=parent)
        parent.focus_force()
        parent.lift()
        return result
    
    @staticmethod
    def ask_okcancel(parent, title: str, message: str) -> bool:
        """Pregunta ok/cancelar manteniendo el foco"""
        parent.update_idletasks()
        result = messagebox.askokcancel(title, message, parent=parent)
        parent.focus_force()
        parent.lift()
        return result
    
    @staticmethod
    def ask_retrycancel(parent, title: str, message: str) -> bool:
        """Pregunta reintentar/cancelar manteniendo el foco"""
        parent.update_idletasks()
        result = messagebox.askretrycancel(title, message, parent=parent)
        parent.focus_force()
        parent.lift()
        return result
