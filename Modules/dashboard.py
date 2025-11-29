"""
Dashboard - Panel de Control del Sistema
"""

import tkinter as tk
from tkinter import Toplevel, Frame, Label, ttk
import sqlite3
from datetime import datetime

from config.database import DB
from ui.theme_manager import FondoManager

class Dashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Dashboard - Estadísticas")
        self.root.geometry("1100x750")
        self.root.configure(bg="#f8fafc")

        # Aplicar fondo temático
        self.fondo_manager = FondoManager(root, "dashboard")
        self.fondo_manager.aplicar_fondo()

        self.crear_widgets()
        self.cargar_estadisticas()

    def crear_widgets(self):
        """Crea los widgets del dashboard"""
        # Frame principal
        main_frame = Frame(self.root, bg="#f8fafc")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título
        Label(main_frame, text="📊 Dashboard - Estadísticas del Sistema", 
              font=("Arial", 18, "bold"), bg="#f8fafc", fg="#2563eb").pack(pady=10)
        
        # Tarjetas de estadísticas
        self._crear_tarjetas_estadisticas(main_frame)
        
        # Botón actualizar
        Button(main_frame, text="🔄 Actualizar Estadísticas", 
               command=self.cargar_estadisticas, bg="#2563eb", fg="white").pack(pady=10)
        
        # Tabla de últimas asistencias
        self._crear_tabla_ultimas_asistencias(main_frame)

    def _crear_tarjetas_estadisticas(self, parent):
        """Crea las tarjetas de estadísticas"""
        cards_frame = Frame(parent, bg="#f8fafc")
        cards_frame.pack(fill=tk.X, pady=10)
        
        self.tarjetas = {}
        
        # Tarjeta 1: Total Estudiantes
        card1 = self._crear_tarjeta(cards_frame, "🎓 Total Estudiantes", "estudiantes", "#e3f2fd")
        card1.pack(side=tk.LEFT, padx=10, ipadx=20, ipady=15)
        
        # Tarjeta 2: Asistencias Hoy
        card2 = self._crear_tarjeta(cards_frame, "✅ Asistencias Hoy", "asistencias_hoy", "#e8f5e9")
        card2.pack(side=tk.LEFT, padx=10, ipadx=20, ipady=15)
        
        # Tarjeta 3: Faltas Hoy
        card3 = self._crear_tarjeta(cards_frame, "❌ Faltas Hoy", "faltas_hoy", "#ffebee")
        card3.pack(side=tk.LEFT, padx=10, ipadx=20, ipady=15)
        
        # Tarjeta 4: Total Docentes
        card4 = self._crear_tarjeta(cards_frame, "👨‍🏫 Total Docentes", "docentes", "#fff3e0")
        card4.pack(side=tk.LEFT, padx=10, ipadx=20, ipady=15)

    def _crear_tarjeta(self, parent, titulo, clave, color):
        """Crea una tarjeta individual"""
        card = Frame(parent, relief=tk.RAISED, borderwidth=2, bg=color)
        
        Label(card, text=titulo, bg=color, font=("Arial", 12, "bold")).pack()
        self.tarjetas[clave] = Label(card, text="0", bg=color, font=("Arial", 24, "bold"))
        self.tarjetas[clave].pack()
        
        return card

    def _crear_tabla_ultimas_asistencias(self, parent):
        """Crea la tabla de últimas asistencias"""
        Label(parent, text="Últimas Asistencias Registradas", 
              font=("Arial", 14, "bold"), bg="#f8fafc").pack(pady=10)
        
        cols = ("id", "estudiante", "fecha", "hora_entrada", "estado")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=12)
        
        for col in cols:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=150)
        
        self.tree.pack(fill=tk.BOTH, expand=True)

    def cargar_estadisticas(self):
        """Carga y actualiza las estadísticas"""
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        
        try:
            # Total estudiantes
            c.execute("SELECT COUNT(*) FROM estudiantes")
            total_estudiantes = c.fetchone()[0]
            
            # Asistencias hoy
            fecha_hoy = datetime.now().strftime("%Y-%m-%d")
            c.execute("SELECT COUNT(*) FROM asistencia WHERE fecha = ?", (fecha_hoy,))
            asistencias_hoy = c.fetchone()[0]
            
            # Faltas hoy (estimado)
            faltas_hoy = total_estudiantes - asistencias_hoy
            
            # Total docentes activos
            c.execute("SELECT COUNT(*) FROM docentes WHERE estado = 'ACTIVO'")
            total_docentes = c.fetchone()[0]
            
            # Actualizar tarjetas
            self.tarjetas['estudiantes'].config(text=str(total_estudiantes))
            self.tarjetas['asistencias_hoy'].config(text=str(asistencias_hoy))
            self.tarjetas['faltas_hoy'].config(text=str(faltas_hoy))
            self.tarjetas['docentes'].config(text=str(total_docentes))
            
            # Actualizar tabla de últimas asistencias
            self._actualizar_tabla_asistencias(c)
            
        except Exception as e:
            print(f"Error cargando estadísticas: {e}")
        finally:
            conn.close()

    def _actualizar_tabla_asistencias(self, cursor):
        """Actualiza la tabla de últimas asistencias"""
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        cursor.execute("""
            SELECT a.id_asistencia, e.nombres || ' ' || e.apellidos, a.fecha, a.hora_entrada, a.estado
            FROM asistencia a
            LEFT JOIN estudiantes e ON a.id_estudiante = e.id
            ORDER BY a.id_asistencia DESC LIMIT 20
        """)
        
        for row in cursor.fetchall():
            self.tree.insert("", "end", values=row)

# Botón import (añadir al inicio del archivo)
from tkinter import Button
