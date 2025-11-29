"""
Módulo de Reportes de Asistencia
"""

import tkinter as tk
from tkinter import Toplevel, Frame, Label, Entry, Button, ttk
import sqlite3
from datetime import datetime

from config.database import DB
from ui.message_manager import MessageManager

class ReporteGeneral:
    """Reporte General de Asistencia"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Reporte General de Asistencia")
        self.root.geometry("900x520")
        
        self._crear_interfaz()
        self.cargar_datos()

    def _crear_interfaz(self):
        """Crea la interfaz del reporte"""
        Label(self.root, text="📊 Reporte General de Asistencia", 
              font=("Arial", 14, "bold")).pack(pady=12)
        
        # Crear tabla
        cols = ("id", "estudiante", "fecha", "hora_entrada", "hora_salida", "estado")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings")
        
        # Configurar columnas
        for col in cols:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=140)
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=8)
        
        # Botones de acción
        btn_frame = Frame(self.root)
        btn_frame.pack(pady=10)
        
        Button(btn_frame, text="🔄 Actualizar", bg="#2563eb", fg="white",
               command=self.cargar_datos).pack(side=tk.LEFT, padx=5)
        Button(btn_frame, text="📤 Exportar", bg="#16a34a", fg="white",
               command=self.exportar_reporte).pack(side=tk.LEFT, padx=5)

    def cargar_datos(self):
        """Carga los datos en la tabla"""
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        try:
            c.execute("""
                SELECT a.id_asistencia, 
                       e.nombres || ' ' || e.apellidos as estudiante, 
                       a.fecha, 
                       a.hora_entrada, 
                       IFNULL(a.hora_salida, '-') as hora_salida, 
                       a.estado
                FROM asistencia a
                LEFT JOIN estudiantes e ON a.id_estudiante = e.id
                ORDER BY a.id_asistencia DESC
            """)
            
            for row in c.fetchall():
                self.tree.insert("", "end", values=row)
                
        except Exception as e:
            MessageManager.show_error(self.root, "Error", f"Error al cargar datos: {str(e)}")
        finally:
            conn.close()

    def exportar_reporte(self):
        """Exporta el reporte a CSV"""
        try:
            from utils.exporters import ExportadorAvanzado
            
            # Obtener datos de la tabla
            datos = []
            for item in self.tree.get_children():
                datos.append(self.tree.item(item)['values'])
            
            # Exportar
            success, message = ExportadorAvanzado.exportar_csv(
                datos, 
                "reporte_general_asistencia",
                ["ID", "Estudiante", "Fecha", "Hora Entrada", "Hora Salida", "Estado"]
            )
            
            if success:
                MessageManager.show_info(self.root, "Éxito", message)
            else:
                MessageManager.show_error(self.root, "Error", message)
                
        except ImportError:
            MessageManager.show_error(self.root, "Error", "Módulo de exportación no disponible")

class ReportePorFecha:
    """Reporte de Asistencia por Fecha"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Reporte por Fecha")
        self.root.geometry("900x520")
        
        self._crear_interfaz()
        # Cargar datos con fecha actual por defecto
        self.buscar()

    def _crear_interfaz(self):
        """Crea la interfaz del reporte por fecha"""
        # Frame de controles
        frm = Frame(self.root)
        frm.pack(pady=8)
        
        Label(frm, text="📅 Fecha (YYYY-MM-DD):").grid(row=0, column=0, padx=6, pady=6)
        self.txt_fecha = Entry(frm)
        self.txt_fecha.grid(row=0, column=1, padx=6, pady=6)
        self.txt_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        Button(frm, text="🔍 Buscar", command=self.buscar, 
               bg="#2563eb", fg="white").grid(row=0, column=2, padx=6)
        
        Button(frm, text="📅 Hoy", command=self.fecha_hoy,
               bg="#16a34a", fg="white").grid(row=0, column=3, padx=6)

        # Crear tabla
        cols = ("id", "estudiante", "fecha", "entrada", "salida", "estado")
        self.tree = ttk.Treeview(self.root, columns=cols, show="headings")
        
        for col in cols:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=140)
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=8)
        
        # Botones adicionales
        btn_frame = Frame(self.root)
        btn_frame.pack(pady=10)
        
        Button(btn_frame, text="📤 Exportar", bg="#16a34a", fg="white",
               command=self.exportar_reporte).pack(side=tk.LEFT, padx=5)

    def buscar(self):
        """Busca asistencias por fecha"""
        fecha = self.txt_fecha.get().strip()
        
        if not fecha:
            MessageManager.show_warning(self.root, "Atención", "Ingrese una fecha")
            return
            
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        try:
            c.execute("""
                SELECT a.id_asistencia, 
                       e.nombres || ' ' || e.apellidos as estudiante, 
                       a.fecha, 
                       a.hora_entrada, 
                       IFNULL(a.hora_salida,'-') as hora_salida, 
                       a.estado
                FROM asistencia a
                LEFT JOIN estudiantes e ON a.id_estudiante = e.id
                WHERE a.fecha=?
                ORDER BY a.id_asistencia DESC
            """, (fecha,))
            
            for row in c.fetchall():
                self.tree.insert("", "end", values=row)
                
            # Mostrar conteo
            total = len(self.tree.get_children())
            self.root.title(f"Reporte por Fecha - {fecha} ({total} registros)")
            
        except Exception as e:
            MessageManager.show_error(self.root, "Error", f"Error al buscar: {str(e)}")
        finally:
            conn.close()

    def fecha_hoy(self):
        """Establece la fecha actual"""
        self.txt_fecha.delete(0, tk.END)
        self.txt_fecha.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.buscar()

    def exportar_reporte(self):
        """Exporta el reporte a CSV"""
        try:
            from utils.exporters import ExportadorAvanzado
            
            fecha = self.txt_fecha.get().strip()
            datos = []
            for item in self.tree.get_children():
                datos.append(self.tree.item(item)['values'])
            
            success, message = ExportadorAvanzado.exportar_csv(
                datos, 
                f"reporte_asistencia_{fecha}",
                ["ID", "Estudiante", "Fecha", "Hora Entrada", "Hora Salida", "Estado"]
            )
            
            if success:
                MessageManager.show_info(self.root, "Éxito", message)
            else:
                MessageManager.show_error(self.root, "Error", message)
                
        except ImportError:
            MessageManager.show_error(self.root, "Error", "Módulo de exportación no disponible")
