"""
Sistema de Notificaciones del Sistema
"""

import tkinter as tk
from tkinter import Toplevel, Frame, Label, Button
from datetime import datetime

class SistemaNotificaciones:
    """Sistema de notificaciones mejorado"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.notificaciones = []
    
    def verificar_notificaciones_pendientes(self):
        """Verifica y genera notificaciones automáticas"""
        self.notificaciones.clear()
        
        # Verificar estudiantes sin asistencia hoy
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        query = """
            SELECT COUNT(*) as faltantes 
            FROM estudiantes e
            LEFT JOIN asistencia a ON e.id = a.id_estudiante AND a.fecha = ?
            WHERE a.id_asistencia IS NULL
        """
        result = self.db_manager.execute_query(query, (fecha_hoy,), fetch=True)
        
        if result and result[0]['faltantes'] > 0:
            self.notificaciones.append({
                'tipo': 'advertencia',
                'titulo': 'Estudiantes sin asistencia',
                'mensaje': f'{result[0]["faltantes"]} estudiantes no tienen asistencia registrada hoy',
                'fecha': datetime.now()
            })
        
        # Verificar backup automático
        if not os.path.exists("backups"):
            self.notificaciones.append({
                'tipo': 'info',
                'titulo': 'Carpeta de backups',
                'mensaje': 'La carpeta de backups no existe',
                'fecha': datetime.now()
            })
        
        # Verificar base de datos
        try:
            stats = self.db_manager.get_estadisticas()
            if stats['total_estudiantes'] == 0:
                self.notificaciones.append({
                    'tipo': 'info',
                    'titulo': 'Base de datos',
                    'mensaje': 'No hay estudiantes registrados en el sistema',
                    'fecha': datetime.now()
                })
        except:
            pass
    
    def mostrar_notificaciones(self, parent):
        """Muestra las notificaciones pendientes"""
        if not self.notificaciones:
            return
        
        ventana_notificaciones = Toplevel(parent)
        ventana_notificaciones.title("Notificaciones del Sistema")
        ventana_notificaciones.geometry("500x400")
        ventana_notificaciones.configure(bg='white')
        
        Label(ventana_notificaciones, text="🔔 Notificaciones", 
              font=("Arial", 14, "bold"), bg="white").pack(pady=10)
        
        frame_lista = Frame(ventana_notificaciones, bg="white")
        frame_lista.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        for notif in self.notificaciones:
            self._crear_notificacion(frame_lista, notif)
        
        Button(ventana_notificaciones, text="Cerrar", 
               command=ventana_notificaciones.destroy).pack(pady=10)
    
    def _crear_notificacion(self, parent, notificacion):
        """Crea una notificación individual"""
        color_fondo = {
            'advertencia': '#fff3cd',
            'peligro': '#f8d7da', 
            'info': '#d1ecf1',
            'exito': '#d4edda'
        }.get(notificacion['tipo'], '#ffffff')
        
        frame_notif = Frame(parent, bg=color_fondo, relief='raised', bd=1)
        frame_notif.pack(fill=tk.X, pady=5)
        
        Label(frame_notif, text=notificacion['titulo'], font=("Arial", 10, "bold"),
              bg=color_fondo).pack(anchor='w', padx=10, pady=(10, 0))
        Label(frame_notif, text=notificacion['mensaje'], font=("Arial", 9),
              bg=color_fondo, wraplength=400).pack(anchor='w', padx=10, pady=(0, 10))
    
    def agregar_notificacion(self, tipo: str, titulo: str, mensaje: str):
        """Agrega una notificación manualmente"""
        self.notificaciones.append({
            'tipo': tipo,
            'titulo': titulo,
            'mensaje': mensaje,
            'fecha': datetime.now()
        })
    
    def limpiar_notificaciones(self):
        """Limpia todas las notificaciones"""
        self.notificaciones.clear()

# Import necesario
import os
