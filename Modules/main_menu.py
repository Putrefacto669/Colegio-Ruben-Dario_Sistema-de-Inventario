"""
Menú Principal del Sistema
"""

import tkinter as tk
from tkinter import Tk, Frame, Label, Button, LabelFrame
import sqlite3
import sys

from core.database_manager import DatabaseManager
from core.permissions import PermisosManager
from core.auditoria import Auditoria
from core.notifications import SistemaNotificaciones
from ui.theme_manager import FondoManager
from ui.window_manager import GestorVentanas

class MainMenu:
    def __init__(self, root, usuario, rol):
        self.root = root
        self.usuario = usuario
        self.rol = rol
        
        # Inicializar managers
        self.db_manager = DatabaseManager()
        self.auditoria = Auditoria(self.db_manager)
        self.notificaciones = SistemaNotificaciones(self.db_manager)
        
        # Registrar login en auditoría
        self.auditoria.registrar_evento(usuario, "LOGIN", f"Inicio de sesión exitoso - Rol: {rol}")
        
        # CONFIGURAR LA VENTANA PRIMERO
        root.title("Instituto Rubén Darío - Menú Principal")
        root.geometry("1000x600")
        root.resizable(True, True)
        
        # Centrar ventana
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (1000 // 2)
        y = (root.winfo_screenheight() // 2) - (600 // 2)
        root.geometry(f"1000x600+{x}+{y}")

        # Aplicar fondo temático DESPUÉS de configurar la ventana
        self.fondo_manager = FondoManager(root, "menu_principal")
        self.fondo_manager.aplicar_fondo()

        # Panel principal semi-transparente
        self.panel_principal = Frame(root, bg='white', bd=4, relief='ridge')
        self.panel_principal.place(relx=0.5, rely=0.5, anchor='center', width=900, height=500)

        # Encabezado con diseño institucional
        header = Frame(self.panel_principal, bg='white', pady=15)
        header.pack(fill='x', padx=20)
        
        Label(header, text="🏫 Instituto Rubén Darío", 
              font=("Arial", 20, "bold"), bg="white", fg="#1e3a8a").pack()
        
        Label(header, text="Sistema Integral de Gestión Académica", 
              font=("Arial", 12), bg="white", fg="#64748b").pack(pady=2)
        
        Label(header, text=f"Usuario: {self.usuario} | Rol: {self.rol}", 
              font=("Arial", 10, "bold"), bg="white", fg="#2563eb").pack(pady=5)

        # Contenedor para los botones de gestión y reportes
        wrap = Frame(self.panel_principal, bg="white")
        wrap.pack(fill='both', expand=True, padx=20, pady=20)

        # Frame para las gestiones
        gestion = LabelFrame(wrap, text="📊 Gestiones del Sistema", 
                           font=("Arial", 11, "bold"), bg="white", fg="#1f2937")
        gestion.grid(row=0, column=0, padx=12, pady=8, sticky='nsew')

        # Frame para los reportes
        reportes = LabelFrame(wrap, text="📈 Reportes y Estadísticas", 
                            font=("Arial", 11, "bold"), bg="white", fg="#1f2937")
        reportes.grid(row=0, column=1, padx=12, pady=8, sticky='nsew')

        # Configurar grid para expandirse
        wrap.columnconfigure(0, weight=1)
        wrap.columnconfigure(1, weight=1)
        wrap.rowconfigure(0, weight=1)

        # Opciones por permisos
        self._crear_botones_gestion(gestion)
        self._crear_botones_reportes(reportes)

        # Mostrar notificaciones al inicio
        self.root.after(1000, self.mostrar_notificaciones)

        # Botón salir
        Button(self.panel_principal, text="🚪 Salir del Sistema", width=18, 
               bg="#dc2626", fg="white", font=("Arial", 10, "bold"),
               command=self.salir_sistema).pack(pady=14)

    def _crear_botones_gestion(self, frame):
        """Crea los botones de gestión según los permisos"""
        if PermisosManager.tiene_permiso(self.rol, 'gestion_docentes'):
            Button(frame, text="👨‍🏫 Gestión de Docentes", width=28,
                   bg="#2563eb", fg="white", command=self.abrir_docentes).pack(padx=12, pady=6)
        
        if PermisosManager.tiene_permiso(self.rol, 'gestion_estudiantes'):
            Button(frame, text="🎓 Gestión de Estudiantes", width=28,
                   bg="#0ea5e9", fg="white", command=self.abrir_estudiantes).pack(padx=12, pady=6)
        
        if PermisosManager.tiene_permiso(self.rol, 'control_asistencia'):
            Button(frame, text="📋 Control de Asistencia", width=28,
                   bg="#22c55e", fg="white", command=self.abrir_asistencia).pack(padx=12, pady=6)
        
        if PermisosManager.tiene_permiso(self.rol, 'gestion_usuarios'):
            Button(frame, text="👥 Usuarios y Roles", width=28,
                   bg="#64748b", fg="white", command=self.abrir_usuarios).pack(padx=12, pady=6)
        
        if PermisosManager.tiene_permiso(self.rol, 'ver_reportes'):
            Button(frame, text="📊 Dashboard Estadísticas", width=28,
                   bg="#8b5cf6", fg="white", command=self.abrir_dashboard).pack(padx=12, pady=6)
        
        if PermisosManager.tiene_permiso(self.rol, 'backup_restore'):
            Button(frame, text="💾 Backup del Sistema", width=28,
                   bg="#f59e0b", fg="white", command=self.abrir_backup).pack(padx=12, pady=6)

    def _crear_botones_reportes(self, frame):
        """Crea los botones de reportes según los permisos"""
        if PermisosManager.tiene_permiso(self.rol, 'ver_reportes'):
            Button(frame, text="📄 Reporte General", width=30,
                   bg="#16a34a", fg="white", command=self.reporte_general).pack(padx=12, pady=6)
            Button(frame, text="📅 Reporte por Fecha", width=30,
                   bg="#f59e0b", fg="white", command=self.reporte_por_fecha).pack(padx=12, pady=6)
            Button(frame, text="🔍 Búsqueda Avanzada", width=30,
                   bg="#8b5cf6", fg="white", command=self.busqueda_avanzada).pack(padx=12, pady=6)

    def abrir_docentes(self):
        from modules.docentes.gestion_docentes import GestionDocentes
        GestorVentanas.abrir_ventana(self.root, GestionDocentes, "Gestión de Docentes")

    def abrir_estudiantes(self):
        from modules.estudiantes.gestion_estudiantes import GestionEstudiantes
        GestorVentanas.abrir_ventana(self.root, GestionEstudiantes, "Gestión de Estudiantes Técnicos")

    def abrir_asistencia(self):
        from modules.asistencia.control_asistencia import GestionAsistencia
        GestorVentanas.abrir_ventana(self.root, GestionAsistencia, "Control de Asistencia - Estudiantes")

    def abrir_usuarios(self):
        from modules.usuarios.gestion_usuarios import GestionUsuarios
        GestorVentanas.abrir_ventana(self.root, GestionUsuarios, "Usuarios y Roles")

    def abrir_dashboard(self):
        from modules.dashboard import Dashboard
        GestorVentanas.abrir_ventana(self.root, Dashboard, "Dashboard - Estadísticas")

    def abrir_backup(self):
        from core.backup_manager import GestionBackup
        GestorVentanas.abrir_ventana(self.root, GestionBackup, "Gestión de Backup")

    def reporte_general(self):
        from modules.asistencia.reportes_asistencia import ReporteGeneral
        GestorVentanas.abrir_ventana(self.root, ReporteGeneral, "Reporte General de Asistencia")

    def reporte_por_fecha(self):
        from modules.asistencia.reportes_asistencia import ReportePorFecha
        GestorVentanas.abrir_ventana(self.root, ReportePorFecha, "Reporte de Asistencia por Fecha")

    def busqueda_avanzada(self):
        from utils.exporters import BuscadorAvanzado
        buscador = BuscadorAvanzado(self.db_manager)
        
        # Crear ventana de búsqueda
        ventana_busqueda = tk.Toplevel(self.root)
        ventana_busqueda.title("Búsqueda Avanzada - Estudiantes")
        ventana_busqueda.geometry("500x400")
        
        # Implementar interfaz de búsqueda...
        Label(ventana_busqueda, text="🔍 Búsqueda Avanzada", 
              font=("Arial", 14, "bold")).pack(pady=10)
        
        self.auditoria.registrar_evento(self.usuario, "BUSQUEDA_AVANZADA", "Acceso a búsqueda avanzada")

    def mostrar_notificaciones(self):
        """Verifica y muestra notificaciones pendientes al iniciar sesión"""
        self.notificaciones.verificar_notificaciones_pendientes()
        if self.notificaciones.notificaciones:
            self.notificaciones.mostrar_notificaciones(self.root)

    def salir_sistema(self):
        """Cierra el sistema de manera segura"""
        self.auditoria.registrar_evento(self.usuario, "LOGOUT", "Cierre de sesión")
        self.root.destroy()
